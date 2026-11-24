"""Regression tests for free-model 429 handling with live-catalog routing.

The live catalog is stubbed as already fetched: these tests exercise the
/chat/completions request, not the separate GET /models request.
"""
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
from urllib.error import HTTPError

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'swarm'))
spec = importlib.util.spec_from_file_location('patched_agent_v213', PROJECT / 'swarm' / 'agent_v2.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def http_429(source=None, message='rate limit'):
    obj = {'error': {'message': message}}
    if source:
        obj['error']['metadata'] = {'limit_source': source}
    return HTTPError('https://openrouter.ai/api/v1/chat/completions', 429,
                     'Rate limited', {}, io.BytesIO(json.dumps(obj).encode()))


class Response:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, *args):
        return json.dumps(self.payload).encode()


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        mod.API_CALLS.clear()
        self._old_catalog = mod._CATALOG
        mod._CATALOG = ('test/alpha:free', 'test/beta:free')
        self._old_override = mod.MODEL_OVERRIDE
        self._old_fallback = mod.FALLBACK_MODEL
        mod.MODEL_OVERRIDE = ''
        mod.FALLBACK_MODEL = ''

    def tearDown(self):
        mod._CATALOG = self._old_catalog
        mod.MODEL_OVERRIDE = self._old_override
        mod.FALLBACK_MODEL = self._old_fallback

    def test_daily_not_retried(self):
        with mock.patch.object(mod.urllib.request, 'urlopen', side_effect=[http_429('openrouter_free_tier_daily')]) as calls:
            with self.assertRaisesRegex(mod.OpenRouterResponseError, 'free_daily_limit'):
                mod.completion('fake-key', 'Mathematician agent', 'test', 100)
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(mod.API_CALLS[-1]['limit_source'], 'free_daily_limit')

    def test_minute_not_retried(self):
        with mock.patch.object(mod.urllib.request, 'urlopen', side_effect=[http_429('openrouter_free_tier_per_minute')]) as calls:
            with self.assertRaisesRegex(mod.OpenRouterResponseError, 'free_minute_limit'):
                mod.completion('fake-key', 'Mathematician agent', 'test', 100)
        self.assertEqual(calls.call_count, 1)

    def test_unknown_429_not_retried(self):
        with mock.patch.object(mod.urllib.request, 'urlopen', side_effect=[http_429()]) as calls:
            with self.assertRaisesRegex(mod.OpenRouterResponseError, 'http_429:unknown'):
                mod.completion('fake-key', 'Mathematician agent', 'test', 100)
        self.assertEqual(calls.call_count, 1)

    def test_upstream_429_triggers_one_free_fallback(self):
        fake_response = {'model': 'test/beta:free',
                         'choices': [{'finish_reason':'stop', 'message': {'content': '{"ok":true}'}}]}
        with mock.patch.object(mod.urllib.request, 'urlopen', side_effect=[http_429('upstream_provider_shared_pool'), Response(fake_response)]) as calls:
            result = mod.completion('fake-key', 'Mathematician agent', 'test', 100)
        self.assertEqual(result, '{"ok":true}')
        self.assertEqual(calls.call_count, 2)
        models = [json.loads(c.args[0].data)['model'] for c in calls.call_args_list]
        self.assertNotEqual(models[0], models[1])
        self.assertTrue(all(x.endswith(':free') for x in models))

    def test_upstream_phrase_recognized_when_metadata_missing(self):
        source, retry = mod.classify_http_error(http_429(message='model temporarily rate-limited upstream'))
        self.assertEqual(source, 'upstream_provider_shared_pool')
        self.assertTrue(retry)

    def test_keys_never_logged(self):
        with mock.patch.object(mod.urllib.request, 'urlopen', side_effect=[http_429('openrouter_free_tier_daily')]):
            with self.assertRaises(mod.OpenRouterResponseError):
                mod.completion('SECRET-TEST-KEY', 'Mathematician agent', 'test', 100)
        self.assertNotIn('SECRET-TEST-KEY', json.dumps(mod.API_CALLS))

if __name__ == '__main__':
    unittest.main()
