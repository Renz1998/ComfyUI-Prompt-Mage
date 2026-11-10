import test_foundry as fixture
import unittest,sys
from types import SimpleNamespace
from unittest.mock import patch
from dart_plugin.py.nodes.foundry import PromptMageFoundry
from dart_plugin.py.dart import foundry as store,foundry_ai as ai

class Blocker:
    def __init__(self,message):self.message=message

class IdleFoundryTests(unittest.TestCase):
    setUp=fixture.FoundryTests.setUp
    tearDown=fixture.FoundryTests.tearDown
    create=fixture.FoundryTests.create
    plan=fixture.FoundryTests.plan
    approve=fixture.FoundryTests.approve
    def blocked(self,**inputs):
        with patch.dict(sys.modules,{'comfy_execution.graph':SimpleNamespace(ExecutionBlocker=Blocker)}),patch.object(ai,'compose') as compose:
            result=PromptMageFoundry().read(**inputs)
        compose.assert_not_called();self.assertEqual(len(result['result']),8)
        self.assertTrue(all(isinstance(v,Blocker) and v.message is None for v in result['result']))
        self.assertTrue(result['ui']['foundry_notice'][0]);return result
    def test_blank_normal_run_stops_without_assistant_or_disk_record(self):
        self.blocked();self.assertFalse(store.run_path(self.id).exists())
    def test_missing_server_run_is_guided_not_an_exception(self):
        self.blocked(run_id=self.id,attempt_id='b'*32)
    def test_preview_and_stale_attempts_are_not_reused(self):
        self.plan();self.blocked(run_id=self.id)
        store.action(self.id,'approve');a=store.reserve(self.id)
        v=store.read(self.id);v['attempts'][0]['status']='reviewed';v['status']='awaiting_approval';store.write(v)
        self.blocked(run_id=self.id,attempt_id=a['id'])
        self.assertEqual(store.read(self.id)['usage']['renders'],1)
    def test_fresh_reserved_attempt_still_renders(self):
        self.approve();a=store.reserve(self.id)
        with patch.object(ai,'compose',return_value=('test prompt',42)) as compose:
            result=PromptMageFoundry().read(run_id=self.id,attempt_id=a['id'])
        compose.assert_called_once();self.assertEqual(result[:4],('test prompt',1024,1024,42))
