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
        self.modules = patch.dict(sys.modules, {'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name,get_filename_list=lambda name:[]),
            'comfy_execution.graph':SimpleNamespace(ExecutionBlocker=Blocker)})
        self.modules.start()
        self.node = plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerGrimoire']()

    def tearDown(self):
        self.modules.stop(); self.temp.cleanup()

    def call(self, replies=('A red mug.',), **kwargs):
        kwargs.setdefault('action','Send')
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
        result,_=self.call(message='JSON please',output_selection='JSON only',chat_mode='Prompt workshop')
        self.assertIsInstance(result['result'][0],Blocker)
        self.assertEqual(result['result'][1],'A red mug.')
        self.assertEqual(select_output('```json\n{"summary":{"caption":"Mug"}}\n```','JSON field','summary.caption'),'Mug')
        with self.assertRaises(ValueError):memory_path('../not-safe')

    def test_canvas_dimensions_are_permanent_sockets(self):
        schema=self.node.INPUT_TYPES()['optional']
        for name in ('width','height'):
            self.assertTrue(schema[name][1]['forceInput'])

    def test_appearance_is_in_every_request(self):
        appearance=plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerAppearanceOverrides']().build(hair_color='Brown')['result'][0]
        _,execute=self.call(message='New scene',appearance=appearance)
        self.assertIn('Brown',execute.call_args.kwargs['system_prompt'])

    def test_saved_settings_and_reuse_without_model_call(self):
        self.call(message='Hello',task_instructions='Write travel scenes',pinned_facts='Green coat')
        state=read_memory(memory_path('chapter-1234'))
        self.assertEqual(state['settings']['task_instructions'],'Write travel scenes')
        self.assertEqual(state['settings']['pinned_facts'],'Green coat')
        with patch('dart_plugin.py.nodes.grimoire.load_local_clip',side_effect=AssertionError('Must not load a model')):
            result=self.node.chat('chapter-1234')
        self.assertIsInstance(result['result'][0],Blocker)
        self.assertEqual(len(read_memory(memory_path('chapter-1234'))['turns']),2)

    def test_image_reference_is_captioned_and_remembered_as_text(self):
        import torch
        execute=Mock(return_value=SimpleNamespace(args=['A green coat.']))
        with patch('dart_plugin.py.nodes.grimoire.load_local_clip',return_value='encoder'), patch('dart_plugin.py.nodes.grimoire.caption_image',return_value='Green coat on a chair.') as caption, patch('dart_plugin.py.nodes.grimoire.execute_generation',execute):
            self.node.chat('chapter-1234',message='Use this outfit',action='Send',image=torch.zeros(1,16,16,3))
        self.assertEqual(caption.call_args.args[0].shape,(1,16,16,3))
        self.assertIn('Green coat on a chair.',read_memory(memory_path('chapter-1234'))['turns'][0]['content'])
        self.assertNotIn('image',execute.call_args.kwargs)

    def test_moss_validation_blocks_out_of_bounds_boxes(self):
        layout=dict(summary={'caption':'Mug','meta':[],'canvas':'single'},items=[dict(label='object',caption='Mug',bbox=[-999,-100,100,100])],bbox_coord_space='abs_centralized',bbox_format='yxyx')
        result,_=self.call(replies=(json.dumps(layout),),message='Layout',output_selection='MOSS JSON layout',chat_mode='Prompt workshop')
        self.assertIsInstance(result['result'][0],Blocker)

    def test_conversation_does_not_force_json_or_retry(self):
        value,execute=self.call(message='Discuss composition',output_selection='MOSS JSON layout')
        self.assertEqual(execute.call_count,1)
        self.assertIn('CURRENT MODE: Conversation',execute.call_args.kwargs['system_prompt'])
        self.assertNotIn('MANDATORY OUTPUT FORMAT',execute.call_args.kwargs['system_prompt'])
        self.assertEqual(value['result'][0],'A red mug.')

    def test_workshop_supplies_native_moss_contract_and_style(self):
        layout=dict(summary=dict(meta=['photo'],canvas='single',caption='A red mug on a table.'),items=[dict(label='object',caption='Red mug',bbox=[-200,-200,200,200])],bbox_coord_space='abs_centralized',bbox_format='yxyx')
        value,execute=self.call(replies=(json.dumps(layout),),message='Mug',chat_mode='Prompt workshop',output_selection='MOSS JSON layout',width=1728,height=2144,style_preset='Photo · Bright lifestyle')
        prompt=execute.call_args.kwargs['system_prompt']
        self.assertIn('TOP-LEFT PIXELS',prompt)
        self.assertIn('width=1728, height=2144',prompt)
        self.assertIn('Bright lifestyle',prompt)
        self.assertEqual(json.loads(value['result'][0]),layout)
        self.assertTrue(read_memory(memory_path('chapter-1234'))['turns'][-1]['valid'])

    def test_generic_scene_json_is_not_a_moss_layout(self):
        value,execute=self.call(replies=('{"subject":"Mug","scene_description":"Table"}',),message='Mug',chat_mode='Prompt workshop',output_selection='MOSS JSON layout')
        self.assertIsInstance(value['result'][0],Blocker)
        self.assertEqual(execute.call_count,1)
        self.assertFalse(read_memory(memory_path('chapter-1234'))['turns'][-1]['valid'])

    def test_edit_branches_only_after_success_and_checks_original(self):
        self.call(message='First')
        self.call(message='Second')
        self.call(replies=('New first answer',),message='Edited first',action='Edit message',edit_index=0,edit_original='First')
        state=read_memory(memory_path('chapter-1234'))
        self.assertEqual([t['content'] for t in state['turns']],['Edited first','New first answer'])
        with self.assertRaisesRegex(ValueError,'changed'):
            self.call(action='Edit message',message='Stale',edit_index=0,edit_original='First')
        self.assertEqual(read_memory(memory_path('chapter-1234')),state)

    def test_manual_assistant_edit_validates_without_generation(self):
        from dart_plugin.py.dart.grimoire import edit_assistant
        self.call(message='First')
        self.call(message='Second')
        value=edit_assistant('chapter-1234',1,'A red mug.','A blue mug.')
        self.assertEqual(len(value['turns']),2)
        self.assertEqual(value['turns'][1]['content'],'A blue mug.')
        with self.assertRaisesRegex(ValueError,'changed'):
            edit_assistant('chapter-1234',1,'A red mug.','A green mug.')

    def test_butt_size_recipe_and_custom(self):
        node=plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerAppearanceOverrides']()
        appearance=node.build(butt_size='Large butt')['result'][0]
        self.assertEqual(appearance['traits']['butt_size'],'Large butt')
        _,execute=self.call(message='Scene',appearance=appearance)
        self.assertIn('Large butt',execute.call_args.kwargs['system_prompt'])
        self.assertEqual(node.build(butt_size='Custom',butt_size_custom='Rounded hips')['result'][0]['traits']['butt_size'],'Rounded hips')

    def test_conversational_style_is_live_without_forcing_a_prompt(self):
        value,execute=self.call(message='What lighting works indoors?',output_selection='MOSS JSON layout',style_preset='Photo · Bright lifestyle')
        self.assertEqual(value['result'][0],'A red mug.')
        self.assertEqual(execute.call_count,1)
        system=execute.call_args.kwargs['system_prompt']
        self.assertIn('CURRENT VISUAL STYLE: Photo · Bright lifestyle',system)
        self.assertIn('only when a prompt is requested',system)
        _,execute=self.call(message='Now revise the scene',output_selection='MOSS JSON layout',style_preset='Photo · Direct flash')
        self.assertIn('STYLE SETTING CHANGED',execute.call_args.kwargs['system_prompt'])
        self.assertIn('Current selection: Photo · Direct flash',execute.call_args.kwargs['system_prompt'])

    def test_conversation_validates_json_prompt_and_records_its_format(self):
        layout=dict(summary=dict(meta=['photo'],canvas='single',caption='A red mug on a table.'),items=[dict(label='object',caption='Red mug',bbox=[-200,-200,200,200])],bbox_coord_space='abs_centralized',bbox_format='yxyx')
        value,execute=self.call(replies=(json.dumps(layout),),message='Write the prompt',output_selection='MOSS JSON layout')
        self.assertEqual(json.loads(value['result'][0]),layout)
        self.assertEqual(read_memory(memory_path('chapter-1234'))['turns'][-1]['mode'],'MOSS JSON layout')
        value,execute=self.call(replies=('{"subject":"mug"}',),message='Revise the prompt',output_selection='MOSS JSON layout')
        self.assertIsInstance(value['result'][0],Blocker)
        self.assertEqual(execute.call_count,1)
