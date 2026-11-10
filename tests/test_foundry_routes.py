from test_regressions import plugin
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from aiohttp import web
from aiohttp.test_utils import TestClient,TestServer
from dart_plugin.py.dart import foundry as store
from dart_plugin.py.dart.foundry_routes import register_foundry_routes


class FoundryRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();routes=web.RouteTableDef();self.queue=SimpleNamespace(get_current_queue=lambda:([],[]))
        self.modules=patch.dict(sys.modules,{'server':SimpleNamespace(PromptServer=SimpleNamespace(instance=SimpleNamespace(routes=routes,prompt_queue=self.queue))),'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name)})
        self.modules.start();register_foundry_routes();app=web.Application();app.add_routes(routes)
        self.client=TestClient(TestServer(app));await self.client.start_server();self.origin=str(self.client.make_url('/')).rstrip('/');self.id='a'*32
    async def asyncTearDown(self):await self.client.close();self.modules.stop();self.temp.cleanup()
    async def call(self,operation,**extra):
        return await self.client.post('/prompt_mage/foundry',json={'operation':operation,'id':self.id,**extra},headers={'Origin':self.origin})
    def create(self):return store.create(self.id,'','single','A traveler','One person','Check map',1,1024,1024,3,3,8)
    async def test_catalog_is_read_only_and_same_origin(self):
        with patch('dart_plugin.py.dart.foundry_ai.generate') as gen:
            r=await self.call('catalog');self.assertEqual(r.status,200);self.assertEqual(len((await r.json())['templates']),5)
        gen.assert_not_called()
        r=await self.client.post('/prompt_mage/foundry',json={'operation':'catalog'},headers={'Origin':'https://untrusted.test'});self.assertEqual(r.status,403)
        r=await self.call('read',id='../private');self.assertEqual(r.status,400)
        r=await self.call('approve',plan={'text':'x'*262144});self.assertEqual(r.status,400)
    async def test_pending_plan_receipt_and_busy_recovery(self):
        r=await self.call('bind_job',job_id='job-1');self.assertEqual(r.status,200)
        value=self.create();self.assertEqual(value['job_id'],'job-1')
        self.queue.get_current_queue=lambda:([(0,'job-1',{},None,None)],[])
        r=await self.call('mark_interrupted');self.assertEqual(r.status,400);self.assertEqual(store.read(self.id)['status'],'planning')
        self.queue.get_current_queue=lambda:([],[])
        r=await self.call('mark_interrupted');self.assertEqual(r.status,200);self.assertEqual((await r.json())['run']['status'],'needs_attention')
    async def test_review_reservation_does_not_render_or_call_model(self):
        value=self.create();value.update(status='needs_attention',attempts=[dict(id='b'*32,image=True,review=None,status='error')]);store.write(value)
        with patch('dart_plugin.py.dart.foundry_ai.generate') as gen:
            r=await self.call('reserve_review',attempt_id='b'*32);self.assertEqual(r.status,200)
            r=await self.call('reserve_review',attempt_id='b'*32);self.assertEqual(r.status,400)
        gen.assert_not_called();self.assertEqual(store.read(self.id)['usage']['renders'],0)
