"""Explicit conversation/prompt contracts, matching OpenMOSS USERGUIDE.md."""
import json
from secrets import randbits
from .moss import canvas_size, read_layout
from .grimoire import select_output
from .style_presets import resolve_style


def response_contract(mode, output, width, height, style, notes):
    if mode == 'Conversation':
        return ('CURRENT MODE: Conversation. Answer the current question naturally, using readable Markdown. '
                'Discuss and plan without emitting an image prompt or JSON unless the current message explicitly asks for one. '
                'Earlier JSON replies are context, not a requirement to keep producing JSON. '
                'The appearance recipe is reference information; do not list it on every reply.')
    if mode != 'Prompt workshop':
        raise ValueError('Choose Conversation or Prompt workshop.')
    _, guidance = resolve_style(style, notes, randbits(64))
    contract = ('CURRENT MODE: Prompt workshop. Produce one image prompt for the current requested scene, '
                'using the agreed task and character. Describe observable details and physical spatial relationships. '
                'Do not invent unrequested identity details.\n' + guidance)
    if output == 'MOSS JSON layout':
        canvas_size(width, height)
        example = dict(summary=dict(meta=['requested medium'], canvas='single', caption='Overall scene description'),
                       items=[dict(label='object', caption='Major subject, pose, clothing, materials and light',
                                   bbox=[-height//4, -width//4, height//4, width//4])],
                       bbox_coord_space='abs_centralized', bbox_format='yxyx')
        contract += f'''
MANDATORY OUTPUT FORMAT: MOSS-Image native layout JSON, not a generic scene JSON.
Return exactly one JSON object, no Markdown fences or commentary. Exact structure:
{json.dumps(example)}
Replace placeholders with detailed, coherent descriptions of the requested scene.
Only these top-level keys: summary, items, bbox_coord_space, bbox_format.
summary has meta (string list), canvas ("single"), caption (full scene, camera, light and background).
items has 1–8 major spatial elements. Each has label ("object" or "text"), caption, bbox.
One item per major subject; do not split body parts or clothing into separate subjects.
Only requested visible lettering gets a text item, with an additional text key containing the exact words.
Canvas: {width} x {height}. Coordinates are ABSOLUTE CENTERED PIXELS, NOT normalized.
bbox is [y_min,x_min,y_max,x_max], y in [{-height/2},{height/2}], x in [{-width/2},{width/2}].
Require y_min < y_max and x_min < x_max. Boxes locate visible extents, not a crop or mask.
Allow natural overlaps. Background can extend across the canvas; subjects need not fill it.
Keep summary and items consistent. Do not output subject/camera/lighting/layout/tags/captions objects.
Preserve explicit focus/no-blur instructions and chosen style. Describe actual texture, light and framing.
'''
    elif output in ('JSON only', 'JSON field'):
        contract += '\nReturn valid JSON only, following the schema supplied in Task instructions.'
    else:
        contract += '\nReturn the image description in readable natural language. Markdown sections are allowed.'
    return contract


def extract_response(text, mode, output, section, width, height):
    if mode == 'Conversation':
        return text
    if output == 'MOSS JSON layout':
        return json.dumps(read_layout(select_output(text, 'JSON only', ''), width, height), ensure_ascii=False, indent=2)
    return select_output(text, output, section)
