from test_regressions import plugin
import asyncio
import copy
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from dart_plugin.py.dart import foundry as store,foundry_runner as runner
from dart_plugin.py.dart.foundry_review import assessment


def workflow():
    f=runner.FOUNDRY
    return dict(output={
        '1':dict(class_type=f,inputs={'image':['9',0],'attachments':'[]'}),
        '2':dict(class_type='CLIPTextEncode',inputs={'text':['1',0]}),
        '3':dict(class_type='RandomNoise',inputs={'noise_seed':['1',3]}),
        '4':dict(class_type='EmptyLatentImage',inputs={'batch_size':1}),
        '5':dict(class_type='SamplerCustomAdvanced',inputs={'positive':['2',0],'noise':['3',0],'latent':['4',0]}),
        '6':dict(class_type='VAEDecode',inputs={'samples':['5',0]}),
        '7':dict(class_type=f+'ReviewOutput',inputs={'image':['6',0],'run_id':['1',4],'attempt_id':['1',5]}),
        '8':dict(class_type='SaveImage',inputs={'images':['6',0],'filename_prefix':['1',6]}),
        '9':dict(class_type='LoadImage',inputs={}),
        '10':dict(class_type='SaveImage',inputs={'images':['6',0],'filename_prefix':'unrelated'}),
    },workflow={'nodes':[]})


def review(score=85,quality=85,major=False,status='pass'):
    return dict(checks=[dict(id='c1',criterion='Map visible',status=status,score=score,evidence='Visible map')],quality_score=quality,major_defect=major,summary='Scene review',verdict=status)


class ToleranceTests(unittest.TestCase):
    def test_good_variations_pass_balanced_but_not_strict(self):
        self.assertTrue(assessment(review(82),['Map visible'],'Balanced')['acceptable'])
        self.assertFalse(assessment(review(82),['Map visible'],'Strict')['acceptable'])
        self.assertTrue(assessment(review(68,60),['Map visible'],'Relaxed')['acceptable'])
    def test_major_defects_and_must_haves_block_automatic_acceptance(self):
        self.assertFalse(assessment(review(95,95,True),['Map visible'],'Relaxed')['acceptable'])
        self.assertFalse(assessment(review(60),['! Map visible'],'Relaxed')['acceptable'])
        self.assertFalse(assessment(review(100,status='uncertain'),['! Map visible'],'Relaxed')['acceptable'])
    def test_reviewers_inconsistent_fail_score_is_capped(self):
        self.assertFalse(assessment(review(100,status='fail'),['Map visible'],'Balanced')['acceptable'])


class RunnerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();self.id='a'*32;self.submitted=[];self.active=[];self.history={};self.score_sequence=[85,85];self.gate=None;self.cancel_job=False
        async def validate_prompt(prompt_id,prompt,partial_execution_list=None):return True,None,partial_execution_list,{}
        self.modules=patch.dict(sys.modules,{'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name,get_output_directory=lambda:self.temp.name+'/output'),'execution':SimpleNamespace(validate_prompt=validate_prompt,SENSITIVE_EXTRA_DATA_KEYS=[])})
        self.modules.start()
        def put(entry):
            self.assertFalse(self.active,'The next frame must wait until the previous native job completes')
            self.submitted.append(entry);self.active.append(entry);asyncio.create_task(self.finish(entry))
        queue=SimpleNamespace(put=put,get_current_queue=lambda:(list(self.active),[]),get_history=lambda prompt_id:{prompt_id:self.history[prompt_id]} if prompt_id in self.history else {})
        self.server=SimpleNamespace(prompt_queue=queue,number=0,send_sync=lambda *args:None)
    async def asyncTearDown(self):
        for task in list(runner.TASKS.values()):task.cancel()
        await asyncio.gather(*list(runner.TASKS.values()),return_exceptions=True)
        self.modules.stop();self.temp.cleanup()
    def ready(self,count=2,tries=3):
        value=store.create(self.id,'','single','Traveler with a map','One adult','Check map',count,1024,1024,tries,count*tries,30)
        value.update(status='plan_ready',plan=store.validate_plan({'title':'Trip','shots':[dict(title='Frame '+str(i),brief='Traveler with map',criteria=['Map visible']) for i in range(count)]},count));store.write(value)
        value=store.action(self.id,'approve');value['automation_enabled']=True;store.write(value);runner.save_recipe(self.id,workflow(),'1','client')
    async def finish(self,entry):
        if self.gate:await self.gate.wait()
        job_id=entry[1];root=entry[2]['1'];run_id=root['inputs']['run_id'];attempt_id=root['inputs']['attempt_id']
        if not self.cancel_job:
            with store.LOCK:
                value=store.read(run_id);attempt=store.attempt_for(value,attempt_id)
                attempt['image']=True
                path=store.root()/'images'/run_id/(attempt_id+'.png');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'PNG fixture')
                if value['status'] not in ('paused','stopped'):
                    attempt['review']=review(self.score_sequence.pop(0) if self.score_sequence else 85);attempt['status']='reviewed';value['status']='awaiting_approval'
                store.write(value)
        self.active.remove(entry);self.history[job_id]={'status':{'status_str':'error' if self.cancel_job else 'success','completed':not self.cancel_job}}
    async def test_server_finishes_multiple_frames_without_browser_callbacks(self):
        self.ready();await runner.run(self.server,self.id,poll=0.001)
        value=store.read(self.id);self.assertEqual(value['status'],'complete');self.assertEqual(len(value['accepted']),2);self.assertEqual(len(self.submitted),2)
        self.assertTrue(all(a['automatic'] for a in value['accepted']))
        for entry in self.submitted:self.assertEqual(entry[4],['7','8']);self.assertEqual(len(entry[2]),10);self.assertNotIn('image',entry[2]['1']['inputs'])
    async def test_low_match_retries_then_advances_with_fresh_seeds(self):
        self.ready();self.score_sequence=[30,85,85];await runner.run(self.server,self.id,poll=0.001)
        value=store.read(self.id);self.assertEqual(value['status'],'complete');self.assertEqual(len(self.submitted),3)
        self.assertEqual([a['shot_id'] for a in value['attempts']],['shot-1','shot-1','shot-2']);self.assertEqual(len({a['seed'] for a in value['attempts']}),3)
    async def test_attempt_limit_pauses_instead_of_looping_or_silently_accepting(self):
        self.ready(count=1,tries=2);v=store.read(self.id);v['failure_policy']='Pause for review';store.write(v);self.score_sequence=[20,20];await runner.run(self.server,self.id,poll=0.001)
        value=store.read(self.id);self.assertEqual(value['status'],'needs_attention');self.assertEqual(len(self.submitted),2);self.assertEqual(value['accepted'],[])
        self.assertIn('retry limit',value['last_error'])
        value=store.action(self.id,'accept',{'attempt_id':value['attempts'][0]['id']});self.assertEqual(value['status'],'complete')
    async def test_first_pass_advances_without_using_remaining_tries(self):
        self.ready(count=3,tries=3);self.score_sequence=[85,85,85]
        await runner.run(self.server,self.id,poll=0.001)
        v=store.read(self.id);self.assertEqual(v['status'],'complete');self.assertEqual(len(self.submitted),3)
        self.assertEqual([a['shot_id'] for a in v['attempts']],['shot-1','shot-2','shot-3'])
    async def test_automatic_exhaustion_flags_frame_and_finishes_rest(self):
        self.ready(count=2,tries=2);self.score_sequence=[20,20,90]
        await runner.run(self.server,self.id,poll=0.001)
        v=store.read(self.id);self.assertEqual(v['status'],'complete');self.assertEqual(len(self.submitted),3)
        self.assertEqual(len(v['skipped']),1);self.assertEqual(len(v['accepted']),1)
        self.assertEqual(v['accepted'][0]['shot_id'],'shot-2')
    async def test_pause_and_stop_prevent_next_submission(self):
        for operation in ('pause','stop'):
            if operation=='stop':self.id='b'*32
            self.ready();self.gate=asyncio.Event();task=asyncio.create_task(runner.run(self.server,self.id,poll=0.001))
            while not self.active:await asyncio.sleep(0.001)
            before=len(self.submitted);store.action(self.id,operation);self.gate.set();await task;await asyncio.sleep(0.001)
            self.assertEqual(len(self.submitted),before);self.assertIn(store.read(self.id)['status'],('paused','stopped'))
    async def test_cancellation_is_not_automatically_retried(self):
        self.ready();self.cancel_job=True;await runner.run(self.server,self.id,poll=0.001)
        self.assertEqual(len(self.submitted),1);self.assertEqual(store.read(self.id)['status'],'needs_attention')
    async def test_native_validation_failure_makes_no_queue_job(self):
        self.ready()
        async def invalid(prompt_id,prompt,partial_execution_list=None):return False,{'message':'Missing model'},[],{}
        with patch.dict(sys.modules,{'execution':SimpleNamespace(validate_prompt=invalid)}):await runner.run(self.server,self.id,poll=0.001)
        self.assertEqual(self.submitted,[]);self.assertIn('Missing model',store.read(self.id)['last_error'])
    async def test_validation_error_names_the_node_and_missing_input(self):
        self.ready()
        async def invalid(prompt_id,prompt,partial_execution_list=None):return False,{'message':'Prompt outputs failed validation'},[],{'131':{'class_type':'KSamplerSelect','errors':[{'message':'Required input is missing','details':'sampler_name'}]}}
        with patch.dict(sys.modules,{'execution':SimpleNamespace(validate_prompt=invalid)}):await runner.run(self.server,self.id,poll=0.001)
        error=store.read(self.id)['last_error'];self.assertIn('KSamplerSelect',error);self.assertIn('sampler_name',error);self.assertFalse(self.submitted)
    async def test_resume_review_uses_saved_worker_not_diffusion_target(self):
        self.ready(count=1);attempt=store.reserve(self.id);value=store.read(self.id);value.update(status='ready',resume_review=True);value['attempts'][0].update(image=True,status='error');store.write(value)
        await runner.run(self.server,self.id,poll=0.001)
        self.assertEqual(len(self.submitted),1);self.assertEqual(self.submitted[0][4],['1']);self.assertEqual(self.submitted[0][2]['1']['class_type'],runner.FOUNDRY+'ReviewSaved');self.assertEqual(store.read(self.id)['usage']['renders'],1)
    async def test_duplicate_start_returns_same_task(self):
        self.ready();self.gate=asyncio.Event();first=runner.start(self.server,self.id);self.assertIs(first,runner.start(self.server,self.id));first.cancel()
        await asyncio.gather(first,return_exceptions=True)
    async def test_worker_review_error_is_broadcast_to_the_ui(self):
        self.ready();events=[];self.server.send_sync=lambda name,payload:events.append(payload['foundry'][0])
        async def failed_review(entry):
            value=store.read(self.id);value['attempts'][-1].update(image=True,status='error');value.update(status='needs_attention',last_error='Image saved; use Review saved image.');store.write(value)
            self.active.remove(entry);self.history[entry[1]]={'status':{'status_str':'error','completed':False}}
        self.finish=failed_review;await runner.run(self.server,self.id,poll=0.001)
        self.assertEqual(events[-1]['status'],'needs_attention');self.assertIn('Image saved',events[-1]['last_error']);self.assertEqual(len(self.submitted),1)
    async def test_review_only_recovery_does_not_render_or_continue_old_scenes(self):
        self.ready();attempt=store.reserve(self.id);value=store.read(self.id);value.update(status='needs_attention');value['attempts'][-1].update(image=True,status='error');store.write(value)
        await runner.retry_saved_review(self.server,self.id,continue_run=False);await asyncio.sleep(0.001)
        value=store.read(self.id);self.assertEqual(value['status'],'awaiting_approval');self.assertFalse(value['automation_enabled']);self.assertEqual(value['usage']['renders'],1)
        self.assertEqual(self.submitted[0][4],['1']);self.assertEqual(self.submitted[0][2]['1']['class_type'],runner.FOUNDRY+'ReviewSaved')
    def test_second_plan_is_blocked_for_same_running_workflow(self):
        self.ready();recipe=runner.load_recipe(self.id);recipe['workflow']={'id':'same-workflow'}
        with patch.dict(runner.TASKS,{self.id:SimpleNamespace(done=lambda:False)}),patch.object(runner,'load_recipe',return_value=recipe):
            with self.assertRaisesRegex(ValueError,'already processing'):runner.assert_can_plan({'id':'same-workflow'},'1')
            runner.assert_can_plan({'id':'different-workflow'},'1')
    def test_recipe_rejects_unrelated_images_and_seedless_workflows(self):
        for change in ('prompt','seed','batch'):
            graph=workflow()
            if change=='prompt':graph['output']['2']['inputs']['text']='unrelated'
            elif change=='seed':graph['output']['3']['inputs']['noise_seed']=1
            else:graph['output']['4']['inputs']['batch_size']=4
            with self.assertRaises(ValueError):runner.validate_recipe(graph,'1')
