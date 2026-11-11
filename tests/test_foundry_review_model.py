import test_foundry as fixture
import unittest,json
from types import SimpleNamespace
from unittest.mock import patch
import torch
from dart_plugin.py.dart import foundry as store,foundry_ai as ai


class ReviewModelTests(unittest.TestCase):
    setUp=fixture.FoundryTests.setUp
    tearDown=fixture.FoundryTests.tearDown
    create=fixture.FoundryTests.create
    plan=fixture.FoundryTests.plan
    approve=fixture.FoundryTests.approve
    review_json=staticmethod(fixture.FoundryTests.review_json)

    def test_review_profile_is_frozen_separately_and_old_runs_fall_back(self):
        profile=next(p for p in store.REVIEWERS if p.startswith('OpenAI · '))
        value=self.create(assistant_profile=store.ASSISTANTS[1],review_profile=profile)
        self.assertEqual(value['config']['assistant_backend'],'DeepSeek API')
        self.assertEqual(value['review_config']['assistant_backend'],'OpenAI API')
        self.assertEqual(value['review_config']['openai_model'],profile.removeprefix('OpenAI · '))
        value['review_config']['thinking']=True
        self.assertFalse(value['config'].get('thinking',False))
        self.assertEqual(store.public(value)['review_assistant'],'OpenAI API')
        del value['review_config']
        self.assertEqual(store.reviewer_config(value),value['config'])
        with self.assertRaises(ValueError):store.review_settings('unknown reviewer',value['config'])

    def test_review_uses_selected_provider_views_and_records_reviewer(self):
        value=self.approve();profile=next(p for p in store.REVIEWERS if p.startswith('OpenAI · '))
        value.update(review_profile=profile,review_config=store.review_settings(profile,value['config']));store.write(value)
        attempt=store.reserve(self.id)
        value=store.read(self.id);value['status']='rendering';value['attempts'][-1]['status']='rendering';store.write(value)
        with patch.object(ai,'generate',return_value=self.review_json()) as generate:
            value=ai.review(self.id,attempt['id'],torch.zeros(1,16,16,3),clip='shared local encoder')
        self.assertEqual(generate.call_args.kwargs['config']['assistant_backend'],'OpenAI API')
        self.assertIsInstance(generate.call_args.args[4],list)
        self.assertEqual(value['attempts'][-1]['review']['reviewer_backend'],'OpenAI API')
        self.assertEqual(value['config']['assistant_backend'],'Local Qwen')

    def test_review_generation_uses_shared_budget_and_remote_encoder(self):
        value=self.create();cfg=store.review_settings(next(p for p in store.REVIEWERS if p.startswith('OpenAI · ')),value['config'])
        with patch.object(ai,'encoder_for',return_value='remote') as encoder,patch.object(ai,'execute_generation',return_value=SimpleNamespace(args=['Review result'])) as execute:
            ai.generate(value,'Inspector','Review',image=['image'],config=cfg)
        encoder.assert_called_once_with(cfg,None)
        self.assertEqual(execute.call_args.args[0],'remote')
        self.assertEqual(execute.call_args.kwargs['image'],['image'])
        self.assertEqual(store.read(self.id)['usage']['calls'],1)

    def test_missing_separate_review_key_fails_before_spending(self):
        value=self.create(review_profile=next(p for p in store.REVIEWERS if p.startswith('OpenAI · ')))
        with patch.object(ai,'encoder_for',side_effect=ValueError('Add reviewer key')),patch.object(ai,'generate') as generate:
            with self.assertRaisesRegex(ValueError,'Add reviewer key'):ai.plan(value)
        generate.assert_not_called()
        self.assertEqual(store.read(self.id)['usage']['calls'],0)
