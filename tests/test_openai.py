from test_regressions import plugin
import io
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch
from urllib.error import HTTPError, URLError
import torch

from dart_plugin.py.dart.openai_assistant import OpenAIEncoder, OpenAIRequestError, MODELS, execute_generation
from dart_plugin.py.dart.memory import offload_after
from dart_plugin.py.dart.openai_assistant import set_session_key, key_status, resolve_key
from dart_plugin.py.dart.openai_routes import trusted_request


class OpenAITests(unittest.TestCase):
    def tearDown(self): set_session_key('')

    def test_ui_session_key_is_write_only_and_environment_is_untouched(self):
        secret='sk-test-secret-not-a-real-key'
        with patch.dict(os.environ,{},clear=True):
            set_session_key(secret)
            self.assertEqual(resolve_key('OPENAI_API_KEY'),secret)
            self.assertNotIn(secret,str(key_status()))
            self.assertNotIn('OPENAI_API_KEY',os.environ)
            self.assertTrue(key_status()['session_configured'])
            set_session_key('')
            self.assertFalse(key_status()['configured'])

    def test_key_updates_reject_cross_origin_or_unauthenticated_remote_posts(self):
        def request(headers,remote='127.0.0.1'):
            return SimpleNamespace(headers=headers,host='pod.example:8188',remote=remote)
        self.assertTrue(trusted_request(request({'Origin':'https://pod.example:8188'},'10.0.0.1')))
        self.assertFalse(trusted_request(request({'Origin':'https://evil.example'})))
        self.assertFalse(trusted_request(request({'Sec-Fetch-Site':'cross-site'})))
        self.assertFalse(trusted_request(request({},'10.0.0.1')))
    def request(self, value=None, label=None, error=None, **kwargs):
        opener = MagicMock()
        response = opener.open.return_value.__enter__.return_value
        response.read.return_value = json.dumps(value or {'status':'completed', 'output':[
            {'type':'message','content':[{'type':'output_text','text':'A red mug.'}]}],
            'usage':{'input_tokens':10,'output_tokens':20,'output_tokens_details':{'reasoning_tokens':3}}}).encode()
        if error: opener.open.side_effect = error
        with patch.dict(os.environ, {'MAGE_API_TEST':'test-secret-not-a-real-key'}), \
             patch('dart_plugin.py.dart.openai_assistant.build_opener', return_value=opener):
            encoder=OpenAIEncoder(label or next(iter(MODELS)), key_env='MAGE_API_TEST')
            result=encoder.execute(prompt='A mug', **kwargs)
        return result, encoder, opener.open.call_args.args[0]

    def test_secret_stays_in_header_and_store_is_disabled(self):
        result,encoder,request=self.request(thinking=True)
        payload=json.loads(request.data)
        self.assertEqual(request.full_url,'https://api.openai.com/v1/responses')
        self.assertEqual(request.get_header('Authorization'),'Bearer test-secret-not-a-real-key')
        self.assertNotIn('test-secret',str(payload)+str(encoder.calls)+str(result.args))
        self.assertFalse(payload['store']);self.assertEqual(payload['reasoning']['effort'],'medium')
        self.assertNotIn('temperature',payload);self.assertNotIn('seed',payload)
        self.assertEqual(encoder.calls[0]['reasoning_tokens'],3)

    def test_sol_uses_supported_minimum_reasoning_when_thinking_is_off(self):
        _,_,request=self.request(label=list(MODELS)[1],thinking=False)
        self.assertEqual(json.loads(request.data)['reasoning']['effort'],'low')
        _,_,request=self.request(thinking=False)
        self.assertEqual(json.loads(request.data)['reasoning']['effort'],'none')

    def test_reference_image_is_encoded_without_external_image_host(self):
        _,_,request=self.request(image=torch.zeros(1,16,32,3))
        image=json.loads(request.data)['input'][0]['content'][1]
        self.assertEqual(image['type'],'input_image')
        self.assertTrue(image['image_url'].startswith('data:image/png;base64,'))

    def test_refusal_and_incomplete_answers_are_not_rewritten(self):
        for response in [{'status':'incomplete','output':[]},
                         {'status':'completed','output':[{'type':'message','content':[{'type':'refusal','refusal':'No'}]}]}]:
            with self.assertRaises(OpenAIRequestError):self.request(response)

    def test_http_and_connection_errors_are_actionable_and_hide_provider_body(self):
        for code in (401,403,429,500):
            error=HTTPError('https://api.openai.com/v1/responses',code,'test-secret-not-a-real-key',{},io.BytesIO(b'secret body'))
            with self.assertRaises(OpenAIRequestError) as caught:self.request(error=error)
            self.assertNotIn('secret',str(caught.exception));self.assertIn(str(code),str(caught.exception))
        with self.assertRaisesRegex(OpenAIRequestError,'may still have been processed and billed'):
            self.request(error=URLError('test-secret'))

    def test_cloud_unload_never_touches_local_model_management(self):
        with patch.dict(os.environ,{'MAGE_API_TEST':'test-secret'}):
            encoder=OpenAIEncoder(key_env='MAGE_API_TEST')
        with offload_after(encoder,True):pass

    def test_unknown_or_missing_credentials_fail_before_network(self):
        with patch.dict(os.environ,{},clear=True),self.assertRaisesRegex(ValueError,'Add an API key'):
            OpenAIEncoder()
        with self.assertRaisesRegex(ValueError,'dropdown'):OpenAIEncoder(model='unknown-model')

    def test_multiple_reference_images_share_one_request(self):
        _,_,request=self.request(image=[torch.zeros(1,16,16,3),torch.ones(1,16,16,3)])
        content=json.loads(request.data)['input'][0]['content']
        self.assertEqual([p['type'] for p in content],['input_text','input_image','input_image'])


if __name__=='__main__':unittest.main()
