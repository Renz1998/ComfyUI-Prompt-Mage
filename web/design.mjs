const stylesheet = document.createElement("link");
stylesheet.rel = "stylesheet";
stylesheet.href = new URL("./dart.css?v=1.12.0", import.meta.url).href;
document.head.append(stylesheet);

const designs = new WeakMap();
const profiles = {
    upload: { title: "UPLOAD IMAGES", subtitle: "UPLOAD IMAGES → QUEUED CAPTIONS / LIST", color: "#233c49", accent: "#a2d6f4", text: "Click the drop area to browse local files, drop images onto the node, or use Choose folder for local image folders, including on RunPod. Reorder with arrows; remove/clear changes this list and keeps server files. Connect image to Archmage and filename to source_name. Use Run all images from first: Batch mode off queues the whole workflow per image; on submits one list run. Manual index controls are available from the right-click menu." },
    batch: { title: "SERVER FOLDER · ADVANCED", subtitle: "FOLDER → QUEUED IMAGE / SEQUENTIAL LIST", color: "#233c49", accent: "#a2d6f4", text: "Choose a folder on the computer running ComfyUI. One image per queued run uses Index plus the native increment control. List mode maps Archmage sequentially over separate images. Keep its Image in batch at 0. Max images limits CPU memory in list mode; use queue mode for large folders." },
    appearance: { title: "APPEARANCE OVERRIDES", subtitle: "ONE RECIPE → YOUR ASSISTANTS", color: "#423044", accent: "#efb4df", text: "Connect appearance to Archmage. Keep unchanged leaves a trait alone. Custom reveals a free-text value. Choose the subject, optional character trigger and replacements. Changes apply to generated text in every format; source image pixels stay unchanged." },
    vision: { title: "VISION CAPTIONER", subtitle: "IMAGE → DETAILED TEXT", color: "#183d49", accent: "#79d9ee", text: "Connect an image, then Run for a detailed caption. Instructions can replace appearance while keeping pose, clothing and scene details. Character trigger inserts your exact training token. This creates text; it does not edit image pixels." },
    assistant: { title: "SCENE ASSISTANT", subtitle: "WORDS → TAGS / PROSE", color: "#173d36", accent: "#79e5bd", text: "Write a scene or connect Dart Generate to source_tags. Concept turns keywords into a new scene; Natural language outputs prose. Custom instructions control style and wording. Local model + Automatic uses installed Qwen. Connect prompt to image text encoding." },
    loader: { title: "MODEL LIBRARY", subtitle: "MODEL + MATCHING TOKENIZER", color: "#1e3453", accent: "#8ebcff" },
    composer: { title: "PROMPT BUILDER", subtitle: "VISUAL TAGS → DART FORMAT", color: "#44351f", accent: "#f0c780" },
    generate: { title: "TAG GENERATOR", subtitle: "SEED TAGS → IMAGE PROMPT", color: "#352747", accent: "#c7a4ff" },
    utility: { title: "TAG WORKSHOP", subtitle: "INSPECT · FILTER · DECODE", color: "#293545", accent: "#a7bfdc" },
};

function profileFor(name) {
    if(name.endsWith('FoundryReviewOutput')) return {title:'FOUNDRY · INSPECTOR',subtitle:'ACTUAL PIXELS → PHYSICAL CHECKS → SHOT REVIEW',color:'#483026',accent:'#ffbf80',text:'Reviews the generated image for anatomy, body/object contact, garment continuity and scene cohesion before assessing prompt match. It saves the image and inspection for Foundry. Automatic mode retries within your caps. AI inspection can miss defects; inspect the accepted collection before publishing.'};
    if(name.endsWith('SpellScroll')) return {title:'SPELL SCROLL',subtitle:'APPLIED PROMPT → IMAGE WORKFLOW',color:'#263649',accent:'#cbb987',text:'Reads the response explicitly applied from Grimoire. No assistant or API calls. Further chat does not change this saved prompt. Connect prompt to the positive encoder and use matching canvas dimensions.'};
    if (name.endsWith('Grimoire')) return {title:'GRIMOIRE · BETA',subtitle:'CONVERSATION → MEMORY → PROMPTS',color:'#272039',accent:'#d4b66f',text:'A persistent spellbook: separate system/task instructions, pinned facts and appearance recipe. Send queues the connected workflow. Next step continues; Regenerate replaces the last answer. Summaries are lossy and editable. Clear removes history/summary, not configured instructions. Conversations are plaintext on this server; use a trusted/private installation.'};
    if (['DescribeImage','ImageToText','SceneComposer'].some(suffix => name.endsWith(suffix))) return {title:'LEGACY ASSISTANT',subtitle:'DEPRECATED · NEW WORKFLOWS → ARCHMAGE',color:'#34323b',accent:'#c1b6a7',text:'This node remains available for saved workflows and specialized legacy features. For new scene, prose and MOSS workflows use Prompt Mage · Archmage (Beta). Existing sockets and behavior are retained. See the legacy assistant guide for external chat servers and Structured JSON captions.'};
    if (name.endsWith("ArchmageBeta")) return {title:"ARCHMAGE · BETA",subtitle:"REFERENCE / CONCEPT → PROSE / MOSS",color:"#33233d",accent:"#ffba72",text:"Reference image takes priority. Without one, develop concepts or leave them blank for a seeded scene. Canvas context works in prose and JSON. Appearance changes text, not image pixels. Use style presets and optional thinking. Older assistants remain available under Deprecated."};
    if (name.endsWith("SceneComposer")) return {title:"SCENE COMPOSER",subtitle:"YOUR CHARACTER → A NEW SCENE",color:"#483026",accent:"#ffbf80",text:"Leave concepts blank to invent a scene. Connect Appearance Overrides to keep your character. Concepts and instructions guide the result. Seed randomize changes the next queued run; fixed repeats seeded directions. This node outputs prose directly without a JSON plan."};
    if (name.endsWith('TagComposer')) return {title:'TAG COMPOSER',subtitle:'IDEA → SCENE → CHECKED TAGS',color:'#483026',accent:'#ffbf80',text:'Start with 1girl or a rough idea. Invent develops a scene; Faithful requests no additions. Qwen plans then chooses from a pinned offline tag vocabulary. Review notes for unmatched concepts and additions. Sorting needs no DART model. Valid tags do not guarantee correct scene meaning or final image quality.'};
    if (name.endsWith("ImageBatchUpload")) return profiles.upload;
    if (name.endsWith("ImageBatchSelector")) return profiles.batch;
    if (name.endsWith("AppearanceOverrides")) return profiles.appearance;
    if (name.endsWith("ImageToText")) return profiles.vision;
    if (name.endsWith("DescribeImage")) return profiles.assistant;
    if (name.endsWith("Loader") || name.endsWith("LoaderV3")) return profiles.loader;
    if (name.includes("ComposePrompt")) return profiles.composer;
    if (name.endsWith("Generate") || name.endsWith("GenerateAdvanced")) return profiles.generate;
    return profiles.utility;
}

function applyAppearance(node) {
    const design = designs.get(node);
    if (!design) return;
    const enabled = node.properties.dart_design !== false;
    const ember = node.properties.atelier_theme !== "studio";
    design.root.dataset.theme = ember ? "ember" : "studio";
    design.root.style.setProperty("--dart-accent", ember ? "#ffaf69" : design.profile.accent);
    design.widget.hidden = !enabled;
    if (enabled) {
        node.color = ember ? "#563021" : design.profile.color;
        node.bgcolor = ember ? "#251c1b" : "#172128";
        node.boxcolor = ember ? "#ffaf69" : design.profile.accent;
        node.shape = LiteGraph.ROUND_SHAPE;
    } else {
        Object.assign(node, design.original);
    }
}

export function installDesign(node, data) {
    const profile = profileFor(data.name);
    node.properties ||= {};
    const original = { color: node.color, bgcolor: node.bgcolor, boxcolor: node.boxcolor, shape: node.shape };
    const root = document.createElement("div");
    root.className = "dart-panel";
    root.setAttribute("aria-label", `${profile.title} guide`);
    root.style.setProperty("--dart-accent", profile.accent);
    root.dataset.state = "ready";
    root.innerHTML = `<div class="dart-panel-bar"><div class="dart-brand"><span class="dart-mark">PM</span><div><strong>PROMPT MAGE</strong><span class="dart-role"></span></div></div><span class="dart-state" role="status" aria-live="polite"><i></i><span>READY</span></span><button class="dart-help-button" type="button" aria-expanded="false" title="Show a quick guide and wiring tips for this node">?</button></div><div class="dart-caption"></div><div class="dart-help"><p></p><span>Hover controls and sockets for details. Right-click the node for Ember/Studio themes or to disable the design.</span></div><div class="dart-fire" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><b></b><b></b><b></b></div><div class="dart-scan"></div>`;
    root.querySelector(".dart-role").textContent = profile.title;
    root.querySelector(".dart-caption").textContent = profile.subtitle;
    root.querySelector(".dart-help p").textContent = profile.text || data.description || "Hover each control and socket for help.";
    let open = false;
    const height = () => open ? 240 : 96;
    const widget = node.addDOMWidget("dart_guide", "DART_GUIDE", root, {
        serialize: false, hideOnZoom: true, getMinHeight: height, getMaxHeight: height,
    });
    widget.serialize = false;
    const button = root.querySelector(".dart-help-button");
    button.setAttribute("aria-label", "Quick guide");
    button.addEventListener("click", (event) => {
        event.stopPropagation();
        open = !open;
        root.dataset.open = String(open);
        button.setAttribute("aria-expanded", String(open));
        const size = node.computeSize();
        node.setSize([Math.max(380, node.size[0], size[0]), Math.max(node.size[1], size[1])]);
        node.setDirtyCanvas(true, true);
    });
    designs.set(node, { root, widget, profile, original });
    const foreground = node.onDrawForeground;
    node.onDrawForeground = function (ctx) {
        foreground?.apply(this, arguments);
        if (root.dataset.state !== "running" || this.properties.dart_design === false || this.flags?.collapsed) return;
        ctx.save();
        ctx.strokeStyle = root.dataset.theme === "ember" ? "#ff9b48" : profile.accent;
        ctx.shadowColor = ctx.strokeStyle; ctx.shadowBlur = 18; ctx.lineWidth = 3;
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(-2,-2,this.size[0]+4,this.size[1]+4,12);
        else ctx.rect(-2,-2,this.size[0]+4,this.size[1]+4);
        ctx.stroke(); ctx.restore();
    };
    applyAppearance(node);
    const size = node.computeSize();
    node.setSize([Math.max(380, node.size[0], size[0]), Math.max(node.size[1], size[1])]);
}

export function configureDesign(node) {
    applyAppearance(node);
    const size = node.computeSize();
    node.setSize([Math.max(380, node.size[0], size[0]), Math.max(node.size[1], size[1])]);
}

export function toggleDesign(node) {
    node.properties.dart_design = node.properties.dart_design === false;
    applyAppearance(node);
    const size = node.computeSize();
    node.setSize([node.size[0], size[1]]);
    node.setDirtyCanvas(true, true);
}

export function toggleTheme(node) {
    node.properties.atelier_theme = node.properties.atelier_theme === "studio" ? "ember" : "studio";
    applyAppearance(node);
    node.setDirtyCanvas(true, true);
}

export function setDesignState(node, state) {
    const design = designs.get(node);
    if (!design) return;
    design.root.dataset.state = state;
    design.root.querySelector(".dart-state span").textContent = {
        ready: "READY", running: "RUNNING", done: "DONE", error: "CHECK INPUT", warning: "REVIEW OVERRIDES", blocked: "DOWNSTREAM BLOCKED",
    }[state] || "READY";
    node.setDirtyCanvas(true, true);
}

export function updateDesignBackend(node, server) {
    const design = designs.get(node);
    if (design?.profile === profiles.assistant) {
        design.root.querySelector(".dart-caption").textContent = server
            ? "CHAT SERVER · WORDS → PROMPT" : "LOCAL MODEL · WORDS → PROMPT";
    }
}
