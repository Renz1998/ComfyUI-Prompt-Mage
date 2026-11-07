"""Beta branch isolation, reference precedence and layout safety."""
from test_regressions import plugin
import json
import sys
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch
import torch

from dart_plugin.py.nodes.archmage import resolve_canvas


class Blocker:
    def __init__(self, value): self.value = value


class ArchmageTests(unittest.TestCase):
    def test_legacy_assistants_deprecated_without_losing_registrations(self):
        for suffix in ('DescribeImage','ImageToText','SceneComposer'):
            node_id = 'DanbooruTagsTransformer' + suffix
            cls = plugin.NODE_CLASS_MAPPINGS[node_id]
            self.assertTrue(cls.DEPRECATED)
            self.assertEqual(cls.CATEGORY, 'Prompt Mage/Deprecated')
            self.assertIn('(Deprecated)', plugin.NODE_DISPLAY_NAME_MAPPINGS[node_id])
            self.assertTrue(cls.INPUT_TYPES()['required'])
        self.assertFalse(getattr(plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerArchmageBeta'],'DEPRECATED',False))

    def test_v3_loader_and_legacy_graph_compatibility(self):
        nodes = plugin.NODE_CLASS_MAPPINGS
        current = nodes['DanbooruTagsTransformerLoaderV3']
        self.assertEqual(current.INPUT_TYPES()['required']['model'][0], ['dart-v3-sft-preview-E (experimental)'])
        self.assertFalse(getattr(current, 'DEPRECATED', False))
        for suffix in ('Loader', 'ComposePrompt', 'ComposePromptV2', 'GetAspectRatio'):
            self.assertTrue(nodes['DanbooruTagsTransformer' + suffix].DEPRECATED)
        self.assertIn('dart-v1-sft', nodes['DanbooruTagsTransformerLoader'].MODEL_NAMES)
        self.assertIn('dart-v2-sft', nodes['DanbooruTagsTransformerLoader'].MODEL_NAMES)
        # Shared tools are version-agnostic and still support v3.
        for suffix in ('Generate', 'GenerationConfig', 'Decode', 'RemoveTagToken'):
            self.assertFalse(getattr(nodes['DanbooruTagsTransformer' + suffix], 'DEPRECATED', False))

    def run_node(self, responses=None, vision=None, **kwargs):
        self.execute = Mock(side_effect=[SimpleNamespace(args=list(text) if isinstance(text, tuple) else [text]) for text in responses or []])
        self.vision = Mock(return_value=vision)
        self.release = Mock()
        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, {
                'comfy_extras.nodes_textgen': SimpleNamespace(TextGenerate=SimpleNamespace(execute=self.execute)),
                'comfy_execution.graph': SimpleNamespace(ExecutionBlocker=Blocker)}))
            stack.enter_context(patch('dart_plugin.py.nodes.archmage.load_local_clip', return_value='encoder'))
            stack.enter_context(patch('dart_plugin.py.nodes.scene_composer.load_local_clip', return_value='encoder'))
            stack.enter_context(patch('dart_plugin.py.nodes.archmage.caption_image', self.vision))
            stack.enter_context(patch('dart_plugin.py.dart.memory.release_assistant_model', self.release))
            return plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerArchmageBeta']().generate(**kwargs)

    def test_canvas_presets_and_limits(self):
        self.assertEqual(resolve_canvas(1024, 1024, '4:5'), (1024, 1280))
        self.assertEqual(resolve_canvas(1024, 1024, '5:4'), (1280, 1024))
        self.assertEqual(resolve_canvas(1024, 1024, '9:16'), (576, 1024))
        self.assertEqual(resolve_canvas(768, 1152), (768, 1152))
        for dims in [(1023, 1024), (0, 1024), (8208, 1024)]:
            with self.assertRaises(ValueError): resolve_canvas(*dims)

    def test_prose_canvas_seed_and_inactive_branches(self):
        result = self.run_node(['An adult woman stands on a stone bridge.'], seed=91, aspect_ratio='3:4')
        payload = json.loads(self.execute.call_args.kwargs['prompt'])
        self.assertIn('768x1024 portrait', payload['instructions'])
        self.assertIn('setting', payload['instructions'])
        self.assertEqual(self.execute.call_count, 1)
        self.assertEqual(result['result'][3:5], (768, 1024))
        self.assertIsInstance(result['result'][2], Blocker)
        self.assertIsInstance(result['result'][5], Blocker)
        self.vision.assert_not_called()

    def test_reference_priority_and_manual_canvas(self):
        image = torch.zeros((1, 96, 64, 3))
        result = self.run_node(vision='A woman holds a red mug.', image=image, concepts='replace the mug with a blue cup',
                               canvas_source='Manual', aspect_ratio='16:9')
        self.execute.assert_not_called()
        self.assertIn('blue cup', self.vision.call_args.args[1])
        self.assertIn('1024x576 landscape', self.vision.call_args.args[1])
        self.assertEqual(result['result'][3:5], (1024, 576))
        self.assertEqual(tuple(result['result'][5].shape), (1, 96, 64, 3))

    def test_reference_canvas_overrides_preset(self):
        result = self.run_node(vision='A red cube.', image=torch.zeros((1, 96, 64, 3)), aspect_ratio='16:9')
        self.assertEqual(result['result'][3:5], (64, 96))
        self.assertEqual(json.loads(result['result'][-1])['source'], 'image')

    def test_reference_does_not_inject_unrequested_mirror_geometry(self):
        image = torch.zeros((1, 96, 64, 3))
        self.run_node(vision='A red circle.', image=image)
        self.assertNotIn('rear cameras', self.vision.call_args.args[1])
        self.run_node(vision='A mirror selfie.', image=image, concepts='Make it a mirror selfie')
        self.assertIn('rear cameras', self.vision.call_args.args[1])

    def test_dart_tags_are_optional_ideas_separate_from_explicit_concepts(self):
        result=self.run_node(['A brown-haired character sits in a cafe.'],source_tags='blue_hair, sitting, cafe, anime',
            concepts='A rainy afternoon',style_preset='Photo · Bright lifestyle')
        payload=json.loads(self.execute.call_args.kwargs['prompt'])
        self.assertEqual(payload['concepts'],'A rainy afternoon')
        self.assertIn('DART candidate concepts',payload['instructions'])
        report=json.loads(result['result'][-1])
        self.assertEqual(report['source_tags']['candidates'],['sitting','cafe'])
        self.assertEqual(self.execute.call_count,1)  # No extra LLM filtering call.

    def test_dart_ideas_reach_vision_as_suggestions_not_reference_replacements(self):
        self.run_node(vision='A red cube.',image=torch.zeros((1,96,64,3)),source_tags='blue_hair, beach, anime')
        directions=self.vision.call_args.args[1]
        self.assertIn('tags alone do not authorize changing',directions)
        self.assertNotIn('Apply these requested concepts/changes',directions)

    def test_rectangular_moss_compiles_pixel_boxes_and_offloads_once(self):
        draft = {'summary': {'meta': [], 'canvas': 'single', 'caption': 'A woman on a bridge.'},
                 'items': [{'label': 'object', 'caption': 'A woman.', 'bbox': [0, 0, 768, 1024]}]}
        result = self.run_node(['A woman on a bridge.', json.dumps({'layout_draft': draft})],
                               output_format='MOSS JSON layout', aspect_ratio='3:4', unload_after_generation=True)
        layout = json.loads(result['result'][2])
        self.assertEqual(layout['items'][0]['bbox'], [-512, -384, 512, 384])
        self.assertEqual(result['result'][0], result['result'][2])
        self.assertEqual(self.execute.call_count, 2)
        self.release.assert_called_once_with('encoder')

    def test_invalid_layout_blocks_json_but_retains_scene_and_report(self):
        result = self.run_node(['A woman at a desk.', '{broken', '{broken'], output_format='MOSS JSON layout')
        self.assertEqual(self.execute.call_count, 3)
        self.assertIsInstance(result['result'][0], Blocker)
        self.assertIsInstance(result['result'][2], Blocker)
        self.assertEqual(result['result'][1], 'A woman at a desk.')
        self.assertEqual(result['result'][-2], 'blocked')
        self.assertIn('two attempts', result['result'][-1])

    def test_root_draft_contract_and_partial_native_metadata(self):
        draft = {'summary': {'caption': 'A red cube.'}, 'items': [
            {'label': 'object', 'caption': 'A red cube.', 'bbox': [0, 0, 1024, 1024]}]}
        result = self.run_node(['A red cube.', json.dumps(draft)], output_format='MOSS JSON layout')
        self.assertEqual(json.loads(result['result'][2])['items'][0]['bbox'], [-512, -512, 512, 512])
        draft['bbox_format'] = 'yxyx'
        result = self.run_node(['A red cube.', json.dumps(draft), json.dumps(draft)], output_format='MOSS JSON layout')
        self.assertEqual(result['result'][-2], 'blocked')

    def test_connected_dimensions_override_aspect_and_full_prose_survives_layout(self):
        prose = 'A red-cloaked mage holds a phone toward a hotel mirror. Sharp focus throughout, no blur.'
        draft = {'summary': {'caption': 'A woman.'}, 'items': [
            {'label': 'object', 'caption': 'A mage in a red cloak.', 'bbox': [0, 0, 1568, 2368]}]}
        result = self.run_node([prose, json.dumps(draft)], output_format='MOSS JSON layout',
            width=1568, height=2368, aspect_ratio='1:1', unique_id='42',
            prompt={'42': {'inputs': {'width': ['8', 0], 'height': ['8', 1]}}})
        layout = json.loads(result['result'][2])
        self.assertEqual(layout['summary']['caption'], prose)
        self.assertEqual(result['result'][3:5], (1568, 2368))
        self.assertEqual(layout['items'][0]['bbox'], [-1184, -784, 1184, 784])
        self.assertEqual(json.loads(result['result'][-1])['layout']['box_union_fraction'], 1)

    def test_runtime_failure_propagates_and_offloads(self):
        with patch('dart_plugin.py.nodes.scene_composer.PromptMageSceneComposer.generate', side_effect=RuntimeError('out of memory')):
            with self.assertRaisesRegex(RuntimeError, 'out of memory'):
                self.run_node(unload_after_generation=True)
        self.release.assert_called_once_with('encoder')

    def test_thinking_reaches_both_stages_without_reasoning_in_outputs(self):
        draft = {'summary': {'caption': 'A red cube.'}, 'items': [
            {'label': 'object', 'caption': 'A red cube.', 'bbox': [0, 0, 1024, 1024]}]}
        result = self.run_node([('A red cube.', 'private-stage-one-marker'),
                                (json.dumps(draft), 'private-stage-two-marker')],
                               output_format='MOSS JSON layout', thinking=True, max_tokens=8192)
        self.assertTrue(all(call.kwargs['thinking'] for call in self.execute.call_args_list))
        self.assertTrue(all(call.kwargs['max_length'] == 8192 for call in self.execute.call_args_list))
        self.assertNotIn('private-stage', json.dumps(result['ui']))
        report = json.loads(result['result'][-1])
        self.assertTrue(report['scene']['generation']['thinking_output_detected'])
        self.assertTrue(report['layout_generation']['thinking_output_detected'])

    def test_thinking_budget_blocks_without_retrying_or_leaking(self):
        result = self.run_node([('', 'unfinished-reasoning-marker')], thinking=True, unload_after_generation=True)
        self.assertEqual(self.execute.call_count, 1)
        self.assertEqual(result['result'][-2], 'blocked')
        self.assertIn('8192', result['result'][-1])
        self.assertNotIn('unfinished-reasoning-marker', result['result'][-1])
        self.assertIsInstance(result['result'][0], Blocker)
        self.release.assert_called_once_with('encoder')

    def test_layout_thinking_budget_preserves_prose(self):
        result = self.run_node(['A red cube.', ('', 'unfinished')], thinking=True, output_format='MOSS JSON layout')
        self.assertEqual(self.execute.call_count, 2)
        self.assertEqual(result['result'][1], 'A red cube.')
        self.assertEqual(result['result'][-2], 'blocked')
        self.assertNotIn('after two attempts', result['result'][-1])

    def test_reference_thinking_is_forwarded_and_defaults_remain_off(self):
        self.run_node(vision='A red cube.', image=torch.zeros((1, 96, 64, 3)), thinking=True)
        self.assertTrue(self.vision.call_args.kwargs['thinking'])
        self.run_node(['A red cube.'])
        self.assertFalse(self.execute.call_args.kwargs['thinking'])

    def test_unsupported_thinking_warns_and_retains_final_answer(self):
        result = self.run_node(['A red cube.'], thinking=True)
        self.assertEqual(result['result'][0], 'A red cube.')
        self.assertEqual(result['result'][-2], 'warning')
        self.assertIn('thinking is unconfirmed', result['result'][-1])

    def test_snapshot_style_replaces_conflicting_random_directions(self):
        result = self.run_node(['A casual phone photograph.'], style_preset='Photo · Amateur Instagram', seed=4)
        payload = json.loads(self.execute.call_args.kwargs['prompt'])
        self.assertIn('ordinary personal Instagram photo', payload['instructions'])
        self.assertNotIn('lighting', payload['creative_directions'])
        self.assertNotIn('framing', payload['creative_directions'])
        self.assertNotIn('floating archive', payload['creative_directions']['setting'])
        self.assertTrue(json.loads(result['result'][-1])['style']['applied'])

    def test_reference_style_requires_explicit_restyle(self):
        args = dict(vision='A sketch of a cube.', image=torch.zeros((1, 96, 64, 3)), style_preset='Anime · Sci-fi')
        result = self.run_node(**args)
        self.assertNotIn('cel-shaded', self.vision.call_args.args[1])
        self.assertFalse(json.loads(result['result'][-1])['style']['applied'])
        self.run_node(**args, reference_style='Apply selected style')
        self.assertIn('cel-shaded', self.vision.call_args.args[1])

    def test_style_reaches_layout_stage_and_user_instructions_remain(self):
        draft = {'summary': {'caption': 'An anime character.'}, 'items': [
            {'label': 'object', 'caption': 'An anime character.', 'bbox': [0, 0, 1024, 1024]}]}
        self.run_node(['An anime character.', json.dumps(draft)], output_format='MOSS JSON layout',
                      concepts='one robot', instructions='Use green accents.', style_preset='Anime · Sci-fi')
        first, second = self.execute.call_args_list
        self.assertIn('Use green accents.', first.kwargs['prompt'])
        self.assertIn('one robot', first.kwargs['prompt'])
        self.assertIn('science-fiction anime', second.kwargs['system_prompt'])

    def test_random_style_is_seeded_and_custom_validated(self):
        from dart_plugin.py.dart.style_presets import resolve_style, STYLE_OPTIONS, STYLES
        self.assertEqual(len(STYLES), 31)
        self.assertEqual(resolve_style('Random preset', '', 17), resolve_style('Random preset', '', 17))
        self.assertGreater(len({resolve_style('Random preset', '', seed)[0] for seed in range(20)}), 5)
        self.assertIn('pastel ink', resolve_style('Custom', 'pastel ink', 1)[1])
        for selection, notes in [('Custom', ''), ('unknown', '')]:
            with self.assertRaises(ValueError): resolve_style(selection, notes, 0)
        self.assertEqual(resolve_style(STYLE_OPTIONS[0], '', 0)[1], '')


if __name__ == '__main__': unittest.main()
