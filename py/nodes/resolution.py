"""Model-independent canvas selection; no latent allocation or CRT dependency."""
import math
from .base import BaseNode

RATIOS = {'1:1': (1, 1), '2:3': (2, 3), '3:2': (3, 2), '3:4': (3, 4),
          '4:3': (4, 3), '9:16': (9, 16), '16:9': (16, 9), '21:9': (21, 9),
          '4:5': (4, 5), '5:4': (5, 4)}


def resolution(megapixels=1.0, aspect_ratio='2:3', multiple=16, custom_width=1024, custom_height=1024):
    if aspect_ratio not in (*RATIOS, 'Custom') or multiple not in (16, 32, 64):
        raise ValueError('Choose a supported aspect ratio and alignment.')
    if aspect_ratio == 'Custom':
        if any(isinstance(v, bool) or not isinstance(v, int) or not 16 <= v <= 8192 for v in (custom_width, custom_height)):
            raise ValueError('Custom dimensions must be integers between 16 and 8192.')
        width, height = custom_width, custom_height
    else:
        if not math.isfinite(megapixels) or not 0.25 <= megapixels <= 16:
            raise ValueError('Megapixel budget must be between 0.25 and 16.')
        x, y = RATIOS[aspect_ratio]
        width = math.sqrt(megapixels * 1_000_000 * x / y)
        height = width * y / x
    width, height = (max(multiple, round(v / multiple) * multiple) for v in (width, height))
    if max(width, height) > 8192:
        raise ValueError('Resolved dimensions exceed 8192 pixels.')
    return width, height


class PromptMageResolution(BaseNode):
    CATEGORY = 'Prompt Mage/Canvas'
    DESCRIPTION = 'Choose a canvas once. Connect the same width/height to Archmage and your empty latent. No model selection, CRT pack or VRAM allocation needed.'

    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {
            'aspect_ratio': (list(RATIOS) + ['Custom'], {'default': '2:3', 'tooltip': 'Shape of the output image. Custom uses the two dimensions below instead of a pixel budget.'}),
            'megapixels': ('FLOAT', {'default': 3.7, 'min': 0.25, 'max': 16, 'step': 0.1, 'tooltip': 'Approximate total pixels in millions, not pixels per side. Higher values require more VRAM; rounded dimensions slightly change this total. MOSS recommends 1–2 MP; 3.7 MP preserves your working preset.'}),
            'multiple': ([16, 32, 64], {'default': 32, 'tooltip': 'Round both dimensions to this alignment. MOSS requires at least multiples of 16.'}),
            'custom_width': ('INT', {'default': 1024, 'min': 16, 'max': 8192, 'step': 16, 'tooltip': 'Used only for Custom; rounded to the chosen alignment.'}),
            'custom_height': ('INT', {'default': 1024, 'min': 16, 'max': 8192, 'step': 16, 'tooltip': 'Used only for Custom; rounded to the chosen alignment.'}),
        }}
    RETURN_TYPES = ('INT', 'INT', 'STRING')
    RETURN_NAMES = ('width', 'height', 'size')
    FUNCTION = 'select'

    def select(self, aspect_ratio='2:3', megapixels=3.7, multiple=32, custom_width=1024, custom_height=1024):
        width, height = resolution(megapixels, aspect_ratio, multiple, custom_width, custom_height)
        return width, height, f'{width} × {height} · {width * height / 1_000_000:.2f} MP'
