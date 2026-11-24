"""Regression checks against the live catalog schema that may omit optional fields."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'swarm'))
import agent_v2 as a


def free_model(id='example/chat:free', **kw):
    result = {'id': id,
              'pricing': {'prompt': '0', 'completion': '0'},
              'architecture': {'input_modalities': ['text'], 'output_modalities': ['text']},
              'top_provider': {'max_completion_tokens': 4096}}
    result.update(kw)
    return result


class CatalogCompatibilityTests(unittest.TestCase):
    def setUp(self):
        a._CATALOG = None
        a.API_CALLS.clear()

    def test_optional_request_fee_absent_is_allowed(self):
        self.assertEqual(a.filter_free_text_models(
            {'data': [free_model(endpoints=['/api/v1/chat/completions'])]}),
            ['example/chat:free'])

    def test_missing_endpoints_only_allowed_with_server_filter(self):
        payload = {'data': [free_model()]}
        self.assertEqual(a.filter_free_text_models(payload), [])
        self.assertEqual(a.filter_free_text_models(payload, server_filtered_chat=True),
                         ['example/chat:free'])

    def test_explicit_nonzero_fee_rejected(self):
        for pricing in (
            {'prompt': '0.1', 'completion': '0'},
            {'prompt': '0', 'completion': '0.01'},
            {'prompt': '0', 'completion': '0', 'request': '0.001'},
        ):
            with self.subTest(pricing=pricing):
                self.assertEqual(a.filter_free_text_models(
                    {'data': [free_model(pricing=pricing)]},
                    server_filtered_chat=True), [])

    def test_explicit_non_chat_endpoint_still_rejected(self):
        payload = {'data': [free_model(endpoints=['/api/v1/embeddings'])]}
        self.assertEqual(a.filter_free_text_models(payload, server_filtered_chat=True), [])

    def test_empty_catalog_filters_to_verified_free_router(self):
        class R:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, *args): return json.dumps({'data': [free_model(id='example/paid', pricing={'prompt':'0.1','completion':'0.2'})]}).encode()
        with patch.object(a.urllib.request, 'urlopen', return_value=R()) as mock_get:
            result = a.discover_free_text_models('secret-test-key')
        self.assertEqual(result, ['openrouter/free'])
        self.assertIn('endpoints=', mock_get.call_args.args[0].full_url)
        self.assertTrue(any(x.get('model_catalog_warning') == 'no_free_variant_eligible' for x in a.API_CALLS))
        self.assertNotIn('secret-test-key', json.dumps(a.API_CALLS))

    def test_actual_catalog_response_logs_candidates_without_key(self):
        payload = {'data': [free_model(endpoints=['/api/v1/chat/completions'])]}
        class R:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, *args): return json.dumps(payload).encode()
        with patch.object(a.urllib.request, 'urlopen', return_value=R()):
            self.assertEqual(a.discover_free_text_models('test-secret-key'), ['example/chat:free'])
        self.assertEqual(a.API_CALLS[-1]['model_catalog_eligible_free_chat_models'], 1)
        self.assertNotIn('test-secret-key', json.dumps(a.API_CALLS))


if __name__ == '__main__':
    unittest.main()
