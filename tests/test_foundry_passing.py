import test_foundry as fixture
import unittest,json
from dart_plugin.py.dart import foundry_ai as ai,foundry as store
from dart_plugin.py.dart.foundry_review import assessment

class PassingScoreTests(unittest.TestCase):
    def test_tolerable_imperfections_can_pass_recommended_score(self):
        r=json.loads(fixture.FoundryTests.review_json());r['quality_score']=72
        for key,score in zip(('anatomy','spatial','clothing','lighting'),(70,68,74,84)):r['visual_integrity'][key].update(score=score,status='partial',severity='minor')
        r=ai.validate_review(r,['Map','Person'],require_integrity=True)
        result=assessment(r,['Map','Person'],'Balanced','Balanced',80)
        self.assertEqual(result['overall_score'],80);self.assertTrue(result['acceptable'])
        self.assertFalse(assessment(r,['Map','Person'],'Balanced','Balanced',90)['acceptable'])
    def test_major_defects_fail_even_with_lower_passing_score(self):
        r=ai.validate_review(json.loads(fixture.FoundryTests.review_json()),['Map','Person'],require_integrity=True)
        r['visual_integrity']['anatomy'].update(severity='major',score=95)
        self.assertFalse(assessment(r,['Map','Person'],'Relaxed','Relaxed',50)['acceptable'])
    def test_visible_fail_and_missing_essentials_still_block(self):
        r=ai.validate_review(json.loads(fixture.FoundryTests.review_json()),['Map','Person'],require_integrity=True)
        r['visual_integrity']['spatial'].update(status='fail',score=95)
        self.assertFalse(assessment(r,['Map','Person'],'Balanced','Balanced',50)['acceptable'])
