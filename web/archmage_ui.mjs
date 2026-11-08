const ARCHMAGE = 'DanbooruTagsTransformerArchmageBeta';
const link = value => Array.isArray(value) && value.length === 2 && Number.isInteger(value[1]);

function dependsOn(output, id, target, seen = new Set()) {
    id = String(id);
    if (id === String(target)) return true;
    if (seen.has(id)) return false;
    seen.add(id);
    return Object.values(output[id]?.inputs || {}).some(value => link(value) && dependsOn(output, value[0], target, seen));
}

function compatibleClip(output, source, seen = new Set()) {
    if (!link(source)) return false;
    const id = String(source[0]);
    if (seen.has(id)) return false;
    seen.add(id);
    const node = output[id];
    if (node?.class_type === 'CLIPLoader') return /qwen3[.-]?(?:5|vl)|qwen35/i.test(node.inputs.clip_name || '');
    // Follow the CLIP branch only, never model/conditioning branches or arbitrary encoders.
    return compatibleClip(output, node?.inputs?.clip, seen);
}

export function bindWorkflowEncoders(snapshot) {
    const output = snapshot.output || {};
    for (const [id, node] of Object.entries(output)) {
        if (node.class_type !== ARCHMAGE) continue;
        if (['OpenAI API','DeepSeek API'].includes(node.inputs.assistant_backend)) {
            delete node.inputs.clip; // Preserve the visible wire, skip its unused execution dependency.
            continue;
        }
        if (node.inputs.clip || node.inputs.local_model !== 'Automatic') continue;
        const candidates = new Map();
        for (const consumer of Object.values(output)) {
            if (consumer.class_type !== 'CLIPTextEncode' || !link(consumer.inputs?.text) || !link(consumer.inputs?.clip)) continue;
            if (!dependsOn(output, consumer.inputs.text[0], id)) continue;
            const source = consumer.inputs.clip;
            if (dependsOn(output, source[0], id) || !compatibleClip(output, source)) continue;
            candidates.set(JSON.stringify(source), source);
        }
        // Ambiguous graphs require the explicit CLIP socket. Never guess between two encoders.
        if (candidates.size === 1) node.inputs.clip = [...candidates.values()][0];
    }
    return snapshot;
}

const GROUPS = [
    ['STYLE', ['style_preset', 'style_notes']],
    ['SCENE', ['concepts', 'instructions', 'source_tag_mode', 'length', 'output_format', 'seed', 'control_after_generate']],
    ['CANVAS', ['canvas_source', 'aspect_ratio', 'width', 'height']],
    ['REFERENCE IMAGE · OPTIONAL', ['reference_style', 'image_index', 'image_megapixels', 'resize_mode', 'resize_method']],
    ['MODEL & PERFORMANCE', ['assistant_backend', 'mage_openai_key', 'mage_deepseek_key', 'deepseek_model', 'deepseek_timeout', 'openai_model', 'openai_key_env', 'openai_timeout', 'local_model', 'thinking', 'max_tokens', 'language_style', 'memory_mode', 'unload_after_generation', 'source_name']],
];

export function arrangeArchmage(node) {
    if (!(node.comfyClass || node.type || '').endsWith('ArchmageBeta')) return;
    if (!node.mageSectionWidgets) {
        node.mageSectionWidgets = GROUPS.map(([title]) => {
            // A native fixed-height widget participates in the canvas layout. DOM
            // overlays can retain stale positions after mixed-widget reordering.
            return node.addCustomWidget({
                name: `mage_section_${title}`, type: 'custom', value: '',
                serialize: false, options: {serialize: false},
                computeSize: () => [0, 30],
                draw(ctx, node, width, y, height) {
                    if (this.hidden) return;
                    ctx.save();
                    ctx.fillStyle = '#ffb56b18';
                    ctx.fillRect(10, y + 4, width - 20, height - 8);
                    ctx.fillStyle = '#ffb56b';
                    ctx.fillRect(10, y + 4, 2, height - 8);
                    ctx.font = 'bold 10px sans-serif';
                    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
                    ctx.fillText(title, 20, y + height / 2);
                    ctx.restore();
                },
            });
        });
    }
    const old = [...node.widgets];
    const ordered = [];
    GROUPS.forEach(([, names], i) => {
        ordered.push(node.mageSectionWidgets[i]);
        ordered.push(...names.map(name => old.find(widget => widget.name === name)).filter(Boolean));
    });
    node.widgets = [...ordered, ...old.filter(widget => !ordered.includes(widget))];
}

export function updateArchmageControls(node) {
    const type = node.comfyClass || node.type || '';
    const get = name => node.widgets?.find(widget => widget.name === name);
    if (type.endsWith('Resolution')) {
        for (const name of ['custom_width', 'custom_height']) if (get(name)) get(name).hidden = get('aspect_ratio')?.value !== 'Custom';
        if (get('megapixels')) get('megapixels').hidden = get('aspect_ratio')?.value === 'Custom';
    }
    if (!type.endsWith('ArchmageBeta')) return;
    if (get('source_tag_mode')) {
        get('source_tag_mode').label = 'DART tags policy';
        get('source_tag_mode').hidden = !node.inputs?.some(slot=>slot.name==='source_tags' && slot.link!=null);
    }
    const tagsSlot = node.inputs?.find(slot=>slot.name==='source_tags');
    if (tagsSlot) tagsSlot.label = 'DART tags (scene ideas)';
    const backend = get('assistant_backend')?.value;
    const remote = ['OpenAI API','DeepSeek API'].includes(backend);
    for (const name of ['deepseek_model','deepseek_timeout']) if (get(name)) get(name).hidden = backend !== 'DeepSeek API';
    for (const name of ['openai_model', 'openai_timeout']) if (get(name)) get(name).hidden = backend !== 'OpenAI API';
    if (get('openai_key_env')) get('openai_key_env').hidden = true; // Advanced env configuration remains API/workflow-compatible.
    for (const name of ['local_model', 'memory_mode', 'unload_after_generation']) if (get(name)) get(name).hidden = remote;
    if (get('assistant_backend')) get('assistant_backend').label = 'Assistant (local or paid API)';
    if (get('thinking')) get('thinking').tooltip = backend === 'DeepSeek API'
        ? 'On: DeepSeek thinking enabled at high effort. Off: thinking explicitly disabled. Thinking consumes the token budget and is billable. Private reasoning is not returned.'
        : remote
        ? 'On: medium API reasoning. Off: no reasoning for Terra/Luna; minimum low for Sol/Astra. Reasoning consumes tokens and costs money. No private reasoning trace is returned.'
        : 'Ask a compatible local model to plan before answering. Thinking shares the generation token budget.';
    const hasImage = node.inputs?.some(slot => slot.name === 'image' && slot.link != null);
    for (const name of ['reference_style', 'image_index', 'image_megapixels', 'resize_mode', 'resize_method']) {
        if (get(name)) get(name).hidden = !hasImage;
    }
    if (node.mageSectionWidgets) node.mageSectionWidgets[3].hidden = !hasImage;
    if (get('reference_style')) get('reference_style').label = 'Image treatment (preserve or restyle)';
    if (get('canvas_source')) get('canvas_source').label = hasImage ? 'Canvas size source' : 'Canvas size (uses width / height below)';
    if (get('canvas_source')) get('canvas_source').hidden = !hasImage;
    if (get('concepts')) get('concepts').label = 'Scene idea · WHAT to depict (blank = random)';
    if (get('instructions')) get('instructions').label = 'Writing rules · HOW to describe it';
    const wired = node.inputs?.some(slot => ['width','height'].includes(slot.name) && slot.link != null);
    if (get('aspect_ratio')) get('aspect_ratio').hidden = wired;
    if (get('source_name')) get('source_name').hidden = true;
}
