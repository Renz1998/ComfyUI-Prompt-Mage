from test_regressions import plugin
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from dart_plugin.py.dart import openai_assistant as oa, deepseek_assistant as ds
from dart_plugin.py.dart.credentials import credential_path


class CredentialTests(unittest.TestCase):
    def test_restart_replace_remove_and_provider_isolation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {'folder_paths':SimpleNamespace(get_user_directory=lambda:directory)}), patch.dict('os.environ', {}, clear=True):
            try:
                oa.set_persistent_key('sk-openai-synthetic-test-key')
                ds.set_persistent_key('sk-deepseek-synthetic-test-key')
                oa.set_session_key('');ds.set_session_key('')
                self.assertEqual(oa.resolve_key('OPENAI_API_KEY'),'sk-openai-synthetic-test-key')
                self.assertEqual(ds.resolve_key('DEEPSEEK_API_KEY'),'sk-deepseek-synthetic-test-key')
                self.assertTrue(oa.key_status()['saved_configured'])
                self.assertNotIn('sk-',str(oa.key_status()))
                oa.set_persistent_key('sk-openai-replacement-test-key')
                self.assertNotIn('sk-openai-synthetic-test-key',credential_path('openai').read_text())
                ds.set_persistent_key('')
                self.assertFalse(credential_path('deepseek').exists())
                self.assertEqual(ds.resolve_key('DEEPSEEK_API_KEY'),'')
                self.assertEqual(oa.resolve_key('OPENAI_API_KEY'),'sk-openai-replacement-test-key')
            finally:
                oa.set_session_key('');ds.set_session_key('')
