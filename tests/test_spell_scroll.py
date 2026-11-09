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
