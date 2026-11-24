import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'swarm'))
import agent_v2 as a


def model(mid, *, paid=False, endpoint=True, output='text', req='0'):
    return {'id': mid,
            'pricing': {'prompt': '0.002' if paid else '0', 'completion': '0', 'request': req},
            'architecture': {'input_modalities': ['text'], 'output_modalities': [output]},
            'endpoints': ['/api/v1/chat/completions'] if endpoint else ['/api/v1/embeddings'],
            'top_provider': {'max_completion_tokens': 8192}}


class LiveRoutingTests(unittest.TestCase):
    def setUp(self):
        a._CATALOG = None
        a.API_CALLS.clear()

    def test_filters_out_paid_wrong_endpoint_and_nontext(self):
        obj = {'data': [model('x/good:free'), model('x/paid:free', paid=True),
                        model('x/embed:free', endpoint=False), model('x/pic:free', output='image'),
                        model('x/request:free', req='1'), model('x/regular'),
                        model('x/backup:free')]}
        self.assertEqual(a.filter_free_text_models(obj), ['x/backup:free', 'x/good:free'])

    def test_unknown_catalog_fail_closed(self):
        self.assertRaises(a.OpenRouterResponseError, a.filter_free_text_models, {})

    def test_fallback_for_404(self):
        a._CATALOG = ('x/alpha:free', 'x/beta:free')
        calls = []
        def fake(key, role, prompt, tokens, model):
            calls.append(model)
            if len(calls) == 1:
                raise a.OpenRouterResponseError('http_404 for role=Mathematician agent')
            return 'hello'
        with patch.object(a, '_one_completion', fake), patch.object(a, 'MODEL_OVERRIDE', ''), patch.object(a, 'FALLBACK_MODEL', ''):
            self.assertEqual(a.completion('key', 'Mathematician agent', 'prompt'), 'hello')
        self.assertEqual(len(set(calls)), 2)

    def test_429_account_does_not_retry(self):
        a._CATALOG = ('x/alpha:free', 'x/beta:free')
        calls = []
        def fake(key, role, prompt, tokens, model):
            calls.append(model)
            raise a.OpenRouterResponseError('http_429:free_daily_limit for role=Mathematician agent', allow_fallback=False)
        with patch.object(a, '_one_completion', fake), patch.object(a, 'MODEL_OVERRIDE', ''), patch.object(a, 'FALLBACK_MODEL', ''):
            with self.assertRaises(a.OpenRouterResponseError):
                a.completion('key', 'Mathematician agent', 'prompt')
        self.assertEqual(len(calls), 1)

    def test_429_upstream_retries_other(self):
        a._CATALOG = ('x/alpha:free', 'x/beta:free')
        calls = []
        def fake(key, role, prompt, tokens, model):
            calls.append(model)
            if len(calls) == 1:
                raise a.OpenRouterResponseError('http_429:upstream_provider_shared_pool for role=Mathematician agent', allow_fallback=True)
            return '{"hypothesis":"valid"}'
        with patch.object(a, '_one_completion', fake), patch.object(a, 'MODEL_OVERRIDE', ''), patch.object(a, 'FALLBACK_MODEL', ''):
            self.assertIn('valid', a.completion('key', 'Mathematician agent', 'prompt'))
        self.assertEqual(len(calls), 2)

    def test_model_override_not_in_free_catalog_is_ignored(self):
        a._CATALOG = ('x/alpha:free', 'x/beta:free')
        with patch.object(a, 'MODEL_OVERRIDE', 'paid/foo'), patch.object(a, 'FALLBACK_MODEL', ''):
            choices = a._candidate_models('key', 'Python optimization engineer')
        self.assertEqual(len(choices), 2)
        self.assertEqual(a.API_CALLS[-1]['configuration_warning'], 'override_not_in_live_free_catalog')

    def test_no_paid_model_possible(self):
        self.assertEqual(a.filter_free_text_models({'data': [model('x/paid:free', paid=True)]}), [])

if __name__ == '__main__':
    unittest.main()

class EmbeddedErrorTests(unittest.TestCase):
    def test_http_200_with_embedded_account_rate_limit_stops(self):
        with self.assertRaises(a.OpenRouterResponseError) as context:
            a.parse_chat_response({'error': {'code': 429,
                 'metadata': {'limit_source': 'openrouter_free_tier_daily'}}}, 'Mathematician agent')
        self.assertFalse(context.exception.allow_fallback)
    def test_http_200_with_embedded_upstream_429_allows_fallback(self):
        with self.assertRaises(a.OpenRouterResponseError) as context:
            a.parse_chat_response({'error': {'code': 429,
                 'metadata': {'limit_source': 'upstream_provider_shared_pool'}}}, 'Mathematician agent')
        self.assertTrue(context.exception.allow_fallback)

class CatalogFetchTests(unittest.TestCase):
    def test_live_catalog_get_and_cache(self):
        a._CATALOG = None
        a.API_CALLS.clear()
        obj = {'data': [model('x/good:free'), model('x/bad:free', paid=True)]}
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self, *args): return json.dumps(obj).encode()
        with patch.object(a.urllib.request, 'urlopen', return_value=Response()) as get:
            self.assertEqual(a.discover_free_text_models('test-secret'), ['x/good:free'])
            self.assertEqual(a.discover_free_text_models('test-secret'), ['x/good:free'])
            self.assertEqual(get.call_count, 1)
        self.assertEqual(a.API_CALLS[-1], {'model_catalog_eligible_free_chat_models': 1})
        self.assertNotIn('test-secret', str(a.API_CALLS))
