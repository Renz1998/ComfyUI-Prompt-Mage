import test_foundry as helpers
import copy
import json
import unittest
from unittest.mock import patch
import torch
from dart_plugin.py.dart import foundry as store,foundry_ai as ai
from dart_plugin.py.dart.foundry_review import assessment


class ReviewFormatTests(unittest.TestCase):
    def value(self,status='pass'):
        return dict(checks=[dict(id='C1 ',status=status,score='85/100',evidence='Requested detail is visible.')],quality_score='88%',major_defect='false',summary='Usable image.')
    def test_casing_aliases_and_partial_matches(self):
        for raw,expected in [(' PASS ','pass'),('Passed','pass'),('partially met','partial'),('mostly-pass','partial'),('not met','fail'),('not visible','uncertain')]:
            result=ai.validate_review(self.value(raw),['Detail'],True)
            self.assertEqual(result['checks'][0]['id'],'c1');self.assertEqual(result['checks'][0]['status'],expected)
            self.assertEqual(result['quality_score'],88);self.assertFalse(result['major_defect'])
    def test_partial_matches_follow_tolerance_but_do_not_satisfy_must_haves(self):
        result=ai.validate_review(self.value('partial'),['Detail'],True)
        self.assertTrue(assessment(result,['Detail'],'Balanced')['acceptable'])
        self.assertFalse(assessment(result,['Detail'],'Strict')['acceptable'])
        self.assertFalse(assessment(result,['! Detail'],'Relaxed')['acceptable'])
    def test_unknown_status_cannot_become_a_high_scoring_pass(self):
        value=self.value('invented status');value['checks'][0]['score']=100
        with self.assertRaisesRegex(ValueError,'unrecognized'):ai.validate_review(value,['Detail'],True)
        parsed=ai.validate_review(value,['Detail']);self.assertEqual(parsed['checks'][0]['status'],'uncertain')
        self.assertFalse(assessment(parsed,['Detail'])['acceptable'])
    def test_invalid_scores_and_ambiguous_flags_are_still_rejected(self):
        for score in ('nan','Infinity','101%','-2',True):
            value=self.value();value['checks'][0]['score']=score
            with self.assertRaises(ValueError):ai.validate_review(value,['Detail'],True)
        value=self.value();value['major_defect']='maybe'
        with self.assertRaises(ValueError):ai.validate_review(value,['Detail'],True)
    def test_missing_or_duplicate_checks_are_not_invented(self):
        value=self.value();value['checks']*=2
        with self.assertRaises(ValueError):ai.validate_review(value,['Detail'],True)
    def test_long_but_valid_explanations_are_bounded_not_rejected(self):
        value=self.value();value['checks'][0]['evidence']='Visible detail. '*100;value['summary']='Scene description. '*100
        result=ai.validate_review(value,['Detail'],True);self.assertEqual(len(result['checks'][0]['evidence']),600);self.assertEqual(len(result['summary']),1200)


class SavedReviewTests(unittest.TestCase):
    setUp=helpers.FoundryTests.setUp
    tearDown=helpers.FoundryTests.tearDown
    create=helpers.FoundryTests.create
    plan=helpers.FoundryTests.plan
    approve=helpers.FoundryTests.approve
    composed=helpers.FoundryTests.composed
    review_json=staticmethod(helpers.FoundryTests.review_json)
    def test_raw_response_is_saved_before_validation_and_reused_without_an_api_call(self):
        attempt,_,_=self.composed();image=torch.zeros(1,16,16,3)
        with patch.object(ai,'generate',return_value=self.review_json()),patch.object(ai,'validate_review',side_effect=ValueError('old strict parser')):
            with self.assertRaisesRegex(ValueError,'Image saved'):ai.review(self.id,attempt['id'],image)
        self.assertTrue(ai.review_response_path(self.id,attempt['id']).exists())
        before=store.read(self.id)['usage'].copy()
        with patch.object(ai,'generate') as generate:result=ai.review(self.id,attempt['id'])
        generate.assert_not_called();self.assertEqual(result['status'],'awaiting_approval');self.assertEqual(result['usage'],before)
    def test_unusable_cached_response_gets_only_one_fresh_review_not_a_new_image(self):
        attempt,_,_=self.composed()
        with patch.object(ai,'generate',return_value='invalid JSON'):
            with self.assertRaises(ValueError):ai.review(self.id,attempt['id'],torch.zeros(1,16,16,3))
        with patch.object(ai,'generate',return_value=self.review_json()) as generate:result=ai.review(self.id,attempt['id'])
        generate.assert_called_once();self.assertEqual(result['usage']['renders'],1)
    def test_saved_reply_is_bound_to_the_actual_image_hash(self):
        attempt,_,_=self.composed();ai.save_image(self.id,attempt['id'],torch.zeros(1,16,16,3));ai.save_review_response(self.id,attempt['id'],self.review_json())
        self.assertIsNotNone(ai.cached_review_response(self.id,attempt['id']))
        ai.save_image(self.id,attempt['id'],torch.ones(1,16,16,3));self.assertIsNone(ai.cached_review_response(self.id,attempt['id']))


