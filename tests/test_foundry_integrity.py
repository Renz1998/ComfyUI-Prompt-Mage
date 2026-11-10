import test_foundry as fixture
from dart_plugin.py.dart import foundry as store,foundry_ai as ai
from dart_plugin.py.dart.foundry_review import assessment
import json,torch,unittest

class PhysicalReviewTests(unittest.TestCase):
    setUp=fixture.FoundryTests.setUp
    tearDown=fixture.FoundryTests.tearDown
    create=fixture.FoundryTests.create
    plan=fixture.FoundryTests.plan
    approve=fixture.FoundryTests.approve
    review_json=staticmethod(fixture.FoundryTests.review_json)
    def test_prompt_match_cannot_hide_broken_geometry(self):
        r=ai.validate_review(json.loads(self.review_json()),['Map','Person'],require_scores=True,require_integrity=True)
        r['visual_integrity']['spatial'].update(score=92,status='pass',severity='major',evidence='Torso intersects solid railing.')
        for policy in ('Relaxed','Balanced','Strict'):
            result=assessment(r,['Map','Person'],policy)
            self.assertFalse(result['acceptable']);self.assertFalse(result['integrity_passed']);self.assertIn('railing',result['decision_reason'])
    def test_uncertain_anatomy_never_auto_passes_from_high_match(self):
        r=ai.validate_review(json.loads(self.review_json()),['Map','Person'],require_integrity=True)
        r['visual_integrity']['anatomy'].update(status='uncertain',score=95,severity='minor')
        self.assertFalse(assessment(r,['Map','Person'],'Relaxed')['acceptable'])
    def test_new_review_requires_all_physical_categories(self):
        r=json.loads(self.review_json());del r['visual_integrity']['clothing']
        with self.assertRaises(ValueError):ai.validate_review(r,['Map','Person'],require_integrity=True)
        del r['visual_integrity']
        with self.assertRaises(ValueError):ai.validate_review(r,['Map','Person'],require_integrity=True)
    def test_absent_people_are_not_anatomy_defects(self):
        r=json.loads(self.review_json());r['visual_integrity']['anatomy']={'applicable':False,'evidence':'Objects-only scene.'}
        result=ai.validate_review(r,['Map','Person'],require_integrity=True)
        self.assertTrue(assessment(result,['Map','Person'])['integrity_passed'])
    def test_review_detail_views_keep_full_context_and_local_single_image(self):
        image=torch.zeros(1,500,400,3)
        images,labels=ai.review_views(image,'DeepSeek API')
        self.assertEqual(len(images),3);self.assertEqual(len(labels),3)
        self.assertEqual(tuple(images[0].shape),tuple(image.shape))
        local,_=ai.review_views(image,'Local Qwen');self.assertIsInstance(local,torch.Tensor)
    def test_friendly_output_folder_and_clean_accepted_collection(self):
        v=self.approve();self.assertEqual(v['output_dir_name'],'trip')
        attempt=store.reserve(self.id);prefix=store.output_prefix(store.read(self.id),attempt['id'])
        self.assertEqual(prefix,'PromptMage-Foundry/trip/attempts/01-inn-try-01')
        ai.save_image(self.id,attempt['id'],torch.zeros(1,16,16,3))
        v=store.read(self.id);v['status']='awaiting_approval';v['attempts'][0]['review']={'verdict':'pass'};store.write(v)
        v=store.action(self.id,'accept',{'attempt_id':attempt['id']})
        path=store.collection_path(v);self.assertTrue((path/'accepted/01-inn.png').exists())
        self.assertEqual(json.loads((path/'collection.json').read_text())['images'][0]['title'],'Inn')
    def test_folder_names_are_safe_customizable_and_unique(self):
        self.plan();v=store.action(self.id,'approve',{'output_folder':'My IG collection'})
        self.assertEqual(v['output_dir_name'],'my-ig-collection')
        other={**v,'id':'b'*32};other.pop('output_dir_name');store.claim_output_folder(other)
        self.assertEqual(other['output_dir_name'],'my-ig-collection-2')
        for name in ('../escape','C:\\escape','..','x/y'):
            with self.assertRaises(ValueError):store.folder_label(name,custom=True)
        self.assertEqual(store.folder_label('CON'),'project-con')
        self.assertNotIn('/',store.folder_label('Sunset / pool'))
    def test_legacy_output_paths_stay_unchanged(self):
        self.approve();a=store.reserve(self.id);v=store.read(self.id);v.pop('output_dir_name')
        self.assertEqual(store.output_prefix(v,a['id']),'PromptMage-Foundry/'+self.id+'/01-'+a['id'][:8])
    def test_approve_rejects_invalid_folder_before_allocating(self):
        self.plan()
        for invalid in ([], 'a'*101, '../escape'):
            with self.assertRaises(ValueError):store.action(self.id,'approve',{'output_folder':invalid})
        self.assertFalse(store.output_root().exists())

    def test_physical_setting_is_independent_of_prompt_tolerance(self):
        r=ai.validate_review(json.loads(self.review_json()),['Map','Person'],require_integrity=True)
        r['visual_integrity']['anatomy'].update(score=78,status='partial',severity='minor')
        self.assertTrue(assessment(r,['Map','Person'],'Balanced','Relaxed')['acceptable'])
        self.assertFalse(assessment(r,['Map','Person'],'Relaxed','Strict')['acceptable'])
    def test_export_prefers_native_png_and_rejects_foreign_collection(self):
        v=self.approve();a=store.reserve(self.id);v=store.read(self.id)
        native=store.output_root().parent/(store.output_prefix(v,a['id'])+'_00001_.png')
        native.parent.mkdir(parents=True);native.write_bytes(b'native metadata fixture')
        store.export_accepted(v,v['attempts'][0])
        self.assertEqual((store.collection_path(v)/v['attempts'][0]['accepted_file']).read_bytes(),b'native metadata fixture')
        v['id']='b'*32
        with self.assertRaisesRegex(ValueError,'another run'):store.collection_path(v)
