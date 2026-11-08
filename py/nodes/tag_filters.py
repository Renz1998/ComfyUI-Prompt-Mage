import json
from .base import BaseNode
from ..dart.tag_filters import PRESETS, build_filter


class PromptMageTagFilters(BaseNode):
    CATEGORY = 'Prompt Mage/DART v3'
    DESCRIPTION = 'Reusable tag exclusion presets. Connect filters to DART Generate and Archmage. Exact tags and known aliases only; no model call. Conflicting protected tags produce an actionable error.'

    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {
            'preset': (PRESETS, {'default': 'Full color', 'tooltip': 'Curated exact tags and bundled vocabulary aliases. Photography excludes drawing media, not every possible non-photo tag.'}),
            'prevent_during_generation': ('BOOLEAN', {'default': True, 'tooltip': 'Ban preset tags while DART generates. Does not remove tags already in its input prompt.'}),
            'clean_final_output': ('BOOLEAN', {'default': True, 'tooltip': 'Remove preset tags from finished DART text and incoming Archmage source tags.'}),
            'extra_banned_tags': ('STRING', {'default': '', 'multiline': True, 'tooltip': 'Additional comma-separated bans during DART generation. Exact tags, not regex.'}),
            'remove_tags': ('STRING', {'default': '', 'multiline': True, 'tooltip': 'Additional comma-separated tags to remove from final tags.'}),
            'protected_tags': ('STRING', {'default': '', 'multiline': True, 'tooltip': 'Tags to retain/append in DART. Not an allow-only whitelist. Conflicts with exclusions are reported instead of silently overriding them.'}),
        }}

    RETURN_TYPES = ('MAGE_TAG_FILTERS', 'STRING', 'STRING', 'STRING', 'STRING')
    RETURN_NAMES = ('filters', 'banned_tags', 'removed_tags', 'protected_tags', 'report')
    FUNCTION = 'build'

    def build(self, preset='Full color', prevent_during_generation=True, clean_final_output=True,
              extra_banned_tags='', remove_tags='', protected_tags=''):
        value = build_filter(preset, prevent_during_generation, clean_final_output,
                             extra_banned_tags, remove_tags, protected_tags)
        return value, ', '.join(value['banned']), ', '.join(value['removed']), ', '.join(value['protected']), json.dumps(value, ensure_ascii=False, indent=2)
