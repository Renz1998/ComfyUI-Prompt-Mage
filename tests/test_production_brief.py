from test_regressions import plugin
import json,sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
from dart_plugin.py.dart import production_brief as brief
from dart_plugin.py.dart.grimoire import memory_path,read_memory,save_memory
from dart_plugin.py.nodes.grimoire import PromptMageGrimoire

class Blocker:
    def __init__(self,message):self.message=message

class ProductionBriefTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.modules=patch.dict(sys.modules,{'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name,get_output_directory=lambda:self.temp.name+'/out'),'comfy_execution.graph':SimpleNamespace(ExecutionBlocker=Blocker)});self.modules.start()
        self.chapter='test-production-chat';self.state={'version':1,'summary':'','turns':[{'role':'user','content':'Three travel photos, green cloak, 4:5.','id':'a'*32},{'role':'assistant','content':'Agreed, a three-frame travel carousel.','id':'b'*32}],'settings':{'style_preset':'Photo · Travel diary'}};save_memory(memory_path(self.chapter),self.state)
        self.draft=dict(brief='A traveler in a green cloak explores a village.',shared_rules='Same cloak.',review_rules='Check pose and cloak.',style_preset='Photo · Travel diary',style_notes='',shot_count=3,aspect_ratio='4:5',width=None,height=None,references=[])
    def tearDown(self):self.modules.stop();self.temp.cleanup()
    def export(self):return brief.compile_brief(self.chapter,lambda system,prompt:json.dumps(self.draft),appearance={'enabled':True,'trigger':'traveler'})
    def test_explicit_snapshot_persists_and_later_chat_does_not_change_it(self):
        one=self.export();state=read_memory(memory_path(self.chapter));state['turns'].append({'role':'user','content':'Actually discuss another scene.'});save_memory(memory_path(self.chapter),state)
        self.assertEqual(brief.latest(self.chapter)['id'],one['id']);self.assertEqual(brief.read(one['id'])['settings']['shot_count'],3)
        two=self.export();self.assertNotEqual(one['id'],two['id']);self.assertEqual(brief.latest(self.chapter)['id'],two['id']);self.assertEqual(brief.read(one['id']),one)
    def test_provider_keys_and_caps_cannot_be_injected(self):
        for key in ('assistant_backend','api_key','max_calls','max_renders','passing_score'):
            with self.assertRaises(ValueError):brief.validate({**self.draft,key:'bad'}, {})
    def test_stale_conversation_is_rejected_before_publication(self):
        def generate(*args):
            state=read_memory(memory_path(self.chapter));state['summary']='changed';save_memory(memory_path(self.chapter),state);return json.dumps(self.draft)
        with self.assertRaisesRegex(ValueError,'Conversation changed'):brief.compile_brief(self.chapter,generate)
        self.assertIsNone(brief.latest(self.chapter))
    def test_ranges_styles_references_and_paths_are_validated(self):
        for patch_value in ({'shot_count':True},{'shot_count':50},{'aspect_ratio':'anything'},{'style_preset':'invented'},{'width':100},{'references':[{'id':'a'*32,'role':'Outfit'}]}):
            with self.assertRaises(ValueError):brief.validate({**self.draft,**patch_value},{})
        with self.assertRaises(ValueError):brief.read('../escape')
    def test_empty_chat_makes_no_model_request(self):
        save_memory(memory_path(self.chapter),{'version':1,'summary':'','turns':[]})
        def no_call(*args):self.fail('No model should be loaded or called')
        with self.assertRaisesRegex(ValueError,'Discuss'):brief.compile_brief(self.chapter,no_call)
    def test_use_latest_socket_is_read_only_and_keeps_old_output_slots(self):
        value=PromptMageGrimoire().chat(self.chapter,action='Use latest')
        self.assertEqual(len(value['result']),5);self.assertEqual(value['result'][4],{'conversation_id':self.chapter});self.assertIsInstance(value['result'][0],Blocker)
    def test_foundry_freezes_appearance_and_preserves_its_selected_provider(self):
        from dart_plugin.py.nodes.foundry import PromptMageFoundryPlan
        from dart_plugin.py.dart import foundry_ai,foundry
        exported=self.export()
        with patch.object(foundry_ai,'plan',side_effect=lambda value,*args:value):
            PromptMageFoundryPlan().prepare(run_id='c'*32,brief=exported['settings']['brief'],brief_id=exported['id'],shot_count=3,max_renders=9,max_calls=20)
        value=foundry.read('c'*32);self.assertEqual(value['appearance']['trigger'],'traveler');self.assertEqual(value['config']['assistant_backend'],'Local Qwen');self.assertEqual(value['limits']['calls'],20);self.assertEqual(value['production_brief_source']['id'],exported['id'])
