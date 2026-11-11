from test_regressions import plugin
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import torch
from dart_plugin.py.dart import foundry as store, foundry_ai as ai


class FoundryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.modules=patch.dict(sys.modules,{'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name,get_output_directory=lambda:self.temp.name+'/output')})
        self.modules.start();self.id='a'*32
    def tearDown(self):self.modules.stop();self.temp.cleanup()
    def create(self,**changes):
        values=dict(run_id=self.id,conversation_id='',template_id='single',brief='A traveler studies a map.',shared_rules='One traveler',review_rules='Check the action',shot_count=1,width=1024,height=1024,max_attempts=3,max_renders=3,max_calls=8)
        values.update(changes);return store.create(**values)
    def plan(self):
        value=self.create()
        with patch.object(ai,'generate',return_value=json.dumps({'title':'Trip','shots':[{'title':'Inn','brief':'A traveler studies a map.','criteria':['Map is visible','One traveler']}]})):
            return ai.plan(value)
    def approve(self):self.plan();return store.action(self.id,'approve')
    def composed(self):
        self.approve();attempt=store.reserve(self.id)
        layout={'summary':{'caption':'Traveler studies a map.','meta':['Photo'],'canvas':'single'},'items':[{'label':'object','caption':'Traveler holding a map','bbox':[-512,-512,512,512]}],'bbox_coord_space':'abs_centralized','bbox_format':'yxyx'}
        with patch.object(ai,'generate',return_value=json.dumps(layout)) as generated:
            prompt,seed=ai.compose(self.id,attempt['id'],1024,1024)
        return attempt,prompt,generated
    @staticmethod
    def review_json(status='pass'):
        return json.dumps({'visual_integrity':{key:dict(applicable=True,status='pass',score=90,severity='none',evidence='Visible structures are coherent.') for key in ('anatomy','spatial','clothing','lighting')},'checks':[{'id':'c1','status':status,'score':{'pass':90,'fail':20,'uncertain':50}[status],'evidence':'A map is visible in both hands.'},{'id':'c2','status':'pass','score':90,'evidence':'One traveler is visible.'}],'quality_score':85,'major_defect':False,'summary':'A readable scene.','suggestion':''})
    def test_manual_gates_and_no_automatic_next_job(self):
        self.plan()
        with self.assertRaisesRegex(ValueError,'Approve'):store.reserve(self.id)
        store.action(self.id,'approve');attempt=store.reserve(self.id)
        with self.assertRaises(ValueError):store.reserve(self.id)
        with self.assertRaises(ValueError):store.action(self.id,'accept',{'attempt_id':attempt['id']})
        self.assertEqual(store.read(self.id)['usage']['renders'],1)
    def test_actual_pixels_review_and_accept(self):
        attempt,_,_=self.composed();image=torch.rand(1,32,48,3)
        with patch.object(ai,'generate',return_value=self.review_json()) as gen:
            result=ai.review(self.id,attempt['id'],image)
        self.assertIsInstance(gen.call_args.args[4],torch.Tensor)
        self.assertEqual(result['status'],'awaiting_approval');self.assertTrue(ai.image_path(self.id,attempt['id']).exists())
        result=store.action(self.id,'accept',{'attempt_id':attempt['id']})
        self.assertEqual(result['status'],'complete');self.assertEqual(result['usage']['renders'],1)
        with self.assertRaises(ValueError):store.reserve(self.id)
    def test_saved_image_review_stage_is_published_before_provider_wait(self):
        attempt,_,_=self.composed();events=[]
        server=SimpleNamespace(instance=SimpleNamespace(send_sync=lambda name,payload:events.append(payload)))
        def answer(*args,**kwargs):
            self.assertEqual(events[-1]['foundry'][0]['status'],'reviewing')
            self.assertTrue(events[-1]['foundry'][0]['attempts'][-1]['image'])
            return self.review_json()
        with patch.dict(sys.modules,{'server':SimpleNamespace(PromptServer=server)}),patch.object(ai,'generate',side_effect=answer):
            ai.review(self.id,attempt['id'],torch.zeros(1,16,16,3))
    def test_retry_preserves_prompt_changes_seed_and_has_no_composition_call(self):
        attempt,prompt,_=self.composed()
        with patch.object(ai,'generate',return_value=self.review_json('fail')):ai.review(self.id,attempt['id'],torch.zeros(1,16,16,3))
        second=store.reserve(self.id)
        with patch.object(ai,'generate') as gen:other,seed=ai.compose(self.id,second['id'],1024,1024)
        gen.assert_not_called();self.assertEqual(prompt,other);self.assertNotEqual(seed,attempt['seed'])
    def test_failed_review_archives_image_and_retry_does_not_render(self):
        attempt,_,_=self.composed()
        with patch.object(ai,'generate',return_value='not JSON') as gen:
            with self.assertRaises(ValueError):ai.review(self.id,attempt['id'],torch.zeros(1,16,16,3))
        gen.assert_called_once();self.assertTrue(store.read(self.id)['attempts'][0]['image'])
        with patch.object(ai,'generate',return_value=self.review_json('uncertain')):value=ai.review(self.id,attempt['id'])
        self.assertEqual(value['usage']['renders'],1);self.assertEqual(value['attempts'][0]['review']['verdict'],'uncertain')
    def test_review_requires_all_observable_checks_and_derives_verdict(self):
        value=json.loads(self.review_json('fail'));value['verdict']='pass'
        self.assertEqual(ai.validate_review(value,['Map','Traveler'])['verdict'],'fail')
        for checks in ([{},{}],['bad'],[{'id':'c1'}],[{'id':'c1'},{'id':'c1'}]):
            with self.assertRaises(ValueError):ai.validate_review({'checks':checks},['Map','Traveler'])
    def test_render_and_call_caps_are_enforced_before_work(self):
        self.approve()
        v=store.read(self.id);v['limits']['calls']=1;store.write(v)
        with self.assertRaisesRegex(ValueError,'calls'):store.reserve(self.id)
        v['limits']['calls']=8;v['limits']['renders']=0;store.write(v)
        with self.assertRaisesRegex(ValueError,'budget'):store.reserve(self.id)
    def test_failed_api_call_is_counted_once_without_auto_retry(self):
        value=self.create()
        with patch.object(ai,'encoder_for',return_value='encoder'),patch.object(ai,'execute_generation',side_effect=ValueError('provider failed')) as execute:
            with self.assertRaisesRegex(ValueError,'provider failed'):ai.plan(value)
        execute.assert_called_once();v=store.read(self.id);self.assertEqual(v['usage']['calls'],1);self.assertEqual(v['status'],'needs_attention')
    def test_pause_stop_preserved_on_error_and_no_more_calls(self):
        self.approve();store.action(self.id,'pause');store.fail(self.id,'late error')
        self.assertEqual(store.read(self.id)['status'],'paused')
        with self.assertRaises(ValueError):store.charge(self.id)
        store.action(self.id,'resume');store.action(self.id,'stop');store.fail(self.id,'late error')
        self.assertEqual(store.read(self.id)['status'],'stopped')
        with self.assertRaises(ValueError):store.reserve(self.id)
    def test_template_reuse_requires_no_ai(self):
        self.approve();store.action(self.id,'save_template',{'name':'Inn test'})
        saved=next(t for t in store.templates() if not t['builtin'])
        self.id='b'*32;value=self.create(template_id=saved['id'])
        with patch.object(ai,'generate') as gen:result=ai.plan(value)
        gen.assert_not_called();self.assertEqual(result['status'],'plan_ready')
    def test_review_finishing_during_pause_can_be_accepted_after_resume(self):
        attempt,_,_=self.composed()
        def result(*args,**kwargs):
            store.action(self.id,'pause')
            return self.review_json()
        with patch.object(ai,'generate',side_effect=result):value=ai.review(self.id,attempt['id'],torch.zeros(1,16,16,3))
        self.assertEqual(value['status'],'paused')
        self.assertEqual(store.action(self.id,'resume')['status'],'awaiting_approval')
        self.assertEqual(store.action(self.id,'accept',{'attempt_id':attempt['id']})['status'],'complete')
    def test_source_copy_does_not_include_keys_or_mutate_chat(self):
        from dart_plugin.py.dart.grimoire import memory_path,save_memory
        path=memory_path('chat-source')
        save_memory(path,{'version':1,'summary':'Shared palette','turns':[{'role':'user','content':'A beach sequence'}],'settings':{'assistant_backend':'DeepSeek API','api_key':'do-not-copy','style_preset':'Photo · Bright lifestyle'}})
        before=path.read_bytes();value=self.create(conversation_id='chat-source')
        self.assertEqual(value['config']['assistant_backend'],'Local Qwen');self.assertNotIn('api_key',value['config']);self.assertEqual(before,path.read_bytes());self.assertIn('A beach sequence',value['context'])
    def test_recommended_deepseek_profile_is_explicit_and_vision_capable(self):
        from dart_plugin.py.dart.deepseek_assistant import MODELS
        value=self.create(assistant_profile=store.ASSISTANTS[1]);self.assertEqual(value['config']['assistant_backend'],'DeepSeek API')
        self.assertEqual(MODELS[value['config']['deepseek_model']],'deepseek-flash');self.assertEqual(value['usage']['calls'],0)
        self.id='b'*32;self.assertEqual(self.create()['config']['assistant_backend'],'Local Qwen')
    def test_text_only_deepseek_is_rejected_before_planning_spends_calls(self):
        settings={'assistant_backend':'DeepSeek API','deepseek_model':'DeepSeek V4 Pro · Text only · Check pricing'}
        with patch.object(store,'source_settings',return_value=(settings,'')),patch.object(ai,'generate') as gen:
            with self.assertRaisesRegex(ValueError,'V4 Pro is text-only'):self.create(assistant_profile=store.ASSISTANTS[2])
        gen.assert_not_called();self.assertFalse(store.run_path(self.id).exists())
    def test_paths_and_plan_validation(self):
        for bad in ('../file','a'*31,'A'*32):
            with self.assertRaises(ValueError):store.read(bad)
        for v in ({},[],{'title':'x','shots':[]}):
            with self.assertRaises(ValueError):store.validate_plan(v,1)
        with self.assertRaises(ValueError):self.create(width=1025)
    def test_batch_output_is_rejected(self):
        attempt,_,_=self.composed()
        with patch.object(ai,'generate') as gen:
            with self.assertRaisesRegex(ValueError,'exactly one'):ai.review(self.id,attempt['id'],torch.zeros(2,16,16,3))
        gen.assert_not_called()
    def test_api_planner_receives_actual_images_with_outfit_roles(self):
        from dart_plugin.py.dart import grimoire_attachments as attachments
        value=self.create(assistant_profile=store.ASSISTANTS[1]);identifier='b'*32
        reply={'title':'Outfit test','reference_notes':'Green wool cloak with brass clasps.','shots':[{'title':'Inn','brief':'Traveler wears a green wool cloak with brass clasps in an inn.','criteria':['Green cloak is visible']}]}
        file={'id':identifier,'name':'outfit.png','kind':'image','truncated':False}
        with patch.object(attachments,'load_attachment',return_value=file),patch.object(attachments,'attachment_image',return_value=torch.zeros(1,16,16,3)),patch.object(ai,'generate',return_value=json.dumps(reply)) as generate:
            result=ai.plan(value,attachments=json.dumps([identifier]),reference_instructions='Borrow only the outfit.',reference_roles=json.dumps({identifier:'Outfit'}))
        self.assertEqual(len(generate.call_args.args[4]),1);self.assertIsInstance(generate.call_args.args[4][0],torch.Tensor)
        self.assertIn('borrow Outfit',generate.call_args.args[2]);self.assertIn('do not copy',generate.call_args.args[1].lower());self.assertIn('Green wool',result['plan']['reference_notes'])
    def test_local_reference_descriptions_are_saved_for_later_composition(self):
        value=self.create();plan={'title':'Outfit','shots':[{'title':'Inn','brief':'Green cloak and map','criteria':['Green cloak']} ]}
        with patch.object(ai,'generate',side_effect=['Green wool cloak with brass clasps.',json.dumps(plan)]) as generate:
            result=ai.plan(value,images=[('Connected outfit reference',torch.zeros(1,16,16,3))],reference_instructions='Use its outfit only.')
        self.assertEqual(generate.call_count,2);self.assertIn('brass clasps',result['reference_context']);self.assertEqual(len(result['references']),1)
    def test_style_and_assistant_are_independent_of_chat_reference(self):
        with patch.object(store,'source_settings',return_value=({'assistant_backend':'DeepSeek API','style_preset':'Photo · Cinematic film still'},'A prior script')):
            value=self.create(style_preset='Photo · Amateur Instagram')
        self.assertEqual(value['config']['assistant_backend'],'Local Qwen');self.assertEqual(value['config']['style_preset'],'Photo · Amateur Instagram');self.assertEqual(value['context'],'A prior script')
    def test_structured_or_empty_optional_reference_notes_do_not_break_valid_plans(self):
        value={'title':'Outfit','shots':[{'title':'Inn','brief':'Teal shirt','criteria':['Teal shirt']} ]}
        for notes in ({'Image 1':'Teal short-sleeve shirt'},['Teal fabric','Short sleeves']):
            result=store.validate_plan(dict(value,reference_notes=notes),1);self.assertIsInstance(result['reference_notes'],str);self.assertIn('Teal',result['reference_notes'])
        self.assertNotIn('reference_notes',store.validate_plan(dict(value,reference_notes='  '),1))
    def test_workflow_links_and_clean_defaults(self):
        value=json.loads((Path(__file__).parents[1]/'workflows/experimental/01-foundry-single-frame-moss.json').read_text(encoding='utf-8'));nodes={n['id']:n for n in value['nodes']}
        for identifier,s,ss,t,ts,kind in value['links']:
            self.assertIn(identifier,nodes[s]['outputs'][ss]['links']);self.assertEqual(nodes[t]['inputs'][ts]['link'],identifier)
            self.assertEqual(nodes[s]['outputs'][ss]['type'],kind);self.assertIn(nodes[t]['inputs'][ts]['type'],(kind,'*'))
        f=nodes[151]['mage_foundry_fields'];self.assertEqual(f['shot_count'],1);self.assertFalse(f['conversation_id']);self.assertFalse(f['run_id'])
        self.assertNotIn('DanbooruTagsTransformerGrimoire',[n['type'] for n in nodes.values()]);self.assertEqual(sum('LoraLoader' in n['type'] for n in nodes.values()),1)
        self.assertFalse(nodes[125]['dart_widget_values']['enabled'])
