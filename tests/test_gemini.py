from test_regressions import plugin
import unittest,os,json,tempfile,sys
from types import SimpleNamespace
from unittest.mock import patch,MagicMock
from urllib.error import HTTPError,URLError
import torch
from dart_plugin.py.dart import gemini_assistant as gemini,credentials
from dart_plugin.py.dart.openai_assistant import execute_generation,OpenAIRequestError

class GeminiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.modules=patch.dict(sys.modules,{'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name)});self.modules.start()
    def tearDown(self):gemini._session_key='';self.modules.stop();self.temp.cleanup()
    def test_keys_are_provider_isolated_and_never_returned(self):
        credentials.store_key('openai','sk-test-openai-not-a-real-key')
        secret='test-gemini-not-a-real-api-key';gemini.set_persistent_key(secret)
        self.assertEqual(gemini.resolve_key(),secret);self.assertNotIn(secret,str(gemini.key_status()))
        gemini.set_persistent_key('');self.assertFalse(credentials.credential_path('gemini').exists())
        self.assertTrue(credentials.credential_path('openai').exists())
    def execute(self,response=None,error=None,**kwargs):
        opener=MagicMock();opener.open.return_value.__enter__.return_value.read.return_value=json.dumps(response or {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'private thought','thought':True},{'text':'A green cloak.'}]}}],'usageMetadata':{'promptTokenCount':15,'candidatesTokenCount':12}}).encode()
        if error:opener.open.side_effect=error
        with patch.dict(os.environ,{'GEMINI_API_KEY':'test-not-a-real-gemini-key'}),patch.object(gemini,'build_opener',return_value=opener):
            value=execute_generation(gemini.GeminiEncoder(),prompt='Describe',**kwargs)
        return value,opener.open.call_args.args[0]
    def test_text_and_multiple_images_use_official_endpoint_and_header(self):
        result,request=self.execute(image=[torch.zeros(1,4,4,3),torch.ones(1,5,5,3)],thinking=True)
        self.assertEqual(result.args,['A green cloak.']);self.assertEqual(result.api_usage['input_tokens'],15)
        self.assertTrue(request.full_url.startswith('https://generativelanguage.googleapis.com/v1beta/models/'))
        self.assertNotIn('key=',request.full_url);self.assertIn('X-goog-api-key',request.headers)
        payload=json.loads(request.data);self.assertEqual(len(payload['contents'][0]['parts']),3)
        self.assertEqual(payload['generationConfig']['thinkingConfig']['thinkingLevel'],'HIGH')
    def test_errors_and_truncation_are_not_silently_retried(self):
        for reason in ('MAX_TOKENS','SAFETY'):
            with self.assertRaises(OpenAIRequestError):self.execute(response={'candidates':[{'finishReason':reason}]})
        with self.assertRaises(OpenAIRequestError):self.execute(error=URLError('connection'))
