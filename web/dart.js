import { installDeepSeekKeyWidget, refreshDeepSeekKeyWidget } from "./deepseek_key.mjs?v=1.19.1";
import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { convertToInput } from "../../extensions/core/widgetInputs.js";
import { addTextPreviewWidgets, updateTextPreviewWidgets } from "../../extensions/core/textPreviewWidgets.js";
import { connectionsFor, resolveSlot } from "./connections.mjs?v=1.15.0";
import { installDesign, configureDesign, toggleDesign, toggleTheme, setDesignState, updateDesignBackend } from "./design.mjs?v=1.19.1";
import { installStatusWidget, updateStatusWidget, finishedState, combineReports } from "./status.mjs";
import { installUploadWidget, refreshUploadWidget } from "./upload.mjs?v=1.15.1";
import { arrangeArchmage, updateArchmageControls, bindWorkflowEncoders } from "./archmage_ui.mjs?v=1.15.1";
import { installOpenAIKeyWidget, refreshOpenAIKeyWidget } from "./openai_key.mjs?v=1.19.1";

const labels = new Map();
const layoutFields = ["canvas_width", "canvas_height", "layout_json"];
const guardedSlots = new WeakSet();

function updateLayoutSockets(node, layout) {
    for (const slot of node.inputs || []) {
        if (!layoutFields.includes(slot.name)) continue;
        slot.dartInactive = !layout;
        // Keep slot indices and existing links intact. Native widget hiding alone
        // still paints compatible/connected sockets during a drag.
        if (guardedSlots.has(slot)) continue;
        guardedSlots.add(slot);
        for (const method of ["draw", "drawCollapsed", "isValidTarget"]) {
            const original = slot[method];
            if (typeof original !== "function") continue;
            slot[method] = function (...args) {
                if (this.dartInactive) return method === "isValidTarget" ? false : undefined;
                return original.apply(this, args);
            };
        }
    }
}

function updateDescribeControls(node) {
    const batch = node.widgets?.find((widget) => widget.name === "batch_mode");
    if (batch) {
        const control = node.widgets.find(widget => widget.name === "control_after_generate");
        node.properties ||= {};
        if (control && batch.value === "All selected images as list" && control.value !== "fixed") {
            node.properties.atelier_queue_index_control = control.value;
            control.value = "fixed";
        } else if (control && batch.value === "One image per queued run" && node.properties.atelier_queue_index_control) {
            control.value = node.properties.atelier_queue_index_control;
            delete node.properties.atelier_queue_index_control;
        }
        for (const widget of node.widgets || []) {
            if (widget.name === "custom_folder") widget.hidden = node.widgets.find(item => item.name === "folder")?.value !== "Custom folder";
            if (["index", "wrap_index", "control_after_generate"].includes(widget.name)) widget.hidden = batch.value !== "One image per queued run";
            if (widget.name === "max_images") widget.hidden = batch.value === "One image per queued run";
        }
    }
    const recipe = node.widgets?.some((widget) => widget.name === "custom_overrides");
    if (recipe) {
        for (const widget of node.widgets || []) {
            if (widget.name.endsWith("_custom")) {
                const selector = node.widgets.find((item) => item.name === widget.name.slice(0, -7));
                widget.hidden = selector?.value !== (widget.name === "subject_custom" ? "Custom subject" : "Custom");
            }
        }
    }
    const server = node.widgets?.find((widget) => widget.name === "backend")?.value === "Chat server";
    const layout = node.widgets?.find((widget) => ["target", "output_format"].includes(widget.name))?.value === "MOSS JSON layout";
    const manual = node.widgets?.find((widget) => widget.name === "dimension_source")?.value;
    const canvas = layout && (!manual || manual === "Manual canvas");
    for (const widget of node.widgets || []) {
        if (["endpoint", "model", "timeout", "api_key_env"].includes(widget.name)) widget.hidden = !server;
        if (widget.name === "local_model") widget.hidden = server;
        if (layoutFields.includes(widget.name)) widget.hidden = !canvas;
        if (widget.name === "dimension_source") widget.hidden = !layout;
        if (["resize_mode", "resize_method"].includes(widget.name)) widget.hidden = node.widgets?.find((item) => item.name === "image_megapixels")?.value === 0;
    }
    if ((node.comfyClass || node.type || '').endsWith('ImageBatchUpload')) {
        const manual = node.properties?.mage_manual_upload_controls === true;
        for (const widget of node.widgets || []) {
            if (widget.name === 'batch_mode') widget.hidden = !manual;
            if (['batch_mode','index','wrap_index','max_images','control_after_generate'].includes(widget.name) && !manual) widget.hidden = true;
            if (widget.name === 'batch_run_id') widget.hidden = true;
        }
    }
    updateLayoutSockets(node, canvas);
    updateArchmageControls(node);
    refreshOpenAIKeyWidget(node);
    refreshDeepSeekKeyWidget(node);
    updateDesignBackend(node, server);
    const size = node.computeSize();
    node.setSize([Math.max(420, node.size[0], size[0]), size[1]]);
    node.setDirtyCanvas(true, true);
}

app.registerExtension({
    name: "Dart.ConnectionsAndPreview",
    beforeRegisterNodeDef(nodeType, nodeData) {
        labels.set(nodeData.name, nodeData.display_name || nodeData.name);
        if (!nodeData.name.startsWith("DanbooruTagsTransformer")) return;
        const baseCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            baseCreated?.apply(this, arguments);
            installDesign(this, nodeData);
            for (const widget of this.widgets || []) {
                const spec = nodeData.input?.required?.[widget.name] || nodeData.input?.optional?.[widget.name];
                const tip = spec?.[1]?.tooltip;
                if (tip) widget.tooltip = tip;
                if (widget.name === "control_after_generate") widget.tooltip = /ImageBatch(Selector|Upload)$/.test(nodeData.name)
                    ? "increment selects the next image for the next queued run; fixed repeats the index. Wrap index controls what happens at the end of the folder."
                    : "fixed keeps the seed; increment/decrement changes it by one; randomize picks a new seed for the next run. Deterministic modes may still produce the same text.";
            }
            if (nodeData.name.endsWith('Resolution')) {
                for (const name of ['aspect_ratio']) {
                    const widget = this.widgets?.find(item => item.name === name);
                    if (widget) { const callback = widget.callback; widget.callback = (...args) => {callback?.apply(widget, args); updateDescribeControls(this);}; }
                }
                updateDescribeControls(this);
            }
        };
        const baseConfigured = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            baseConfigured?.apply(this, arguments);
            configureDesign(this);
            if (nodeData.name.endsWith('Resolution')) updateDescribeControls(this);
        };
        const baseExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function () {
            baseExecuted?.apply(this, arguments);
            setDesignState(this, "done");
        };
        const baseMenu = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (_, options) {
            baseMenu?.apply(this, arguments);
            options.push({ content: this.properties.dart_design === false ? "Enable Mage design" : "Disable Mage design", callback: () => toggleDesign(this) });
            options.push({ content: this.properties.atelier_theme === "studio" ? "Use Ember theme (fire while running)" : "Use Studio theme", callback: () => { toggleTheme(this); refreshUploadWidget(this); } });
            if (nodeData.name.endsWith('ImageBatchUpload')) options.push({content: this.properties.mage_manual_upload_controls ? 'Hide advanced manual image controls' : 'Show advanced manual image controls', callback: () => {this.properties.mage_manual_upload_controls = !this.properties.mage_manual_upload_controls; updateDescribeControls(this);}});
        };
        if (!["DanbooruTagsTransformerDescribeImage", "DanbooruTagsTransformerImageToText", "DanbooruTagsTransformerAppearanceOverrides", "DanbooruTagsTransformerImageBatchSelector", "DanbooruTagsTransformerImageBatchUpload", "DanbooruTagsTransformerTagComposer", "DanbooruTagsTransformerSceneComposer", "DanbooruTagsTransformerArchmageBeta"].includes(nodeData.name)) return;
        const created = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            created?.apply(this, arguments);
            if (nodeData.name.endsWith("ImageBatchUpload")) installUploadWidget(this, api, app);
            if (nodeData.name.endsWith('ArchmageBeta')) { installOpenAIKeyWidget(this, api); installDeepSeekKeyWidget(this, api); }
            if (["DanbooruTagsTransformerDescribeImage", "DanbooruTagsTransformerImageToText", "DanbooruTagsTransformerTagComposer", "DanbooruTagsTransformerSceneComposer", "DanbooruTagsTransformerArchmageBeta"].includes(nodeData.name)) installStatusWidget(this);
            addTextPreviewWidgets(this);
            const preview = this.widgets?.find((widget) => widget.name === "preview_text");
            if (preview) preview.options.getMinHeight = () => 120;
            const names = { backend: "Assistant", local_model: "Local model", endpoint: "Server URL",
                model: "Chat model", keep_tags: "Keep exact tags", avoid: "Avoid",
                description: "Scene / keywords (optional with source tags)", custom_instructions: "Custom instructions",
                canvas_width: "MOSS canvas width", canvas_height: "MOSS canvas height", layout_json: "Edit MOSS JSON (optional override)",
                instructions: "Caption instructions / replacements", character_trigger: "Character trigger", image_index: "Image in batch",
                style_preset: "Style / theme", style_notes: "Custom style notes", reference_style: "Reference style", thinking: "Thinking mode", prompt_length: "Prompt length", output_format: "Output format", image_megapixels: "Image megapixel budget", dimension_source: "Layout dimensions", resize_mode: "Resize mode", resize_method: "Resize method", language_style: "Language style", max_tokens: "Generation token limit", unload_after_generation: "Unload assistant model after generation", trigger: "Character trigger", identity_mode: "Identity wording", custom_overrides: "Extra appearance replacements" };
            for (const widget of this.widgets || []) {
                if (/(SceneComposer|ArchmageBeta)$/.test(nodeData.name) && widget.name==='concepts') widget.label='Concepts (blank = surprise me)';
                else if (/(SceneComposer|ArchmageBeta)$/.test(nodeData.name) && widget.name==='instructions') widget.label='Scene instructions';
                else if (/Composer$/.test(nodeData.name) && widget.name==='seed') widget.label='Variation seed';
                else if (nodeData.name.endsWith('TagComposer') && widget.name==='idea') widget.label='Idea / seed tags (blank = random)';
                else if (widget.name === "apply_size_wording") widget.label = "Apply exact breast-size wording";
                else if (widget.name === "on_override_mismatch") widget.label = "On override mismatch";
                else if (widget.name === "strict_wording") widget.label = "Strict trait wording";
                else if (names[widget.name]) widget.label = names[widget.name];
                else if (nodeData.name.endsWith("AppearanceOverrides")) widget.label = widget.name.replaceAll("_", " ");
            }
            const appearanceSelectors = nodeData.name.endsWith("AppearanceOverrides") ? (this.widgets || []).filter((widget) => widget.type === "combo").map((widget) => widget.name) : [];
            for (const name of ["backend", "target", "output_format", "dimension_source", "image_megapixels", "folder", "batch_mode", "canvas_source", "aspect_ratio", "assistant_backend", ...appearanceSelectors]) {
                const control = this.widgets?.find((widget) => widget.name === name);
                if (!control) continue;
                const callback = control.callback;
                control.callback = (...args) => {
                    callback?.apply(control, args);
                    updateDescribeControls(this);
                };
            }
            this.mageCanonicalWidgets = (this.widgets || []).filter(widget => widget.serialize !== false);
            this.mageWidgetDefaults = new Map(this.mageCanonicalWidgets.map(widget => [widget.name, widget.value]));
            arrangeArchmage(this);
            if (nodeData.name.endsWith('AppearanceOverrides')) {
                const gender = this.widgets.filter(widget => ['gender', 'gender_custom'].includes(widget.name));
                this.widgets = this.widgets.filter(widget => !gender.includes(widget));
                const index = this.widgets.findIndex(widget => widget.name === 'identity_mode');
                this.widgets.splice(index + 1, 0, ...gender);
            }
            updateDescribeControls(this);
            refreshUploadWidget(this);
        };
        const slotAt = nodeType.prototype.getSlotInPosition;
        if (slotAt) nodeType.prototype.getSlotInPosition = function (...args) {
            const found = slotAt.apply(this, args);
            return found?.input?.dartInactive ? null : found;
        };
        const configured = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (data) {
            if (['DanbooruTagsTransformerGenerate','DanbooruTagsTransformerArchmageBeta'].includes(nodeData.name) && this.addInput && !this.inputs?.some(slot=>slot.name==='filters')) {
                this.addInput('filters','MAGE_TAG_FILTERS',{shape:7,tooltip:'Shared recipe from Prompt Mage Tag Filters.'});
            }
            configured?.apply(this, arguments);
            if (nodeData.name.endsWith('ArchmageBeta') && this.addInput && !this.inputs?.some(slot=>slot.name==='source_tags')) {
                this.addInput('source_tags','STRING',{shape:7,tooltip:'Optional DART scene ideas. Character, style and explicit instructions take priority.'});
            }
            if (nodeData.name === "DanbooruTagsTransformerImageToText" && this.addOutput) {
                for (const [name, type] of [["width", "INT"], ["height", "INT"], ["image", "IMAGE"], ["status", "STRING"], ["report", "STRING"]]) {
                    if (!this.outputs?.some((slot) => slot.name === name)) this.addOutput(name, type);
                }
            }
            if (nodeData.name === "DanbooruTagsTransformerDescribeImage" && this.addOutput) {
                for (const name of ["status", "report"]) {
                    if (!this.outputs?.some((slot) => slot.name === name)) this.addOutput(name, "STRING");
                }
            }
            // Persist by name so converted inputs and UI-only widgets cannot shift settings.
            const named = data?.dart_widget_values || data?.widgets_values_named;
            if (named) {
                for (const widget of this.widgets || []) {
                    if (widget.serialize !== false) {
                        if (Object.hasOwn(named, widget.name)) widget.value = named[widget.name];
                        else if (this.mageWidgetDefaults?.has(widget.name)) widget.value = this.mageWidgetDefaults.get(widget.name);
                    }
                }
            }
            else if (this.mageCanonicalWidgets && Array.isArray(data?.widgets_values)) {
                this.mageCanonicalWidgets.forEach((widget, i) => {
                    if (i < data.widgets_values.length) widget.value = data.widgets_values[i];
                    else widget.value = this.mageWidgetDefaults.get(widget.name);
                });
            }
            if (nodeData.name.endsWith('AppearanceOverrides') && !Object.hasOwn(named || {}, 'gender') &&
                (named || (data?.widgets_values?.length || 0) < this.mageCanonicalWidgets?.length)) {
                const gender = this.widgets.find(widget => widget.name === 'gender');
                if (gender) gender.value = 'Keep unchanged';
            }
            updateDescribeControls(this);
            refreshUploadWidget(this);
        };
        const serialized = nodeType.prototype.onSerialize;
        nodeType.prototype.onSerialize = function (data) {
            serialized?.apply(this, arguments);
            data.dart_widget_values = Object.fromEntries((this.widgets || [])
                .filter((widget) => widget.serialize !== false).map((widget) => [widget.name, widget.value]));
            if (this.mageCanonicalWidgets) data.widgets_values = this.mageCanonicalWidgets.map(widget => widget.value);
        };
        const connectionsChanged = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function () {
            connectionsChanged?.apply(this, arguments);
            updateDescribeControls(this);
        };
        const executed = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            executed?.apply(this, arguments);
            if (message?.mage_report?.[0]) {
                const r=message.mage_report[0];
                const beta=(this.comfyClass || this.type || '').endsWith('ArchmageBeta');
                const scene=beta || (this.comfyClass || this.type || '').endsWith('SceneComposer');
                const edits=scene && r.post_edits?.length ? '\nSelected size wording was post-edited by Prompt Mage; original model text is retained in the report.' : '';
                updateStatusWidget(this,{...r,has_appearance:true,title:beta ? (r.status==='ok'?'Archmage: ready':r.status==='blocked'?'Archmage: output blocked':'Archmage: review notes') : scene ? (r.status==='ok'?'Scene generated':'Scene Composer: review notes') : (r.status==='ok'?'Tags vocabulary-checked':'Tag Composer: review notes'),message:(r.issues.join('\n') || (scene ? r.note : 'Dataset tag membership checked; semantic correctness remains model-guided.'))+edits,issues:[]});
                setDesignState(this, finishedState(this));
            }
            if (message?.atelier_report?.[0]) {
                updateStatusWidget(this, combineReports(message.atelier_report));
                setDesignState(this, finishedState(this));
            }
            const json = message?.moss_json?.[0] === true || message?.json_preview?.[0] === true;
            const mode = this.widgets?.find((widget) => widget.name === "preview_mode");
            // Markdown is a preview choice only: output wires always contain raw JSON.
            if (json && !this.properties.dart_seen_json_preview && mode) {
                mode.value = true;
                this.properties.dart_seen_json_preview = true;
            }
            this.dartPreviewMessage = message;
            const refresh = () => {
                const current = this.dartPreviewMessage;
                const formatted = (current?.moss_json?.[0] || current?.json_preview?.[0]) && mode?.value;
                updateTextPreviewWidgets(this, formatted ? {
                    ...current, text: (current.text || []).map((text) => "```json\n" + text + "\n```"),
                } : current);
            };
            if (mode && !mode.dartRefreshInstalled) {
                const callback = mode.callback;
                mode.callback = (...args) => { callback?.apply(mode, args); refresh(); };
                mode.dartRefreshInstalled = true;
            }
            refresh();
        };
    },
    setup() {
        if (app.graphToPrompt) {
            const originalPrompt = app.graphToPrompt;
            app.graphToPrompt = async function (...args) {
                return bindWorkflowEncoders(await originalPrompt.apply(this, args));
            };
        }
        let activeNode;
        api.addEventListener("executing", ({ detail }) => {
            if (activeNode) setDesignState(activeNode, finishedState(activeNode));
            const id = detail && typeof detail === "object" ? detail.node : detail;
            activeNode = id != null ? app.graph.getNodeById(id) : null;
            if (activeNode) {
                setDesignState(activeNode, "running");
                if (activeNode.atelierLastReport?.has_appearance) updateStatusWidget(activeNode, {
                    status: "running", has_appearance: true, message: /Composer$/.test(activeNode.comfyClass || activeNode.type || "") ? "Generating a new scene and checking the output." : "Generating text and checking the selected appearance wording.", issues: [],
                });
            }
        });
        for (const event of ["execution_error", "execution_interrupted"]) {
            api.addEventListener(event, ({detail} = {}) => {
                if (activeNode) {
                    setDesignState(activeNode, "error");
                    updateStatusWidget(activeNode, {status: "error", has_appearance: true,
                        message: detail?.exception_message || "Generation was interrupted or failed. Open ComfyUI's execution details for the cause.", issues: []});
                }
                activeNode = null;
            });
        }
        const canvas = app.canvas;
        const original = canvas.showConnectionMenu;
        canvas.showConnectionMenu = function (options) {
            const source = options?.nodeFrom || options?.nodeTo;
            if (!source || options.afterRerouteId != null) return original.apply(this, arguments);
            const isOutput = Boolean(options.nodeFrom);
            const { index, slot } = resolveSlot(isOutput ? source.outputs : source.inputs,
                isOutput ? options.slotFrom : options.slotTo);
            if (!slot) return original.apply(this, arguments);
            const candidates = connectionsFor(source.comfyClass || source.type, slot.name, slot.type, isOutput)
                .filter(({ type }) => LiteGraph.registered_node_types[type]);
            if (!candidates.length) return original.apply(this, arguments);
            const position = this.convertEventToCanvasOffset(options.e);
            const graph = source.graph;
            const entries = candidates.map(({ type, slot: targetSlot }) => ({
                content: labels.get(type) || LiteGraph.registered_node_types[type].title || type,
                callback: () => {
                    const next = LiteGraph.createNode(type);
                    graph.beforeChange();
                    try {
                        graph.add(next);
                        next.pos = position;
                        let targetIndex = typeof targetSlot === "number" ? targetSlot : next.findInputSlot(targetSlot);
                        if (isOutput && targetIndex < 0) {
                            const widget = next.widgets?.find((widget) => widget.name === targetSlot);
                            if (widget) convertToInput(next, widget);
                            targetIndex = next.findInputSlot(targetSlot);
                        }
                        if (isOutput) {
                            source.connect(index, next, targetIndex);
                            if (/ImageBatch(Selector|Upload)$/.test(source.comfyClass || source.type) && slot.name === "image" && ["DanbooruTagsTransformerImageToText","DanbooruTagsTransformerArchmageBeta"].includes(type)) {
                                const nameSlot = next.findInputSlot("source_name");
                                if (nameSlot >= 0) source.connect(1, next, nameSlot);
                            }
                        }
                        else {
                            next.connect(targetIndex, source, index);
                            if (/ImageBatch(Selector|Upload)$/.test(type) && slot.name === "image" && ["DanbooruTagsTransformerImageToText","DanbooruTagsTransformerArchmageBeta"].includes(source.comfyClass || source.type)) {
                                const nameSlot = source.findInputSlot("source_name");
                                if (nameSlot >= 0) next.connect(1, source, nameSlot);
                            }
                        }
                    } finally {
                        graph.afterChange();
                    }
                    this.setDirty(true, true);
                },
            }));
            entries.push(null, { content: "More compatible nodes…", callback: () => original.call(this, options) });
            return new LiteGraph.ContextMenu(entries, { event: options.e, title: `${slot.name} | ${slot.type}` });
        };
    },
});
import './grimoire.mjs?v=1.19.1';
