from .py.nodes.loader import DanbooruTagsTransformerLoader, PromptMageDartV3Loader
from .py.nodes.generate import DanbooruTagsTransformerGenerate
from .py.nodes.prompt import DanbooruTagsTransformerComposePrompt
from .py.nodes.prompt_v2 import (
    DanbooruTagsTransformerComposePromptV2,
    DanbooruTagsTransformerGetAspectRatio,
)
from .py.nodes.config import DanbooruTagsTransformerGenerationConfig
from .py.nodes.advanced.generate import DanbooruTagsTransformerGenerateAdvanced
from .py.nodes.advanced.decode import (
    DanbooruTagsTransformerDecode,
    DanbooruTagsTransformerDecodeBySplitedParts,
)
from .py.nodes.advanced.token_ids import (
    DanbooruTagsTransformerRearrangedByAnimagine,
    DanbooruTagsTransformerRemoveTagToken,
)
from .py.nodes.ban_tags import DanbooruTagsTransformerBanTagsFromRegex
from .py.nodes.prompt_v3 import DanbooruTagsTransformerComposePromptV3
from .py.nodes.assistant import DanbooruTagsTransformerDescribeImage
from .py.nodes.vision import DanbooruTagsTransformerImageToText
from .py.nodes.help import attach_help
from .py.nodes.appearance import DanbooruTagsTransformerAppearanceOverrides
from .py.nodes.image_batch import DanbooruTagsTransformerImageBatchSelector, DanbooruTagsTransformerImageBatchUpload

NODE_CLASS_MAPPINGS = {
    "DanbooruTagsTransformerLoaderV3": PromptMageDartV3Loader,
    "DanbooruTagsTransformerImageBatchUpload": DanbooruTagsTransformerImageBatchUpload,
    "DanbooruTagsTransformerImageBatchSelector": DanbooruTagsTransformerImageBatchSelector,
    "DanbooruTagsTransformerAppearanceOverrides": DanbooruTagsTransformerAppearanceOverrides,
    "DanbooruTagsTransformerImageToText": DanbooruTagsTransformerImageToText,
    "DanbooruTagsTransformerComposePromptV3": DanbooruTagsTransformerComposePromptV3,
    "DanbooruTagsTransformerDescribeImage": DanbooruTagsTransformerDescribeImage,
    "DanbooruTagsTransformerLoader": DanbooruTagsTransformerLoader,
    "DanbooruTagsTransformerGenerate": DanbooruTagsTransformerGenerate,
    "DanbooruTagsTransformerComposePrompt": DanbooruTagsTransformerComposePrompt,
    "DanbooruTagsTransformerComposePromptV2": DanbooruTagsTransformerComposePromptV2,
    "DanbooruTagsTransformerGetAspectRatio": DanbooruTagsTransformerGetAspectRatio,
    "DanbooruTagsTransformerGenerationConfig": DanbooruTagsTransformerGenerationConfig,
    "DanbooruTagsTransformerBanTagsFromRegex": DanbooruTagsTransformerBanTagsFromRegex,
    # Advanced
    "DanbooruTagsTransformerGenerateAdvanced": DanbooruTagsTransformerGenerateAdvanced,
    "DanbooruTagsTransformerDecode": DanbooruTagsTransformerDecode,
    "DanbooruTagsTransformerDecodeBySplitedParts": DanbooruTagsTransformerDecodeBySplitedParts,
    "DanbooruTagsTransformerRearrangedByAnimagine": DanbooruTagsTransformerRearrangedByAnimagine,
    "DanbooruTagsTransformerRemoveTagToken": DanbooruTagsTransformerRemoveTagToken,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DanbooruTagsTransformerLoaderV3": "Prompt Mage · DART v3 Load",
    "DanbooruTagsTransformerImageBatchUpload": "Prompt Mage · Upload Images",
    "DanbooruTagsTransformerImageBatchSelector": "Prompt Mage · Server Folder (Advanced)",
    "DanbooruTagsTransformerAppearanceOverrides": "Prompt Mage · Appearance Overrides",
    "DanbooruTagsTransformerImageToText": "Prompt Mage · Image to Text",
    "DanbooruTagsTransformerComposePromptV3": "Prompt Mage · DART Compose Prompt V3 (Experimental)",
    "DanbooruTagsTransformerDescribeImage": "Prompt Mage · Text Assistant",
    "DanbooruTagsTransformerLoader": "Prompt Mage · DART Load",
    "DanbooruTagsTransformerGenerate": "Prompt Mage · DART Generate",
    "DanbooruTagsTransformerComposePrompt": "Prompt Mage · DART Compose Prompt",
    "DanbooruTagsTransformerComposePromptV2": "Prompt Mage · DART Compose Prompt V2",
    "DanbooruTagsTransformerGetAspectRatio": "Prompt Mage · DART Get Aspect Ratio",
    "DanbooruTagsTransformerGenerationConfig": "Prompt Mage · DART Generation Config",
    "DanbooruTagsTransformerBanTagsFromRegex": "Prompt Mage · DART Ban Tags From Regex",
    # Advanced
    "DanbooruTagsTransformerGenerateAdvanced": "Prompt Mage · DART Generate(Advanced)",
    "DanbooruTagsTransformerDecode": "Prompt Mage · DART Decode",
    "DanbooruTagsTransformerDecodeBySplitedParts": "Prompt Mage · DART Decode By Splited Parts",
    "DanbooruTagsTransformerRearrangedByAnimagine": "Prompt Mage · DART Rearranged By Animagine",
    "DanbooruTagsTransformerRemoveTagToken": "Prompt Mage · DART Remove Tag Token",
}

attach_help(NODE_CLASS_MAPPINGS)
from .py.nodes.tag_composer import PromptMageTagComposer
NODE_CLASS_MAPPINGS['DanbooruTagsTransformerTagComposer'] = PromptMageTagComposer
NODE_DISPLAY_NAME_MAPPINGS['DanbooruTagsTransformerTagComposer'] = 'Prompt Mage · Tag Composer (Experimental)'
from .py.nodes.scene_composer import PromptMageSceneComposer
NODE_CLASS_MAPPINGS['DanbooruTagsTransformerSceneComposer'] = PromptMageSceneComposer
NODE_DISPLAY_NAME_MAPPINGS['DanbooruTagsTransformerSceneComposer'] = 'Prompt Mage · Scene Composer'
PromptMageTagComposer.OUTPUT_TOOLTIPS = ('Vocabulary-checked sorted dataset tags.', 'Validated tags plus an explicitly supplied character trigger, if connected. The trigger is a user literal, not a verified booru tag.', 'Scene prose; semantic accuracy remains model-guided.', 'Structured subject/concept selections.', 'ok, warning or blocked.', 'Vocabulary provenance, additions, omissions and validation notes.')

WEB_DIRECTORY = "./web"
from .py.dart.openai_routes import register_openai_routes
register_openai_routes()
from .py.nodes.resolution import PromptMageResolution
NODE_CLASS_MAPPINGS['DanbooruTagsTransformerResolution'] = PromptMageResolution
NODE_DISPLAY_NAME_MAPPINGS['DanbooruTagsTransformerResolution'] = 'Prompt Mage · Resolution'
from .py.nodes.archmage import PromptMageArchmageBeta
NODE_CLASS_MAPPINGS['DanbooruTagsTransformerArchmageBeta'] = PromptMageArchmageBeta
NODE_DISPLAY_NAME_MAPPINGS['DanbooruTagsTransformerArchmageBeta'] = 'Prompt Mage · Archmage (Beta)'

# Preserve execution schemas and IDs; guide new workflows toward the unified node.
for legacy_id in ('DanbooruTagsTransformerDescribeImage', 'DanbooruTagsTransformerImageToText',
                  'DanbooruTagsTransformerSceneComposer'):
    legacy = NODE_CLASS_MAPPINGS[legacy_id]
    legacy.CATEGORY = 'Prompt Mage/Deprecated'
    legacy.DESCRIPTION = ('Deprecated: use Prompt Mage · Archmage (Beta) for new scene, prose and MOSS workflows. '
                          'Kept for existing workflows and specialized legacy features. ' + getattr(legacy, 'DESCRIPTION', ''))
    legacy.DEPRECATED = True
    NODE_DISPLAY_NAME_MAPPINGS[legacy_id] += ' (Deprecated)'

# Retire version-specific v1/v2 entry points without invalidating saved workflows.
for suffix in ('Loader', 'ComposePrompt', 'ComposePromptV2', 'GetAspectRatio'):
    legacy_id = 'DanbooruTagsTransformer' + suffix
    legacy = NODE_CLASS_MAPPINGS[legacy_id]
    legacy.CATEGORY = 'Prompt Mage/Deprecated'
    legacy.DEPRECATED = True
    legacy.DESCRIPTION = ('Deprecated: start new DART workflows with DART v3 Load and Compose Prompt V3. '
                          'Original v1/v2 model choices and behavior remain available for saved workflows. '
                          + getattr(legacy, 'DESCRIPTION', ''))
    NODE_DISPLAY_NAME_MAPPINGS[legacy_id] += ' (Deprecated)'

from .py.nodes.tag_filters import PromptMageTagFilters
NODE_CLASS_MAPPINGS['DanbooruTagsTransformerTagFilters'] = PromptMageTagFilters
NODE_DISPLAY_NAME_MAPPINGS['DanbooruTagsTransformerTagFilters'] = 'Prompt Mage · Tag Filters'

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

from .py.dart.deepseek_routes import register_deepseek_routes
register_deepseek_routes()

from .py.nodes.grimoire import PromptMageGrimoire
NODE_CLASS_MAPPINGS["DanbooruTagsTransformerGrimoire"] = PromptMageGrimoire
NODE_DISPLAY_NAME_MAPPINGS["DanbooruTagsTransformerGrimoire"] = "Prompt Mage · Grimoire (Beta)"
from .py.dart.grimoire_routes import register_grimoire_routes
register_grimoire_routes()

from .py.nodes.spell_scroll import PromptMageSpellScroll
NODE_CLASS_MAPPINGS["DanbooruTagsTransformerSpellScroll"] = PromptMageSpellScroll
NODE_DISPLAY_NAME_MAPPINGS["DanbooruTagsTransformerSpellScroll"] = "Prompt Mage · Spell Scroll"

from .py.nodes.grimoire import PromptMageGrimoireTurn
NODE_CLASS_MAPPINGS["DanbooruTagsTransformerGrimoireTurn"] = PromptMageGrimoireTurn
NODE_DISPLAY_NAME_MAPPINGS["DanbooruTagsTransformerGrimoireTurn"] = "Prompt Mage · Grimoire Turn (Internal)"

from .py.nodes.foundry import PromptMageFoundry, PromptMageFoundryPlan, PromptMageFoundryReviewSaved, PromptMageFoundryReviewOutput
for suffix, cls, label in (
    ('Foundry',PromptMageFoundry,'Foundry (Experimental)'),
    ('FoundryPlan',PromptMageFoundryPlan,'Foundry Plan (Internal)'),
    ('FoundryReviewSaved',PromptMageFoundryReviewSaved,'Foundry Saved Review (Internal)'),
    ('FoundryReviewOutput',PromptMageFoundryReviewOutput,'Foundry · Review Output (Experimental)')):
    NODE_CLASS_MAPPINGS['DanbooruTagsTransformer'+suffix]=cls
    NODE_DISPLAY_NAME_MAPPINGS['DanbooruTagsTransformer'+suffix]='Prompt Mage · '+label
from .py.dart.foundry_routes import register_foundry_routes
register_foundry_routes()

from .py.dart.gemini_routes import register_gemini_routes
register_gemini_routes()
