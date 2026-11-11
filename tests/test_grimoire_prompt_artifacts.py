from test_regressions import plugin
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from dart_plugin.py.dart.grimoire_prompt import compile_moss_response, response_output_mode, prepare_turn, DEFAULT_SYSTEM, LEGACY_SYSTEM, PREVIOUS_DEFAULT_SYSTEM, effective_system
from dart_plugin.py.dart.grimoire import memory_path, save_memory, select_output
from dart_plugin.py.dart.spell_scroll import approve, prompt_from_scroll


def layout(caption='A ceramic cup.'):
    return dict(summary=dict(meta=['photo'],canvas='single',caption=caption),items=[dict(label='object',caption=caption,bbox=[-288,-592,352,32])],bbox_coord_space='abs_centralized',bbox_format='yxyx')


class PromptArtifactTests(unittest.TestCase):
    def test_fences_and_trailing_prose_do_not_enter_the_model_prompt(self):
        native=layout('A cup with a {curved} handle and "tea" lettering.')
        for text in (json.dumps(native)+'\nWait — use only the JSON.', 'Here you go:\n```json\n'+json.dumps(native)+'\n```\nWant another idea?'):
            result=compile_moss_response(text,1536,1024)
            self.assertEqual(json.loads(result),native)
            self.assertNotIn('\n',result)
            self.assertNotIn('Wait',result)
            self.assertEqual(response_output_mode(text,'Conversation','MOSS JSON layout'),'MOSS JSON layout')

    def test_official_pixel_draft_conversion_and_canvas_match(self):
        draft=layout();draft.update(width=1536,height=1024,bbox_coord_space='abs',bbox_format='xyxy');draft['items'][0]['bbox']=[176,224,800,864]
        result=json.loads(compile_moss_response(json.dumps(draft),1536,1024))
        self.assertEqual(result['items'][0]['bbox'],[-288,-592,352,32])
        self.assertNotIn('width',result)
        draft['items'][0]['bbox']=[176.8,224.2,800.1,864.8]
        self.assertEqual(json.loads(compile_moss_response(json.dumps(draft),1536,1024))['items'][0]['bbox'],[-288,-592,353,33])
        with self.assertRaisesRegex(ValueError,'canvas differs'):
            compile_moss_response(json.dumps(draft),1728,2144)

    def test_ambiguous_and_incomplete_prompts_are_blocked(self):
        two=json.dumps(layout('Cup.'))+'\nOr this:\n'+json.dumps(layout('Teapot.'))
        with self.assertRaisesRegex(ValueError,'multiple different'):
            compile_moss_response(two,1536,1024)
        with self.assertRaises(ValueError):compile_moss_response('{"summary":',1536,1024)
        with self.assertRaises(ValueError):compile_moss_response('{"subject":"cup"}',1536,1024)
        duplicate=json.dumps(layout())+'\n```json\n'+json.dumps(layout())+'\n```'
        self.assertEqual(json.loads(compile_moss_response(duplicate,1536,1024)),layout())

    def test_legacy_failed_reply_can_be_applied_without_a_new_model_call(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(sys.modules,{'folder_paths':SimpleNamespace(get_user_directory=lambda:directory)}):
            raw='```json\n'+json.dumps(layout())+'\n```\nHere is your prompt.'
            turns=[dict(role='user',content='Cup'),dict(role='assistant',content=raw,mode='MOSS JSON layout',width=1536,height=1024,valid=False)]
            save_memory(memory_path('artifact-chat'),dict(version=1,summary='',turns=turns))
            recovered=prepare_turn(turns[-1]);self.assertTrue(recovered['valid']);self.assertIn('prompt_text',recovered)
            active=approve('main-scroll','artifact-chat',1,raw,'MOSS JSON layout','')
            self.assertEqual(json.loads(active['text']),layout())
            self.assertEqual(json.loads(prompt_from_scroll(active,1536,1024)),layout())

    def test_conversation_and_personality_preserve_custom_system_prompts(self):
        self.assertEqual(effective_system(LEGACY_SYSTEM),DEFAULT_SYSTEM)
        self.assertEqual(effective_system(PREVIOUS_DEFAULT_SYSTEM),DEFAULT_SYSTEM)
        self.assertIn('warm',DEFAULT_SYSTEM)
        self.assertEqual(effective_system('Be a formal technical editor.'),'Be a formal technical editor.')
        self.assertEqual(response_output_mode('Let’s try a warmer window light.','Conversation','MOSS JSON layout'),'Latest response')
        self.assertNotIn('prompt_text',prepare_turn(dict(role='assistant',content='Try warmer light.',mode='Latest response')))
        self.assertNotIn('format_error',prepare_turn(dict(role='assistant',content='Try warmer light.'),{'output_selection':'MOSS JSON layout'}))
        self.assertEqual(select_output('42','JSON only',''),'42')
        self.assertEqual(select_output('Here:\n```json\n{"prompt":"cup"}\n```\nDone.','JSON field','prompt'),'cup')
