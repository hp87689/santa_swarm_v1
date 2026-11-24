"""Offline contract tests: no API key or network requests required."""
import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'swarm'))
from agent_v2 import parse_chat_response, object_from_response, OpenRouterResponseError, API_CALLS


class Tests(unittest.TestCase):
    def setUp(self):
        API_CALLS.clear()

    def test_content(self):
        data = {'model': 'demo/free', 'choices': [{'finish_reason': 'stop', 'message': {'content': '{"a":1}'}}]}
        self.assertEqual(parse_chat_response(data, 'mathematician'), '{"a":1}')
        self.assertEqual(API_CALLS[-1]['model'], 'demo/free')

    def test_null_content(self):
        data = {'model': 'reasoning/free', 'usage': {'completion_tokens': 1300, 'completion_tokens_details': {'reasoning_tokens': 1300}},
                'choices': [{'finish_reason': 'length', 'message': {'content': None}}]}
        with self.assertRaisesRegex(OpenRouterResponseError, 'empty_content'):
            parse_chat_response(data, 'mathematician')
        self.assertEqual(API_CALLS[-1]['reasoning_tokens'], 1300)

    def test_missing_choices(self):
        with self.assertRaisesRegex(OpenRouterResponseError, 'missing_choices'):
            parse_chat_response({'choices': None}, 'mathematician')

    def test_missing_message(self):
        with self.assertRaisesRegex(OpenRouterResponseError, 'empty_content'):
            parse_chat_response({'choices':[{'finish_reason':'stop', 'message': None}]}, 'critic')

    def test_part_list_content(self):
        data={'choices':[{'message':{'content':[{'type':'text','text':'{\"ok\":true}'}]}}]}
        self.assertIn('ok',parse_chat_response(data,'coder'))

    def test_parsing_null(self):
        with self.assertRaisesRegex(OpenRouterResponseError, 'empty_text_response'):
            object_from_response(None)

    def test_api_error(self):
        with self.assertRaisesRegex(OpenRouterResponseError, 'api_error_code=429'):
            parse_chat_response({'error': {'code':429,'message':'rate limited'}}, 'coder')

if __name__=='__main__':unittest.main()
