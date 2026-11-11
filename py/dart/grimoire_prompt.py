"""Explicit conversation/prompt contracts, matching OpenMOSS USERGUIDE.md."""
import json
from secrets import randbits
from .moss import canvas_size, read_layout, compile_layout
from .grimoire_json import json_values, select_json, is_moss
from .grimoire import select_output
from .style_presets import resolve_style


PREVIOUS_DEFAULT_SYSTEM = """You are Grimoire, a warm, sharp creative companion and practical visual director.
Be curious, candid and playful in a natural way, with occasional light fantasy flavor rather than theatrical roleplay.
Match the user's conversational tone. Offer concrete visual ideas, useful choices and honest tradeoffs instead of generic praise.
Keep simple answers short. Ask only when a missing detail truly matters; otherwise make a sensible creative choice.
Never claim to have generated an image, changed a workflow or performed an action you did not perform.
Preserve the user's character trigger, selected appearance, scene constraints and requested medium.
Use personality in discussion; keep image prompts precise and visually observable, without jokes or assistant chatter.
When asked only to reformat a prompt, preserve its scene, wording and geometry. Do not invent a new version.
"""
LEGACY_SYSTEM = 'You are a helpful visual scene and prompt-writing assistant. Follow the requested output format. Describe observable details and coherent spatial relationships.'

DEFAULT_SYSTEM = PREVIOUS_DEFAULT_SYSTEM + """
Use direct, matter-of-fact language for adult creative work, including non-graphic discussions of anatomy, clothing, figure studies and visual composition.
Do not treat an anatomical word, lingerie, swimwear, a body shape or an adult-content label alone as a reason to refuse an otherwise supported request.
For non-graphic appearance descriptions, retain the user's exact selected terms and degree rather than substituting euphemisms or weakening their meaning. Do not infer sexual actions from appearance settings.
Describe only requested, observable details. Do not add erotic embellishment or turn an ordinary fashion or portrait request into a sexual scene.
Distinguish discussion, image analysis and prompt formatting from requests for new content. Preserve supported details during edits and keep the requested output schema intact.
If a request exceeds your supported scope, explain the specific limitation briefly and offer a useful supported alternative. Do not claim an unrestricted mode, changed provider rules or a disabled filter.
"""


def effective_system(value):
    return DEFAULT_SYSTEM if value.strip() in ('', LEGACY_SYSTEM, PREVIOUS_DEFAULT_SYSTEM.strip()) else value


def response_contract(mode, output, width, height, style, notes):
    if mode not in ('Conversation', 'Prompt workshop'):
        raise ValueError('Choose a supported conversation mode.')
    _, guidance = resolve_style(style, notes, randbits(64))
    conversational = mode == 'Conversation'
    contract = (('CURRENT MODE: Conversation. Answer the current question naturally, using readable Markdown. '
                 'Be warm, curious, candid and lightly playful, with sparse fantasy flavor unless the system prompt requests another voice. '
                 'Discuss and plan without emitting an image prompt or JSON unless the current message asks to create, '
                 'continue or revise a prompt. Earlier JSON replies do not require more JSON. '
                 'The appearance recipe is reference information; do not list it on every reply. '
                 'When the user asks for a prompt, use the prompt-format rules below. '
                 'These rules apply to prompt responses only, not ordinary discussion.\n') if conversational else
                'CURRENT MODE: Prompt workshop. Produce one image prompt for the requested scene.\n')
    contract += ('CURRENT VISUAL STYLE: ' + style + '. This live selection supersedes previous style selections in history. '
                 'Use it for the next requested prompt or revision, while preserving the requested scene and character. '
                 'Do not regenerate a prompt just because the style changed. Explicit user scene directions take priority.\n' + guidance)
    contract += ('\nSOURCE ROLES: Current user instructions define the requested change; selected appearance controls the target character; the style selector controls visual treatment; connected dimensions control canvas geometry. '
                 'References provide only the details the user asks to borrow. Do not merge different reference people or silently copy every reference attribute. '
                 'Use current image numbers/socket names/filenames, not old numbering from conversation. Ask one brief question if reference roles are materially ambiguous.\n')
    contract += '\nBEGIN PROMPT RESPONSE RULES (only when a prompt is requested):\n'
    if output == 'MOSS JSON layout':
        canvas_size(width, height)
        example = dict(width=width, height=height, bbox_coord_space='abs', bbox_format='xyxy', summary=dict(meta=['requested medium'], canvas='single', caption='Overall scene description'),
                       items=[dict(label='object', caption='Major subject, pose, clothing, materials and light',
                                   bbox=[width//4, height//4, 3*width//4, 3*height//4])])
        contract += f'''
PROMPT OUTPUT FORMAT: MOSS-Image Pixel Layout draft, compiled by the application.
Official reference: https://github.com/OpenMOSS/MOSS-Image/tree/main/skills/moss-image-prompt-enhancer
For a prompt response, produce ONE complete JSON draft. A json code fence is fine; the app handles presentation.
Do not add an alternative JSON version or a second prompt. Avoid commentary after the JSON.
The user should not have to choose between a draft, prose, and compiled versions.
Exact editable draft structure:
{json.dumps(example)}
Replace placeholders with the requested scene. width={width}, height={height}; match the connected canvas exactly.
Use bbox_coord_space="abs" and bbox_format="xyxy" for your draft.
Boxes are [x_min,y_min,x_max,y_max] in TOP-LEFT PIXELS: 0 <= x_min < x_max <= {width}, 0 <= y_min < y_max <= {height}.
Do NOT calculate centered coordinates. The application converts to native abs_centralized / yxyx and removes width/height.
summary has meta (short medium/style list), canvas ("single"), caption (cohesive complete scene and visual relationships).
items is a FLAT list of major coherent visual units, each with label ("object" or "text"), caption and bbox.
Use one box for a person including their visible pose/clothes, not separate boxes for body parts.
Natural overlap and occlusion are allowed. A box locates an element; it is not a drawn border or crop.
Use the whole composition naturally, including background and intentional negative space. No mandatory full-canvas subject box.
Only requested visible lettering gets a text item with an additional text field containing the exact words and line breaks.
A request such as "put it in a code block" changes chat presentation, not words to draw inside the image.
No children, parent, editor IDs, nested coordinate systems, normalized/percentage boxes or generic scene-schema elements.
Describe observable subject/action, selected appearance, setting, camera/framing, lighting direction, materials and color.
Keep scene counts and relationships coherent across summary and items. Add useful detail without redundant quality tags.
Preserve explicit no-blur/sharp-focus requests. Do not substitute unrequested cinematic grading, identities or anatomy.
On a revision, change only the requested captions/geometry and keep the other content. On formatting-only requests, keep all content.
Do not place explanations of JSON, bounding boxes or conversion inside image captions. Use no placeholder text or invented watermarks.
The pack supports one continuous canvas; do not invent panels or collages unless the user changes the workflow.
Only the compiled prompt goes to the image model. The application provides the copyable preview and Apply action.
'''
    elif output in ('JSON only', 'JSON field'):
        contract += '\nReturn valid JSON only, following the schema supplied in Task instructions.'
    else:
        contract += '\nReturn the image description in readable natural language. Markdown sections are allowed.'
    contract += '\nEND PROMPT RESPONSE RULES.\n'
    if conversational:
        contract += 'For ordinary questions, answer conversationally in Markdown; do not output a scene or JSON unasked.'
    return contract


def response_output_mode(text, mode, output):
    if mode != 'Conversation':
        return output
    # Ordinary chat stays ordinary text. Whole JSON responses use the selected prompt validator.
    if contains_moss(text):
        return 'MOSS JSON layout'
    value = text.lstrip()
    if output != 'Latest response' and value.startswith(('{', '[', '```json', '```\n{', '```\n[')):
        return output
    return 'Latest response'


def extract_response(text, mode, output, section, width, height):
    output = response_output_mode(text, mode, output)
    if output == 'MOSS JSON layout':
        return compile_moss_response(text, width, height)
    return select_output(text, output, section)


def compile_moss_response(text, width, height):
    value = select_json(text, is_moss)
    if value.get('bbox_coord_space') == 'abs' and value.get('bbox_format') == 'xyxy':
        if value.get('width') != width or value.get('height') != height:
            raise ValueError('Draft canvas differs from this response canvas. Match the connected width and height.')
        layout = compile_layout(value, width, height, draft=True)
    else:
        layout = read_layout(json.dumps(value), width, height)
    return json.dumps(layout, ensure_ascii=False, separators=(',', ':'))


def prepare_turn(turn, settings=None):
    result = dict(turn)
    result.pop('prompt_text', None)
    result.pop('format_error', None)
    if result.get('role') != 'assistant':
        return result
    settings = settings or {}
    mode = result.get('mode', 'Latest response')
    if contains_moss(result['content']):
        mode = 'MOSS JSON layout'
    if mode == 'MOSS JSON layout':
        try:
            result['prompt_text'] = compile_moss_response(result['content'], result.get('width',1024), result.get('height',1024))
            result.update(mode=mode, valid=True)
        except (ValueError,TypeError) as error:
            result.update(mode=mode, valid=False, format_error=str(error))
    return result


def contains_moss(text):
    try:
        return any(is_moss(value) for value in json_values(text))
    except ValueError:
        return False
