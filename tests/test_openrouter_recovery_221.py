"""Offline regression suite for Santa Swarm OpenRouter recovery (no keys/network)."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'swarm'))
import agent_v2 as a


def failure(status, message):
    payload = {'error': {'code': status, 'message': message}}
    return HTTPError('https://openrouter.ai/api/v1/chat/completions', status,
                     'bad request', {}, io.BytesIO(json.dumps(payload).encode()))


class Response:
    def __init__(self, body): self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, *args): return json.dumps(self.body).encode()


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        a.API_CALLS.clear()
        a._MODEL_LIMITS.clear()
        a._CATALOG = ('sample/alpha:free', 'sample/beta:free')

    def test_400_retries_next_free_model_with_minimal_payload(self):
        answered = Response({'model': 'sample/beta:free',
                             'choices': [{'finish_reason':'stop', 'message': {'content': '{"hypothesis":"test"}'}}]})
        with patch.object(a.urllib.request, 'urlopen', side_effect=[failure(400, 'temperature parameter unsupported'), answered]) as requests:
            actual = a.completion('private-secret', 'Mathematician agent', 'Try algebra', 1800)
        self.assertIn('hypothesis', actual)
        self.assertEqual(requests.call_count, 2)
        bodies = [json.loads(c.args[0].data) for c in requests.call_args_list]
        for body in bodies:
            self.assertTrue(body['model'].endswith(':free'))
            self.assertEqual([m['role'] for m in body['messages']], ['user'])
            self.assertNotIn('reasoning', body)
            self.assertNotIn('temperature', body)
            self.assertNotIn('response_format', body)
            self.assertNotIn('private-secret', json.dumps(body))
        self.assertNotEqual(bodies[0]['model'], bodies[1]['model'])
        self.assertIn('parameter_unsupported', json.dumps(a.API_CALLS))
        self.assertNotIn('private-secret', json.dumps(a.API_CALLS))

    def test_400_token_limit_is_categorized_safely(self):
        self.assertEqual(a.classify_bad_request(failure(400, 'Maximum context length exceeded: 20000 tokens')),
                         'context_or_token_limit')

    def test_401_key_failure_never_retries(self):
        with patch.object(a.urllib.request, 'urlopen', side_effect=[failure(401, 'unauthorized')]) as requests:
            with self.assertRaisesRegex(a.OpenRouterResponseError, 'http_401'):
                a.completion('secret', 'Mathematician agent', 'hello', 2000)
        self.assertEqual(requests.call_count, 1)

    def test_output_budget_respects_live_model_capacity(self):
        a._MODEL_LIMITS['sample/alpha:free'] = 1600
        with patch.object(a.urllib.request, 'urlopen', return_value=Response({'model': 'sample/alpha:free',
            'choices': [{'message': {'content': '{}'}}]})) as req:
            a._one_completion('key', 'Mathematician agent', 'problem', 3000, 'sample/alpha:free')
        body = json.loads(req.call_args.args[0].data)
        self.assertEqual(body['max_tokens'], 1536)

    def test_programmer_retries_when_candidate_is_malformed(self):
        bad = 'some text, not source code'
        good = '{"idea":"test","code":"def optimize(puzzle, program, rng):\\n    return None\\n"}'
        with patch.object(a, '_one_completion', side_effect=[bad,good]) as mock_calls:
            raw = a.completion('key', 'Python optimization engineer', 'code',
                               validator=a.extract_candidate_code)
        self.assertIn('def optimize', raw)
        self.assertEqual(mock_calls.call_count, 2)
        self.assertTrue(any(x.get('candidate_validation') == 'ValueError' for x in a.API_CALLS))

    def test_invalid_source_cannot_be_accepted(self):
        with self.assertRaises(ValueError):
            a.extract_candidate_code('def optimize(puzzle, program, rng):\n    import subprocess\n    return None')

    def test_embedded_400_can_switch_model(self):
        with self.assertRaises(a.OpenRouterResponseError) as ctx:
            a.parse_chat_response({'error': {'code': 400, 'message': 'bad request'}}, 'Math')
        self.assertTrue(ctx.exception.allow_fallback)

    def test_full_agent_cycle_saves_code_without_network(self):
        import os
        from unittest.mock import patch
        candidate = '{"idea":"bounded pattern search","code":"def optimize(puzzle, program, rng):\\n    return None\\n"}'
        # Three fake completed text generations: math, programmer, critic.
        replies = ['{"hypothesis":"factor sharing","algorithm":"try a short rewrite"}',
                   candidate, '{"risks":[],"fix_suggestion":"none"}']
        with tempfile.TemporaryDirectory() as tmp:
            prev = Path.cwd()
            try:
                os.chdir(tmp)
                with patch.dict(os.environ, {'OPENROUTER_API_KEY':'FAKE-LOCAL-KEY', 'GITHUB_RUN_NUMBER':'15'}), \
                     patch.object(a, 'gather', return_value=[]), \
                     patch.object(a, 'completion', side_effect=replies) as calls:
                    a.main()
                status = json.loads(Path('logs/proposal.json').read_text())
                self.assertEqual(status['status'], 'candidate_saved')
                self.assertEqual(status['stages'], ['mathematician','programmer','critic'])
                self.assertEqual(calls.call_count, 3)
                self.assertIn('def optimize', Path('candidate.py').read_text())
                self.assertNotIn('FAKE-LOCAL-KEY', Path('logs/proposal.json').read_text())
                self.assertTrue(Path('state/agent_history.json').is_file())
            finally:
                os.chdir(prev)

    def test_real_puzzle_example_is_loaded_if_available(self):
        from core import save_submission, Puzzle
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir(); (root / 'state').mkdir()
            (root/'data'/'puzzles.csv').write_text('id,starting_values,targets,value_limit,registers\np1,"[2,3]","[5]",99,48\n')
            save_submission(root/'state'/'base.csv', {'p1':[['+',0,1,2]]},
                            {'p1':Puzzle('p1',(2,3),(5,),99,48)})
            import os
            prev = Path.cwd()
            try:
                os.chdir(root)
                examples = a.champion_examples()
            finally:
                os.chdir(prev)
        self.assertEqual(examples[0]['id'], 'p1')
        self.assertEqual(examples[0]['program'], [['+',0,1,2]])

if __name__ == '__main__':
    unittest.main()
