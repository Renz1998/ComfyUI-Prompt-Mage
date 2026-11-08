from test_regressions import plugin
import unittest
from dart_plugin.py.dart.tag_filters import build_filter, clean_text, dart_lists


class TagFilterTests(unittest.TestCase):
    def test_full_color_exact_aliases_preserve_black_attributes(self):
        recipe = build_filter('Full color')
        self.assertEqual(clean_text('monochrome, black_hair, black dress, blue eyes', recipe),
                         'black_hair, black dress, blue eyes')
        self.assertIn('monochrome', recipe['banned'])

    def test_independent_switches_and_custom_lists(self):
        r = build_filter('Full color', False, True, 'watermark', 'signature')
        self.assertNotIn('monochrome', r['banned'])
        self.assertIn('watermark', r['banned'])
        self.assertIn('monochrome', r['removed'])
        self.assertEqual(clean_text('signature, red hair', r), 'red hair')

    def test_conflicts_fail_instead_of_silent_keep_override(self):
        with self.assertRaisesRegex(ValueError, 'conflict'):
            build_filter('Full color', protected='monochrome')
        with self.assertRaisesRegex(ValueError, 'conflict'):
            dart_lists(build_filter('Full color'), '', '', 'monochrome')
        r = build_filter('Full color', protected='black hair')
        self.assertIn('black hair', dart_lists(r, '', '', '')[2])

    def test_dart_filters_before_generation_and_after_decode(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        model = SimpleNamespace(generate=Mock(return_value=[[4, 5]]))
        tokenizer = SimpleNamespace(tokenizer=object(), decode=Mock(return_value='monochrome, black hair'))
        with patch('dart_plugin.py.nodes.generate.remove_tag_sequences', return_value=[5]):
            output = plugin.NODE_CLASS_MAPPINGS['DanbooruTagsTransformerGenerate']().generate(
                model, tokenizer, '', 1, animagine_order=False, filters=build_filter('Full color'))
        self.assertIn('monochrome', model.generate.call_args.args[4])
        self.assertEqual(output, ('black hair',))
