from test_regressions import plugin
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from dart_plugin.py.dart.grimoire import memory_path, read_memory, save_memory, select_output


class Blocker:
    def __init__(self, reason): self.reason = reason


class GrimoireTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.modules = patch.dict(sys.modules, {'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name),
            'comfy_execution.graph':SimpleNamespace(ExecutionBlocker=Blocker)})
        self.modules.start()
        self.node = plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerGrimoire']()

    def tearDown(self):
        self.modules.stop(); self.temp.cleanup()

    def call(self, replies=('A red mug.',), **kwargs):
        execute = Mock(side_effect=[SimpleNamespace(args=[r]) for r in replies])
        with patch('dart_plugin.py.nodes.grimoire.load_local_clip',return_value='encoder'), patch('dart_plugin.py.nodes.grimoire.execute_generation',execute):
            value = self.node.chat('chapter-1234', **kwargs)
        return value, execute

    def test_persistence_next_step_regenerate_and_clear(self):
        self.call(message='Start a travel scene', pinned_facts='Character wears a green cloak')
        value, execute = self.call(replies=('Second scene.',),action='Next step',pinned_facts='Character wears a green cloak')
        self.assertIn('A red mug.', execute.call_args.kwargs['prompt'])
        self.assertIn('green cloak',execute.call_args.kwargs['system_prompt'])
        self.assertEqual(len(read_memory(memory_path('chapter-1234'))['turns']),4)
        self.call(replies=('Replacement second scene.',),action='Regenerate')
        self.assertEqual(len(read_memory(memory_path('chapter-1234'))['turns']),4)
        result, execute = self.call(action='Clear conversation')
        execute.assert_not_called()
        self.assertIsInstance(result['result'][0],Blocker)
        self.assertEqual(read_memory(memory_path('chapter-1234'))['turns'],[])

    def test_compaction_preserves_recent_turns_and_pinned_fields(self):
        state={'version':1,'summary':'Earlier fact','turns':[{'role':'user' if i%2==0 else 'assistant','content':str(i)} for i in range(14)]}
        save_memory(memory_path('chapter-1234'),state)
        result, execute = self.call(replies=('Summary of older messages.','New answer.'),message='Next',pinned_facts='Pinned forever')
        saved=read_memory(memory_path('chapter-1234'))
        self.assertEqual(saved['summary'],'Summary of older messages.')
        self.assertEqual(saved['turns'][0]['content'],'8')
        self.assertIn('Pinned forever',execute.call_args.kwargs['system_prompt'])
        self.assertTrue(result['ui']['grimoire'][0]['report']['compacted'])

    def test_failed_generation_does_not_mutate_saved_memory(self):
        self.call(message='Initial')
        before=memory_path('chapter-1234').read_bytes()
        with patch('dart_plugin.py.nodes.grimoire.load_local_clip',return_value='encoder'), patch('dart_plugin.py.nodes.grimoire.execute_generation',side_effect=ValueError('failed')), patch('dart_plugin.py.dart.memory.release_assistant_model'):
            with self.assertRaises(ValueError):self.node.chat('chapter-1234',action='Regenerate')
        self.assertEqual(memory_path('chapter-1234').read_bytes(),before)

    def test_output_selection_blocks_bad_json_but_retains_answer(self):
        result,_=self.call(message='JSON please',output_selection='JSON only')
        self.assertIsInstance(result['result'][0],Blocker)
        self.assertEqual(result['result'][1],'A red mug.')
        self.assertEqual(select_output('```json\n{"summary":{"caption":"Mug"}}\n```','JSON field','summary.caption'),'Mug')
        with self.assertRaises(ValueError):memory_path('../not-safe')

    def test_appearance_is_in_every_request(self):
        appearance=plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerAppearanceOverrides']().build(hair_color='Brown')['result'][0]
        _,execute=self.call(message='New scene',appearance=appearance)
        self.assertIn('Brown',execute.call_args.kwargs['system_prompt'])

    def test_image_reference_is_captioned_and_remembered_as_text(self):
        import torch
        execute=Mock(return_value=SimpleNamespace(args=['A green coat.']))
        with patch('dart_plugin.py.nodes.grimoire.load_local_clip',return_value='encoder'), patch('dart_plugin.py.nodes.grimoire.caption_image',return_value='Green coat on a chair.') as caption, patch('dart_plugin.py.nodes.grimoire.execute_generation',execute):
            self.node.chat('chapter-1234',message='Use this outfit',image=torch.zeros(1,16,16,3))
        self.assertEqual(caption.call_args.args[0].shape,(1,16,16,3))
        self.assertIn('Green coat on a chair.',read_memory(memory_path('chapter-1234'))['turns'][0]['content'])
        self.assertNotIn('image',execute.call_args.kwargs)

    def test_moss_validation_blocks_out_of_bounds_boxes(self):
        layout=dict(summary={'caption':'Mug','meta':[],'canvas':'single'},items=[dict(label='object',caption='Mug',bbox=[-999,-100,100,100])],bbox_coord_space='abs_centralized',bbox_format='yxyx')
        result,_=self.call(replies=(json.dumps(layout),),message='Layout',output_selection='MOSS JSON layout')
        self.assertIsInstance(result['result'][0],Blocker)
