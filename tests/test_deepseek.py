from test_regressions import plugin
import json
import os
import unittest
from urllib.error import HTTPError
from unittest.mock import MagicMock, patch
import torch
from dart_plugin.py.dart.deepseek_assistant import DeepSeekEncoder, MODELS, set_session_key, key_status, resolve_key
from dart_plugin.py.dart.openai_assistant import OpenAIRequestError, key_status as openai_status


class DeepSeekTests(unittest.TestCase):
    def tearDown(self):
        set_session_key('')

    def request(self, model=None, choice=None, error=None, **kwargs):
        opener = MagicMock()
        if error:
            opener.open.side_effect = error
        opener.open.return_value.__enter__.return_value.read.return_value = json.dumps({
            'choices': [choice or {'finish_reason':'stop','message':{'content':'A red mug.', 'reasoning_content':'PRIVATE'}}],
            'usage': {'prompt_tokens':10,'completion_tokens':20,'completion_tokens_details':{'reasoning_tokens':5}}
        }).encode()
        with patch.dict(os.environ, {'DEEPSEEK_API_KEY':'test-not-real'}), patch('dart_plugin.py.dart.deepseek_assistant.build_opener', return_value=opener):
            encoder = DeepSeekEncoder(model or next(iter(MODELS)))
            result = encoder.execute(prompt='Describe a mug', **kwargs)
        return encoder, result, opener

    def test_key_isolation_and_no_readback(self):
        before = openai_status()
        with patch.dict(os.environ, {}, clear=True):
            set_session_key('sk-test-not-a-real-deepseek-key')
            self.assertTrue(key_status()['configured'])
            self.assertNotIn('sk-test', str(key_status()))
            self.assertEqual(resolve_key('DEEPSEEK_API_KEY'), 'sk-test-not-a-real-deepseek-key')
            self.assertFalse(os.environ.get('DEEPSEEK_API_KEY'))
        self.assertEqual(openai_status(), before)

    def test_payload_thinking_usage_and_vision(self):
        encoder, result, opener = self.request(thinking=True, image=torch.zeros(1,16,16,3))
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.deepseek.com/chat/completions')
        payload = json.loads(request.data)
        self.assertEqual(payload['model'], 'deepseek-flash')
        self.assertEqual(payload['thinking'], {'type':'enabled'})
        self.assertEqual(payload['reasoning_effort'], 'high')
        self.assertTrue(payload['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,'))
        self.assertEqual(result.args, ['A red mug.'])
        self.assertEqual(encoder.calls[0]['reasoning_tokens'], 5)
        self.assertNotIn('PRIVATE', str(result))
        self.assertEqual(opener.open.call_count, 1)

    def test_pro_vision_fails_before_request_and_truncation_refusal_fail(self):
        with self.assertRaisesRegex(ValueError, 'text-only'):
            self.request(model=list(MODELS)[1], image=torch.zeros(1,16,16,3))
        for choice in [dict(finish_reason='length',message={'content':'partial'}),
                       dict(finish_reason='content_filter',message={'content':''}),
                       dict(finish_reason='stop',message={'content':'','reasoning_content':'private'})]:
            with self.assertRaises(OpenAIRequestError):
                self.request(choice=choice)

    def test_non_thinking_and_archmage_registration(self):
        _, _, opener = self.request(thinking=False)
        payload = json.loads(opener.open.call_args.args[0].data)
        self.assertEqual(payload['thinking'], {'type':'disabled'})
        self.assertNotIn('reasoning_effort', payload)
        schema = plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerArchmageBeta'].INPUT_TYPES()
        self.assertIn('DeepSeek API', schema['optional']['assistant_backend'][0])
        self.assertEqual(schema['optional']['deepseek_model'][0], list(MODELS))

    def test_billing_and_auth_errors_do_not_echo_provider_secrets(self):
        import io
        for code in (401, 402, 429):
            with self.assertRaises(OpenAIRequestError) as caught:
                self.request(error=HTTPError('https://api.deepseek.com/chat/completions', code,
                                            'secret-key-detail', {}, io.BytesIO(b'private provider body')))
            self.assertIn(str(code), str(caught.exception))
            self.assertNotIn('secret', str(caught.exception))
            self.assertNotIn('private', str(caught.exception))
