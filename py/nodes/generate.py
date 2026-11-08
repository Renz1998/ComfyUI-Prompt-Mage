from .base import BaseNode
from ..dart.tag_filters import dart_lists, clean_text

from ..dart.model import DartModel
from ..dart.tokenizer.tokenizer import DartTokenizer
from ..dart.tags import remove_tags as remove_tag_sequences, keep_tags as preserve_tags


class DanbooruTagsTransformerGenerate(BaseNode):
    @classmethod
    def INPUT_TYPES(s):
        input_types = {
            "required": {
                "model": ("DART_MODEL",),
                "tokenizer": ("DART_TOKENIZER",),
                "prompt": (
                    "STRING",
                    {
                        "default": "<|bos|><rating>rating:sfw, rating:general</rating><copyright>original</copyright><character></character><general><|long|>1girl<|input_end|>",
                        "display": "prompt",
                        "multiline": True,
                    },
                ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2**32 - 1}),
                "animagine_order": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "display": "animagine order",
                    },
                ),
            },
            "optional": {
                "setting": ("DART SETTING",),
                "ban_tags": (
                    "STRING",
                    {
                        "default": "",
                        "display": "ban tags",
                        "multiline": True,
                    },
                ),
                "remove_tags": (
                    "STRING",
                    {
                        "default": "",
                        "display": "remove tags",
                        "multiline": True,
                    },
                ),
                "keep_tags": ("STRING", {"default": "", "multiline": True, "tooltip": "Append required tags verbatim. Overrides removal and bans."}),
            },
        }

        input_types["optional"]["filters"] = ("MAGE_TAG_FILTERS", {"tooltip": "Connect a reusable Tag Filters recipe; share it with Archmage."})
        return input_types

    RETURN_TYPES = ("STRING",)
    FUNCTION = "generate"

    def generate(
        self,
        model: DartModel,
        tokenizer: DartTokenizer,
        prompt,
        seed,
        animagine_order=True,
        setting=None,
        ban_tags="",
        remove_tags="",
        keep_tags="",
        filters=None,
    ):
        if filters:
            ban_tags, remove_tags, keep_tags = dart_lists(filters, ban_tags, remove_tags, keep_tags)
        outputs = model.generate(tokenizer, prompt, seed, setting, ban_tags)
        token_ids = outputs[0]

        # remove tags
        token_ids = remove_tag_sequences(tokenizer.tokenizer, token_ids, remove_tags)

        if animagine_order:
            result = tokenizer.decode_by_animagine(token_ids)
        else:
            result = tokenizer.decode(token_ids)
        result = clean_text(result, filters) if filters else result
        return (preserve_tags(result, keep_tags),)
