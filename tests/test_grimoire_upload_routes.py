from test_regressions import plugin
import sys
import io
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from aiohttp import web, FormData
from aiohttp.test_utils import TestClient, TestServer
from dart_plugin.py.dart.grimoire_routes import register_grimoire_routes


class UploadRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory()
        routes=web.RouteTableDef()
        self.modules=patch.dict(sys.modules,{'server':SimpleNamespace(PromptServer=SimpleNamespace(instance=SimpleNamespace(routes=routes))),
            'folder_paths':SimpleNamespace(get_user_directory=lambda:self.temp.name)})
        self.modules.start();register_grimoire_routes()
        app=web.Application(client_max_size=17*1024*1024);app.add_routes(routes)
        self.client=TestClient(TestServer(app));await self.client.start_server()
        self.origin=str(self.client.make_url('/')).rstrip('/')

    async def asyncTearDown(self):
        await self.client.close();self.modules.stop();self.temp.cleanup()

    async def test_browser_upload_read_and_origin_checks(self):
        form=FormData();form.add_field('file',b'Green cloak, brown boots.',filename='outfit.md')
        response=await self.client.post('/prompt_mage/grimoire/attachment',data=form,headers={'Origin':self.origin})
        self.assertEqual(response.status,200);value=await response.json()
        self.assertEqual(value['kind'],'text');self.assertNotIn('text',value)
        response=await self.client.post('/prompt_mage/grimoire/attachment/read',json={'id':value['id']},headers={'Origin':self.origin})
        self.assertEqual(response.status,200);self.assertIn('brown boots',(await response.json())['excerpt'])
        response=await self.client.post('/prompt_mage/grimoire/attachment/read',json={'id':value['id']},headers={'Origin':'https://untrusted.example'})
        self.assertEqual(response.status,403)
        response=await self.client.post('/prompt_mage/grimoire/attachment/read',json={'id':'../../private'},headers={'Origin':self.origin})
        self.assertEqual(response.status,400)

    async def test_unsupported_and_oversized_uploads_fail_without_storage(self):
        for name,raw in [('script.exe',b'not executable'),('large.txt',b'x'*(16*1024*1024+1))]:
            form=FormData();form.add_field('file',io.BytesIO(raw),filename=name)
            response=await self.client.post('/prompt_mage/grimoire/attachment',data=form,headers={'Origin':self.origin})
            self.assertEqual(response.status,400)
            self.assertIn('error',await response.json())
