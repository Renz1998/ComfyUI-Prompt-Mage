from ..dart.openai_assistant import execute_generation, OpenAIEncoder, MODELS, DEFAULT_MODEL
"""Isolated beta composer; existing Scene Composer behavior stays unchanged."""
import json
import re

from .base import BaseNode
from .scene_composer import PromptMageSceneComposer, VISIBLE_EXPRESSIONS
from ..dart.local_assistant import load_local_clip, local_models
from ..dart.memory import offload_after, prepare_assistant_memory
from ..dart.scene_variation import variation
from ..dart.assistant import language_guidance, LANGUAGE_STYLES
from ..dart.appearance import override_instructions, check_layout_appearance, AppearanceMismatch
from ..dart.size_edit import edit_layout
from ..dart.vision import prepare_caption_image, caption_image, parse_caption_json, RESIZE_METHODS
from ..dart.moss import canvas_size, compile_layout, layout_instruction
from ..dart.text_output import final_text, ThinkingBudgetError
from ..dart.style_presets import STYLE_OPTIONS, resolve_style, style_directions
from ..dart.source_tags import TAG_MODES, screen_source_tags
from ..dart.tag_filters import check_recipe, clean_text

PRESETS = {'1:1': (1024, 1024), '3:4': (768, 1024), '4:3': (1024, 768),
           '2:3': (768, 1152), '3:2': (1152, 768), '9:16': (576, 1024), '16:9': (1024, 576),
           '4:5': (1024, 1280), '5:4': (1280, 1024)}


def resolve_canvas(width, height, aspect_ratio='Custom'):
    if aspect_ratio != 'Custom':
        if aspect_ratio not in PRESETS:
            raise ValueError('Choose a supported aspect ratio.')
        width, height = PRESETS[aspect_ratio]
    canvas_size(width, height)
    if max(width, height) > 8192:
        raise ValueError('Canvas dimensions must not exceed 8192 pixels.')
    return width, height


def text_layout(encoder, description, width, height, max_tokens, seed, appearance, report, thinking=False, style_guidance='', constraints=''):
    """Convert a finished scene, with one bounded schema correction attempt."""
    replacements, trigger = override_instructions(appearance)
    system = ('Convert the supplied scene into spatial MOSS JSON. Preserve its concrete details and subject associations. '
              'Return only a JSON object containing layout_draft. No prose outside JSON. ' +
              layout_instruction(width, height) +
              'The draft may also be the root object with summary/items and no bbox metadata; '
              'that root draft MUST use the same top-left pixel xyxy coordinates. '
              'Native centered coordinates require both explicit bbox_coord_space and bbox_format metadata. '
              'Retain the exact character trigger in every caption depicting that character. Do not weaken focus, camera or clothing constraints. '
              + replacements + '\n' + style_guidance + '\nUser constraints to preserve: ' + constraints)
    prompt = description
    for attempt in range(2):
        output = execute_generation(clip=encoder, prompt=prompt, system_prompt=system,
            max_length=max_tokens, sampling_mode={'sampling_mode': 'on', 'temperature': 0.4,
            'top_k': 40, 'top_p': 0.9, 'min_p': 0.05, 'repetition_penalty': 1.08, 'seed': seed},
            thinking=thinking, mtp='off')
        generation = {}
        raw = final_text(output, thinking, generation)
        report['layout_generation'] = generation
        raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.S).strip()
        report.update(layout_attempts=attempt + 1, layout_model_output=raw)
        try:
            value = parse_caption_json(raw)
            if 'layout_draft' in value:
                layout = compile_layout(value['layout_draft'], width, height, draft=True)
            elif 'bbox_coord_space' not in value and 'bbox_format' not in value:
                # Explicit root-draft contract above; never infer a space from numeric values.
                layout = compile_layout(value, width, height, draft=True)
                report['layout_input_schema'] = 'root pixel xyxy draft'
            else:
                layout = compile_layout(value, width, height)
            # Conversion plans space; it must not replace a rich finished scene with a lossy summary.
            layout['summary']['caption'] = description
            if trigger and trigger not in layout['summary']['caption']:
                layout['summary']['caption'] = trigger + ', ' + layout['summary']['caption']
            layout, edits = edit_layout(layout, appearance)
            report.setdefault('post_edits', []).extend(edits)
            try:
                check_layout_appearance(layout, appearance)
            except AppearanceMismatch as error:
                report['issues'].extend(item['message'] for item in error.issues)
            return json.dumps(layout, ensure_ascii=False, indent=2)
        except ValueError as error:
            if attempt == 1:
                raise
            prompt = description + '\nReturn a complete corrected layout. Validation error: ' + str(error) + '\nPrevious response:\n' + raw


class PromptMageArchmageBeta(BaseNode):
    CATEGORY = 'Prompt Mage/Assistants'
    DESCRIPTION = ('Standalone beta. Image connected: describe that image with requested changes. Otherwise develop concepts or invent a seeded scene. '
                   'Canvas context applies to prose and JSON. Appearance changes generated text, not image pixels. Existing composers remain available.')

    @classmethod
    def INPUT_TYPES(cls):
        required = dict(PromptMageSceneComposer.INPUT_TYPES()['required'])
        required['length'][1]['default'] = 'Detailed'
        required['concepts'][1]['tooltip'] = 'WHAT to depict: a subject, place or action. Example: a mage in a red cloak taking a mirror selfie in a hotel. Blank invents a scene. An image supplies the starting scene when connected.'
        required.update({
            'output_format': (['Prose', 'MOSS JSON layout'], {'default': 'MOSS JSON layout', 'tooltip': 'Prose uses one text generation. MOSS retains that full description plus validated spatial boxes. Layout is experimental; compare Prose on the same scene using the description output.'}),
            'aspect_ratio': (['Custom'] + list(PRESETS), {'default': 'Custom', 'tooltip': 'Preset canvas dimensions. Custom uses width and height. An image takes precedence when canvas source is From image.'}),
            'width': ('INT', {'default': 1024, 'min': 16, 'max': 8192, 'step': 16, 'tooltip': 'Manual canvas width, also used as composition context for prose. Connect width/height outputs to your latent node to set generation size.'}),
            'height': ('INT', {'default': 1024, 'min': 16, 'max': 8192, 'step': 16, 'tooltip': 'Manual canvas height. Dimensions must be multiples of 16.'}),
            'canvas_source': (['From image when connected', 'Manual'], {'default': 'From image when connected', 'tooltip': 'Use the processed reference image dimensions, or adapt composition to your chosen manual canvas. Without an image, always use the preset/manual canvas.'}),
        })
        optional = dict(PromptMageSceneComposer.INPUT_TYPES()['optional'])
        optional.update({
            'instructions': ('STRING', {'default': '', 'multiline': True, 'tooltip': 'HOW to write or change it: constraints and rules. Example: keep all clothing, sharp focus throughout, no extra people. Concepts supplies the scene; instructions controls its treatment. Both are optional.'}),
            'image': ('IMAGE', {'tooltip': 'Optional reference, prioritized over random scene suggestions. Concepts and instructions explicitly guide changes to this reference.'}),
            'image_index': ('INT', {'default': 0, 'min': 0, 'tooltip': 'Select one image in an IMAGE batch. List inputs from Batch Upload run individually using ComfyUI list mapping.'}),
            'image_megapixels': ('FLOAT', {'default': 3.7, 'min': 0, 'max': 16, 'step': 0.1, 'tooltip': 'Reference image processing budget, not output resolution. Zero keeps original dimensions up to the 8192-pixel safety cap.'}),
            'resize_mode': (['Downscale only', 'Resize to budget'], {'tooltip': 'Downscale only preserves small references. Resize to budget can enlarge them; it cannot restore missing details.'}),
            'resize_method': (RESIZE_METHODS, {'default': 'lanczos', 'tooltip': 'Image interpolation method used before vision inference.'}),
            'language_style': (LANGUAGE_STYLES, {'default': 'Default', 'tooltip': 'Direct / explicit requests precise supplied terminology. Model behavior still depends on its training.'}),
            'max_tokens': ('INT', {'default': 4096, 'min': 128, 'max': 16384, 'step': 128, 'tooltip': 'Token ceiling per generation stage, including thinking and final answer. With Thinking mode try 8192–16384. Larger budgets can take longer; they do not force longer prompts.'}),
            'source_name': ('STRING', {'default': '', 'tooltip': 'Optional batch filename for diagnostics; never treated as a scene instruction.'}),
            'thinking': ('BOOLEAN', {'default': True, 'tooltip': 'Ask a compatible model to plan before answering. Slower; try 8192 tokens if the current 4096 budget runs out. Reasoning stays separate from prompt outputs.'}),
            'style_preset': (STYLE_OPTIONS, {'default': 'Photo · Bright lifestyle', 'tooltip': 'Visual treatment, not scene content. Bright lifestyle favors crisp detail and clean light like the beach example, while keeping your chosen location. Explicit instructions take priority.'}),
            'style_notes': ('STRING', {'default': '', 'multiline': True, 'tooltip': 'Refine any preset or write your own style. Required for Custom. Examples: cheap phone camera, flat afternoon light, no color grading. These guide generated text, not model weights or image pixels.'}),
            'reference_style': (['Preserve reference style', 'Apply selected style'], {'default': 'Preserve reference style', 'tooltip': 'With an image, preserve its visible medium and camera treatment by default. Apply selected style explicitly restyles the caption while retaining subjects and spatial details unless your instructions change them.'}),
            'memory_mode': (['Automatic', 'Native ComfyUI'], {'default': 'Automatic', 'tooltip': 'Automatic asks ComfyUI to offload competing models and reserve 2 GB for generation before each run. Interrupted runs release this assistant. Does not clear all models. Native leaves preparation to ComfyUI.'}),
            'assistant_backend': (['Local Qwen', 'OpenAI API'], {'default': 'Local Qwen', 'tooltip': 'Local keeps inference on this machine. OpenAI sends scene text, appearance instructions and any connected reference image to OpenAI and incurs API charges. It does not use the local CLIP.'}),
            'openai_model': (list(MODELS), {'default': DEFAULT_MODEL, 'tooltip': 'Terra: recommended lower-cost visual/writing model. Sol: recommended for harder composition. Astra: expensive. Labels show standard USD per 1M input/output tokens, checked 2026-11-07; pricing/access can change. Reasoning counts toward billed output.'}),
            'openai_key_env': ('STRING', {'default': 'OPENAI_API_KEY', 'tooltip': 'Environment variable NAME on the ComfyUI server, not the API key. Restart the server after setting it. Keys are never saved in workflows by this node.'}),
            'openai_timeout': ('INT', {'default': 180, 'min': 10, 'max': 600, 'tooltip': 'Seconds per API request. A timeout/cancel may still incur charges. No automatic network retries. Text → MOSS normally uses two requests; a schema correction may add one.'}),
            'source_tags': ('STRING', {'forceInput': True, 'tooltip': 'Optional DART Generate / Decode tags. Treated as candidate scene ideas, not character identity or mandatory instructions. Appearance settings, explicit scene ideas, style and reference images take priority.'}),
            'source_tag_mode': (TAG_MODES, {'default': TAG_MODES[0], 'tooltip': 'Scene ideas removes known random hair, eye, body and named-character traits. Keep unselected appearance allows unselected traits but still removes known conflicts with chosen replacements. Both discard metadata and defer to the chosen style. See report.source_tags for candidates and removal reasons.'}),
        })
        optional['filters'] = ('MAGE_TAG_FILTERS', {'tooltip': 'Shared Tag Filters recipe: clean source tags and request the same exclusions in prose/JSON. Assistant wording remains model-guided.'})
        optional['local_model'][1]['tooltip'] = 'A connected CLIP wins. Automatic in the browser reuses a compatible downstream text encoder when unambiguous; otherwise uses a small installed Qwen. If none exists, downloads the official Qwen3.5 2B fallback once.'
        return {'required': required, 'optional': optional, 'hidden': {'prompt': 'PROMPT', 'unique_id': 'UNIQUE_ID'}}

    RETURN_TYPES = ('STRING', 'STRING', 'STRING', 'INT', 'INT', 'IMAGE', 'STRING', 'STRING')
    RETURN_NAMES = ('prompt', 'description', 'moss_json', 'width', 'height', 'image', 'status', 'report')
    OUTPUT_TOOLTIPS = ('Selected output format, ready to encode.', 'Prose scene, useful for a separate tagger.', 'Validated native MOSS JSON; inactive in Prose mode.',
                       'Resolved canvas width.', 'Resolved canvas height.', 'Processed reference; inactive without an image. Appearance edits do not alter pixels.',
                       'ok, warning, or blocked. Read the report for details.', 'JSON diagnostics, source, dimensions and generation notes.')
    FUNCTION = 'generate'
    OUTPUT_NODE = True

    def generate(self, concepts='', length='Balanced', seed=0, output_format='Prose', aspect_ratio='Custom',
                 width=1024, height=1024, canvas_source='From image when connected', appearance=None,
                 instructions='', local_model='Automatic', clip=None, max_tokens=4096, unload_after_generation=False,
                 image=None, image_index=0, image_megapixels=1.0, resize_mode='Downscale only',
                 resize_method='lanczos', language_style='Default', source_name='', thinking=False,
                 style_preset='None (model choice)', style_notes='', reference_style='Preserve reference style',
                 memory_mode='Automatic', prompt=None, unique_id=None, assistant_backend='Local Qwen',
                 openai_model=DEFAULT_MODEL, openai_key_env='OPENAI_API_KEY', openai_timeout=180,
                 source_tags='', source_tag_mode=TAG_MODES[0], filters=None):
        from comfy_execution.graph import ExecutionBlocker
        if output_format not in ('Prose', 'MOSS JSON layout') or length not in ('Short', 'Balanced', 'Detailed'):
            raise ValueError('Choose a supported output format and length.')
        if canvas_source not in ('From image when connected', 'Manual'):
            raise ValueError('Choose a supported canvas source.')
        if memory_mode not in ('Automatic', 'Native ComfyUI'):
            raise ValueError('Choose a supported memory mode.')
        if assistant_backend not in ('Local Qwen', 'OpenAI API'):
            raise ValueError('Choose Local Qwen or OpenAI API.')
        inputs = (prompt or {}).get(str(unique_id), {}).get('inputs', {})
        wired_size = any(isinstance(inputs.get(key), list) for key in ('width', 'height'))
        width, height = resolve_canvas(width, height, 'Custom' if wired_size else aspect_ratio)
        replacements, trigger = override_instructions(appearance)
        wording = language_guidance(language_style)
        resolved_style, style_guidance = resolve_style(style_preset, style_notes, seed)
        if reference_style not in ('Preserve reference style', 'Apply selected style'):
            raise ValueError('Choose a supported reference style mode.')
        style_applied = bool(style_guidance) and (image is None or reference_style == 'Apply selected style')
        if not style_applied:
            style_guidance = ''
        recipe = check_recipe(filters)
        if filters:
            if recipe.get('preset') in ('Full color', 'Full color + clean photo') and any(x in (style_preset + ' ' + style_notes).casefold() for x in ('monochrome', 'black and white', 'greyscale', 'grayscale')):
                raise ValueError('Full color tag filter conflicts with the selected style. Change the style or filter preset.')
            source_tags = clean_text(source_tags, filters)
        tag_guidance, tag_report = screen_source_tags(source_tags, appearance, source_tag_mode,
                                                     style_active=style_applied, reference=image is not None)
        if filters:
            tag_report['filters'] = recipe
            tag_guidance += '\nTag filter constraints (do not render as visible writing): ' + ' '.join(recipe['guidance'])
            if recipe['banned'] or recipe['removed']:
                tag_guidance += '\nAvoid these exact concepts: ' + ', '.join(sorted(set(recipe['banned'] + recipe['removed'])))
        tag_ideas = bool(tag_report['candidates'])
        guided = bool(concepts.strip() or instructions.strip() or tag_ideas)
        scene_concepts = concepts or ('Compose a coherent scene using the optional DART candidate concepts supplied in the instructions.' if tag_ideas else '')
        prepared = None
        processed_size = None
        if image is not None:
            prepared, iw, ih = prepare_caption_image(image, image_index, image_megapixels, resize_mode, resize_method,
                                                    canvas_source == 'From image when connected')
            processed_size = [iw, ih]
            if canvas_source == 'From image when connected':
                width, height = iw, ih
        shape = 'portrait' if height > width else 'landscape' if width > height else 'square'
        context = (f'Compose for a {width}x{height} {shape} canvas (aspect ratio {width / height:.3f}). '
                   'Use this framing context even for prose; do not render resolution numbers as visible writing. '
                   'Describe concrete visible details, not feelings, metaphors or narrative. ')
        context += ('Preserve explicit scene constraints, including sharp focus and no blur. '
                    'Do not change clothing into nudity simply because a body-size trait was selected. '
                    'Spend detail on materials, pose, camera distance, light and readable surroundings, not quality slogans. ')
        mirror_requested = ('mirror selfie' in (concepts + ' ' + instructions + ' ' + resolved_style).casefold() or
                            (image is None and 'mirror selfie' in tag_report['candidates']))
        if mirror_requested:
            context += ('For the requested mirror selfie, describe one reflected person and one visible phone. '
                        'Hold the phone between person and mirror at normal arm distance, rear cameras facing the mirror, '
                        'never against the glass. Use plausible grip and gaze toward the screen; no second person or extra phone. ')
        if thinking:
            context += ('Plan a readable focal hierarchy, balanced visual weight, useful negative space, consistent perspective, '
                        'subject scale, lighting and spatial relationships before answering. Check left/right, overlaps and occlusion. '
                        'Respect the reference image and explicit user choices; do not redesign preserved details. '
                        'Keep the final answer in the requested format. ')
        context += '\n' + style_guidance
        if source_tags.strip():
            context += tag_guidance
        report = dict(status='ok', issues=[], seed=seed, source='image' if prepared is not None else 'text',
                      source_name=source_name, canvas=[width, height], processed_image=processed_size,
                      output_format=output_format, thinking_requested=thinking, max_tokens_per_stage=max_tokens, post_edits=[],
                      canvas_resolved_from='processed image' if prepared is not None and canvas_source == 'From image when connected' else 'connected dimensions' if wired_size else 'manual / preset',
                      memory_mode=memory_mode, encoder_source='connected / workflow encoder' if clip is not None else local_model,
                      source_tags=tag_report,
                      style=dict(selected=style_preset, resolved=resolved_style, notes=style_notes,
                                 applied=style_applied, reference_mode=reference_style),
                      note='Beta: compare with Scene Composer. Canvas outputs set generation size only when connected to your latent node. Appearance semantics remain model-guided.')
        if source_tags.strip():
            report['note'] += f" DART: {len(tag_report['candidates'])} candidate ideas; {len(tag_report['removed'])} filtered. See report.source_tags for reasons; relevance is model-guided."
        encoder = (OpenAIEncoder(openai_model, openai_key_env, openai_timeout) if assistant_backend == 'OpenAI API'
                   else load_local_clip(local_model, clip, auto_download=True))
        report['assistant_backend'] = assistant_backend
        if assistant_backend == 'OpenAI API':
            report['encoder_source'] = 'OpenAI Responses API'
        description = ''
        moss = None
        with offload_after(encoder, unload_after_generation, release_on_error=True):
            if memory_mode == 'Automatic':
                prepare_assistant_memory(encoder)
            if prepared is not None:
                target = {'Short': '40–70', 'Balanced': '80–130', 'Detailed': '140–220'}[length]
                vision_instructions = context + f'Aim for {target} useful words, without padding. ' + replacements + '\n' + instructions
                if concepts.strip():
                    vision_instructions += '\nApply these requested concepts/changes to the reference: ' + concepts
                diagnostics = {}
                try:
                    result = caption_image(prepared, vision_instructions, trigger, 'Concise' if length == 'Short' else 'Detailed',
                        0, max_tokens, clip=encoder, language_style=language_style,
                        output_format='Plain text' if output_format == 'Prose' else output_format,
                        canvas_width=width, canvas_height=height, appearance=appearance, diagnostics=diagnostics, thinking=thinking)
                    if output_format == 'Prose':
                        description = result
                    else:
                        moss = result
                        description = json.loads(moss)['summary']['caption']
                except ValueError as error:
                    report['status'] = 'blocked'
                    report['issues'].append(str(error))
                report['vision'] = diagnostics
                report['issues'].extend(item['message'] for item in diagnostics.get('issues', []))
                report['post_edits'].extend(diagnostics.get('edits', []))
            else:
                directions = variation(seed, guided=guided)
                mood = directions.pop('mood')
                if not (appearance and appearance.get('enabled') and appearance.get('traits', {}).get('expression')):
                    directions['visible_expression'] = VISIBLE_EXPRESSIONS[mood]
                directions = style_directions(directions, resolved_style, seed,
                    guided, style_applied)
                guidance = context + wording + '\nSeeded suggestions (explicit user instructions take priority): ' + json.dumps(directions) + '\n' + instructions
                try:
                    generated = PromptMageSceneComposer().generate(scene_concepts, length, seed, appearance, guidance,
                        local_model, encoder, max_tokens, False, thinking=thinking,
                        creative_directions=directions if style_applied else None)
                    description = generated['result'][0]
                    scene_report = generated['ui']['mage_report'][0]
                    report['scene'] = scene_report
                    report['issues'].extend(scene_report['issues'])
                    report['post_edits'].extend(scene_report['post_edits'])
                except ThinkingBudgetError as error:
                    report['status'] = 'blocked'
                    report['issues'].append(str(error))
                if output_format == 'MOSS JSON layout' and report['status'] != 'blocked':
                    try:
                        moss = text_layout(encoder, description, width, height, max_tokens, seed, appearance, report,
                                           thinking=thinking, style_guidance=style_guidance, constraints=concepts + '\n' + instructions)
                    except ThinkingBudgetError as error:
                        report['status'] = 'blocked'
                        report['issues'].append(str(error))
                    except ValueError as error:
                        report['status'] = 'blocked'
                        report['issues'].append('MOSS conversion failed after two attempts: ' + str(error))
        if isinstance(encoder, OpenAIEncoder):
            report['api'] = dict(model=encoder.model, calls=encoder.calls,
                reasoning_tokens=sum(call['reasoning_tokens'] for call in encoder.calls),
                note='Standard API charges apply, including reasoning. Seed varies scene suggestions, not deterministic API sampling. Cancellation cannot undo a billed request. Provider content policies apply.')
        elif thinking and report['status'] != 'blocked':
            stages = [report['vision']] if 'vision' in report else [report.get('scene', {}).get('generation', {})]
            if 'layout_generation' in report:
                stages.append(report['layout_generation'])
            report['thinking_output_detected'] = all(stage.get('thinking_output_detected', False) for stage in stages)
            if not report['thinking_output_detected']:
                report['issues'].append('Thinking was requested, but at least one generation stage returned no separate thinking output. '
                                        'The selected model/loader may not support this switch. The final answer is available; thinking is unconfirmed.')
        if report['issues'] and report['status'] != 'blocked':
            report['status'] = 'warning'
        if moss:
            from ..dart.moss import layout_diagnostics
            report['layout'] = layout_diagnostics(json.loads(moss), width, height)
        selected = moss if output_format == 'MOSS JSON layout' else description
        prompt = selected if report['status'] != 'blocked' else ExecutionBlocker(None)
        values = (prompt, description or ExecutionBlocker(None), moss if moss is not None else ExecutionBlocker(None),
                  width, height, prepared if prepared is not None else ExecutionBlocker(None), report['status'],
                  json.dumps(report, ensure_ascii=False, indent=2))
        return {'ui': {'text': [selected or '\n'.join(report['issues'])], 'mage_report': [report],
                       'json_preview': [bool(moss)]}, 'result': values}
