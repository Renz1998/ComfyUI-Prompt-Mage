from test_regressions import plugin
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from dart_plugin.py.nodes.resolution import resolution
from dart_plugin.py.dart.memory import offload_after, prepare_assistant_memory
from dart_plugin.py.dart.moss import compile_layout, layout_diagnostics
from dart_plugin.py.dart.local_assistant import select_model
from dart_plugin.py.dart.local_assistant import load_local_clip


class CanvasMemoryTests(unittest.TestCase):
    def test_resolution_rounds_and_preserves_portrait_shape(self):
        self.assertEqual(resolution(3.7, '2:3', 32), (1568, 2368))
        for ratio in ('1:1', '16:9', '9:16', '4:5', '5:4'):
            width, height = resolution(1, ratio, 16)
            self.assertEqual(width % 16, 0)
            self.assertEqual(height % 16, 0)
            self.assertLess(abs(width * height - 1_000_000), 40_000)
        self.assertEqual(resolution(1, 'Custom', 32, 1024, 1000), (1024, 992))
        for budget in (float('nan'), float('inf'), -1, 100):
            with self.assertRaises(ValueError): resolution(budget)

    def test_layout_uses_full_rectangular_canvas_without_double_counting_overlap(self):
        layout = compile_layout({'summary': {'caption': 'A red mug on a desk.'}, 'items': [
            {'label': 'object', 'caption': 'Desk.', 'bbox': [0, 0, 1568, 2368]},
            {'label': 'object', 'caption': 'Mug.', 'bbox': [100, 100, 600, 900]}]}, 1568, 2368, draft=True)
        self.assertEqual(layout['items'][0]['bbox'], [-1184, -784, 1184, 784])
        self.assertEqual(layout_diagnostics(layout, 1568, 2368)['box_union_fraction'], 1)

    def test_auto_memory_reserves_headroom_and_keeps_shared_encoder(self):
        patcher = SimpleNamespace(load_device=SimpleNamespace(type='cuda'), clone_base_uuid='shared',
                                  model_size=lambda: 8 * 1024**3, loaded_size=lambda: 3 * 1024**3)
        own = SimpleNamespace(model=patcher)
        other = SimpleNamespace(model=SimpleNamespace(clone_base_uuid='diffusion'))
        management = SimpleNamespace(current_loaded_models=[own, other], free_memory=Mock(), soft_empty_cache=Mock())
        with patch.dict(sys.modules, {'comfy': SimpleNamespace(model_management=management), 'comfy.model_management': management}):
            prepare_assistant_memory(SimpleNamespace(patcher=patcher))
        management.free_memory.assert_called_once_with(7 * 1024**3, patcher.load_device, keep_loaded=[own])

    def test_interrupt_cleanup_even_when_normal_unload_is_disabled(self):
        with patch('dart_plugin.py.dart.memory.release_assistant_model') as release:
            with self.assertRaises(KeyboardInterrupt), offload_after('clip', False, release_on_error=True):
                raise KeyboardInterrupt()
            release.assert_called_once_with('clip')

    def test_smallest_installed_model_and_gender_compatibility(self):
        self.assertIn('2b', select_model(['qwen3vl_4b_fp8.safetensors', 'qwen3.5_2b_bf16.safetensors']))
        cls = plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerAppearanceOverrides']
        self.assertEqual(cls.INPUT_TYPES()['required']['gender'][1]['default'], 'Female')
        self.assertEqual(cls().build(gender='Male')['result'][0]['traits']['gender'], 'man')
        self.assertNotIn('gender', cls().build()['result'][0]['traits'])

    def test_automatic_download_only_when_no_model_or_clip_is_available(self):
        loader = Mock(return_value=SimpleNamespace(load_clip=Mock(return_value=['loaded'])))
        with patch.dict(sys.modules, {'nodes': SimpleNamespace(CLIPLoader=loader)}), \
             patch('dart_plugin.py.dart.local_assistant.local_models', return_value=[]) as available, \
             patch('dart_plugin.py.dart.local_assistant.download_fallback', return_value='fallback.safetensors') as download:
            self.assertEqual(load_local_clip(clip='shared', auto_download=True), 'shared')
            available.assert_not_called(); download.assert_not_called()
            with self.assertRaises(ValueError): load_local_clip()
            download.assert_not_called()
            self.assertEqual(load_local_clip(auto_download=True), 'loaded')
            download.assert_called_once()
            available.return_value = ['qwen3vl_4b_int8.safetensors']
            load_local_clip(auto_download=True)
            self.assertEqual(download.call_count, 1)


if __name__ == '__main__': unittest.main()
