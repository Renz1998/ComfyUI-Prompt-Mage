from test_regressions import plugin
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from dart_plugin.py.dart.grimoire import memory_path, save_memory
from dart_plugin.py.dart.spell_scroll import approve, active_scroll


class SpellScrollTests(unittest.TestCase):
    def test_only_explicit_apply_changes_workflow_prompt(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules,{'folder_paths':SimpleNamespace(get_user_directory=lambda:directory)}):
            state=dict(version=1,summary='',turns=[dict(role='user',content='Scene A'),dict(role='assistant',content='Approved A')])
            save_memory(memory_path('chapter-A'),state)
            node=plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerSpellScroll']()
            with self.assertRaisesRegex(ValueError,'No applied prompt'):node.read()
            approve('main-scroll','chapter-A',1,'Approved A','Latest response','')
            for _ in range(3):self.assertEqual(node.read()[0],'Approved A')
            state['turns'] += [dict(role='user',content='Scene B'),dict(role='assistant',content='Unselected B')]
            save_memory(memory_path('chapter-A'),state)
            self.assertEqual(node.read()[0],'Approved A')
            with self.assertRaisesRegex(ValueError,'changed'):
                approve('main-scroll','chapter-A',1,'Mismatched content','Latest response','')
            self.assertEqual(node.read()[0],'Approved A')
            approve('main-scroll','chapter-A',3,'Unselected B','Latest response','')
            self.assertEqual(node.read()[0],'Unselected B')
            save_memory(memory_path('chapter-A'),dict(version=1,summary='',turns=[]))
            self.assertEqual(node.read()[0],'Unselected B')
            self.assertEqual(active_scroll('main-scroll')['conversation_id'],'chapter-A')

    def test_chat_and_workflow_have_separate_execution_roots(self):
        classes=plugin.NODE_CLASS_MAPPINGS
        self.assertFalse(classes['DanbooruTagsTransformerGrimoire'].OUTPUT_NODE)
        self.assertTrue(classes['DanbooruTagsTransformerGrimoireTurn'].OUTPUT_NODE)
        self.assertFalse(classes['DanbooruTagsTransformerSpellScroll'].OUTPUT_NODE)

    def test_source_identity_survives_conversation_compaction(self):
        from dart_plugin.py.dart.grimoire import read_memory
        with tempfile.TemporaryDirectory() as directory,patch.dict(sys.modules,{'folder_paths':SimpleNamespace(get_user_directory=lambda:directory)}):
            path=memory_path('compact-chat')
            save_memory(path,dict(version=1,summary='',turns=[dict(role='user',content='Old'),dict(role='assistant',content='Old reply'),dict(role='user',content='New'),dict(role='assistant',content='Chosen reply')]))
            original=read_memory(path)
            active=approve('main-scroll','compact-chat',3,'Chosen reply','Latest response','')
            from dart_plugin.py.dart.spell_scroll import scroll_path
            legacy=dict(active);legacy.pop('response_id');save_memory(scroll_path('main-scroll'),legacy)
            active=active_scroll('main-scroll');self.assertEqual(active['response_id'],original['turns'][3]['id'])
            original['turns']=original['turns'][-2:];save_memory(path,original)
            shortened=read_memory(path)
            self.assertEqual(active['response_id'],shortened['turns'][1]['id'])
            self.assertNotEqual(active['response_index'],1)
