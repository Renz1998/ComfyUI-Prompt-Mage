import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { connectionsFor, resolveSlot } from "../web/connections.mjs";
import { arrangeArchmage, updateArchmageControls, bindWorkflowEncoders } from "../web/archmage_ui.mjs";
import { combineReports } from "../web/status.mjs";

let extension, menu, previewMessage;
const connections = [];
const graph = { beforeChange() {}, afterChange() {}, add(node) { node.graph = this; } };
class Canvas {
    showConnectionMenu() { return "original"; }
    convertEventToCanvasOffset() { return [100, 200]; }
    setDirty() {}
}
const context = {
    app: { canvas: new Canvas(), registerExtension(value) { extension = value; } },
    api: { addEventListener() {} },
    installDesign() {}, configureDesign() {}, toggleDesign() {}, toggleTheme() {}, setDesignState() {}, updateDesignBackend() {},
    installStatusWidget() {}, updateStatusWidget(node, report) {node.atelierLastReport=report;}, finishedState(node) {return node.atelierLastReport?.status || 'done';},
    combineReports, arrangeArchmage, updateArchmageControls, bindWorkflowEncoders,
    installUploadWidget() {}, refreshUploadWidget() {},
    installDeepSeekKeyWidget() {}, refreshDeepSeekKeyWidget() {}, installOpenAIKeyWidget() {}, refreshOpenAIKeyWidget() {},
    connectionsFor, resolveSlot, LGraphCanvas: Canvas,
    addTextPreviewWidgets() {}, updateTextPreviewWidgets(node, message) { previewMessage = message; }, convertToInput() {},
    LiteGraph: {
        registered_node_types: {
            CLIPTextEncode: { title: "CLIP Text Encode" }, PreviewAny: { title: "Preview as Text" },
            DanbooruTagsTransformerComposePromptV3: { title: "Dart Compose Prompt V3" },
            DanbooruTagsTransformerLoaderV3: { title: "Dart v3 Load" },
            DanbooruTagsTransformerDescribeImage: { title: "Dart Describe Image" },
            DanbooruTagsTransformerAppearanceOverrides: { title: "Prompt Mage · Appearance Overrides" },
            DanbooruTagsTransformerImageToText: {title:"Prompt Mage · Image to Text"},
            DanbooruTagsTransformerArchmageBeta: {title:"Prompt Mage · Archmage (Beta)"},
            DanbooruTagsTransformerSceneComposer: {title:"Prompt Mage · Scene Composer"},
            DanbooruTagsTransformerTagComposer: {title:"Prompt Mage · Tag Composer (Experimental)"},
            DanbooruTagsTransformerImageBatchSelector: {title:"Prompt Mage · Server Folder (Advanced)"},
            DanbooruTagsTransformerImageBatchUpload: {title:"Prompt Mage · Upload Images"},
        },
        ContextMenu: class { constructor(entries) { menu = entries; } },
        createNode(type) {
            return { type, inputs: ['DanbooruTagsTransformerImageToText','DanbooruTagsTransformerArchmageBeta'].includes(type) ? [{name:'image'},{name:'source_name'},{name:'source_tags'}] : [{ name: "text" }, { name: "general" }, { name: "source_tags" }],
                findInputSlot(name) { return this.inputs.findIndex((slot) => slot.name === name); },
                connect(...args) { connections.push({ from: type, args }); } };
        },
    },
};
vm.runInNewContext(readFileSync(new URL("../web/dart.js", import.meta.url), "utf8").replace(/^import .*;\r?\n/gm, ""), context);
extension.setup();
const canvas = context.app.canvas;
const source = { type: "DanbooruTagsTransformerDescribeImage", graph,
    outputs: [{ name: "prompt", type: "STRING" }, { name: "general_tags", type: "STRING" }],
    connect(...args) { connections.push({ from: "describe", args }); } };
canvas.showConnectionMenu({ nodeFrom: source, slotFrom: 0, e: {} });
assert.equal(menu[0].content, "CLIP Text Encode");
menu[0].callback();
assert.equal(connections[0].args[0], 0);
assert.equal(connections[0].args[1].type, "CLIPTextEncode");
assert.equal(connections[0].args[2], 0);
canvas.showConnectionMenu({ nodeFrom: source, slotFrom: source.outputs[1], e: {} });
assert.equal(menu[0].content, "Dart Compose Prompt V3");
menu[0].callback();
assert.equal(connections[1].args[2], 1); // The actual general input, not an arbitrary STRING.
const target = { type: "DanbooruTagsTransformerGenerate", graph, inputs: [{ name: "tokenizer", type: "DART_TOKENIZER" }] };
canvas.showConnectionMenu({ nodeTo: target, slotTo: 0, e: {} });
menu[0].callback();
assert.equal(connections[2].from, "DanbooruTagsTransformerLoaderV3");
assert.equal(connections[2].args[0], 1); // Loader's tokenizer output, not its model output.
assert.equal(connections[2].args[2], 0);
assert.equal(canvas.showConnectionMenu({ nodeFrom: { ...source, type: "OtherPlugin" }, slotFrom: 0, e: {} }), "original");
canvas.showConnectionMenu({ nodeFrom: { ...source, type: "DanbooruTagsTransformerGenerate" }, slotFrom: 0, e: {} });
assert.equal(menu[0].content, "Prompt Mage · Archmage (Beta)");
menu[0].callback();
assert.equal(connections[3].args[1].type, "DanbooruTagsTransformerArchmageBeta");
assert.equal(connections[3].args[2], 2); // source_tags, not description or another STRING.
class Describe {
    constructor() {
        this.size = [380, 500];
        this.properties = {};
        this.inputs = ["canvas_width", "canvas_height", "layout_json"].map((name) => ({name,
            link: 123, draw() { return "drawn"; }, isValidTarget() { return true; }}));
        this.widgets = ["backend", "local_model", "endpoint", "model", "timeout", "api_key_env", "keep_tags", "avoid", "target", "canvas_width", "canvas_height", "layout_json", "preview_mode"]
            .map((name) => ({ name, value: name === "backend" ? "Local model" : "" }));
    }
    setSize(size) { this.size = size; }
    computeSize() { return [400, 500]; }
    setDirtyCanvas() {}
    getSlotInPosition() { return {input: this.inputs[0]}; }
}
extension.beforeRegisterNodeDef(Describe, {name: "DanbooruTagsTransformerDescribeImage"});
const describeNode = new Describe();
describeNode.onNodeCreated();
assert.equal(describeNode.widgets.find((w) => w.name === "endpoint").hidden, true);
assert.equal(describeNode.widgets.find((w) => w.name === "local_model").hidden, false);
const backend = describeNode.widgets.find((w) => w.name === "backend");
backend.value = "Chat server";
backend.callback("Chat server");
assert.equal(describeNode.widgets.find((w) => w.name === "endpoint").hidden, false);
assert.equal(describeNode.widgets.find((w) => w.name === "local_model").hidden, true);
assert.equal(backend.label, "Assistant");
assert.equal(describeNode.size[0], 420);
assert.equal(describeNode.widgets.find((w) => w.name === "canvas_width").hidden, true);
assert.equal(describeNode.inputs[0].draw(), undefined);
assert.equal(describeNode.inputs[0].isValidTarget(), false);
assert.equal(describeNode.getSlotInPosition(), null);
const targetControl = describeNode.widgets.find((w) => w.name === "target");
targetControl.value = "MOSS JSON layout";
targetControl.callback("MOSS JSON layout");
assert.equal(describeNode.widgets.find((w) => w.name === "canvas_width").hidden, false);
assert.equal(describeNode.widgets.find((w) => w.name === "layout_json").hidden, false);
assert.equal(describeNode.inputs[0].draw(), "drawn");
assert.equal(describeNode.inputs[0].isValidTarget(), true);
assert.equal(describeNode.inputs[0].link, 123);
assert.equal(describeNode.getSlotInPosition().input.name, "canvas_width");
describeNode.onExecuted({text: ['{\n  "summary": {}\n}'], moss_json: [true]});
assert.equal(previewMessage.text[0], '```json\n{\n  "summary": {}\n}\n```');
const previewMode = describeNode.widgets.find((w) => w.name === "preview_mode");
previewMode.value = false;
previewMode.callback();
assert.equal(previewMessage.text[0], '{\n  "summary": {}\n}');
targetControl.value = "Natural language";
targetControl.callback("Natural language");
assert.equal(describeNode.widgets.find((w) => w.name === "layout_json").hidden, true);
describeNode.widgets.find((w) => w.name === "local_model").value = "Automatic";
const saved = {};
describeNode.onSerialize(saved);
describeNode.widgets.find((w) => w.name === "local_model").value = "shifted value";
describeNode.onConfigure(saved);
assert.equal(describeNode.widgets.find((w) => w.name === "local_model").value, "Automatic");
// The vision node shares JSON preview handling and uses auto/manual canvas controls.
targetControl.name = "output_format";
targetControl.value = "MOSS JSON layout";
describeNode.widgets.push({name: "dimension_source", value: "From processed image"});
targetControl.callback();
assert.equal(describeNode.widgets.find((w) => w.name === "canvas_width").hidden, true);
assert.equal(describeNode.inputs[0].isValidTarget(), false);
describeNode.widgets.find((w) => w.name === "dimension_source").value = "Manual canvas";
targetControl.callback();
assert.equal(describeNode.widgets.find((w) => w.name === "canvas_width").hidden, false);
previewMode.value = true;
describeNode.onExecuted({text: ['{"description":"scene"}'], json_preview: [true]});
assert.equal(previewMessage.text[0], '```json\n{"description":"scene"}\n```');
class OldVision {
    constructor() { this.outputs = [{name: "description", type: "STRING", links: [99]}]; this.widgets = []; this.size = [420,500]; }
    addOutput(name, type) { this.outputs.push({name, type}); }
    computeSize() { return this.size; }
    setSize(size) { this.size = size; }
    setDirtyCanvas() {}
}
extension.beforeRegisterNodeDef(OldVision, {name: "DanbooruTagsTransformerImageToText"});
const oldVision = new OldVision();
oldVision.onConfigure({});
assert.deepEqual(oldVision.outputs.map((slot) => slot.name), ["description", "width", "height", "image", "status", "report"]);
assert.deepEqual(oldVision.outputs[0].links, [99]);
oldVision.onConfigure({});
assert.equal(oldVision.outputs.length, 6);
canvas.showConnectionMenu({nodeTo: {type:'DanbooruTagsTransformerImageToText',graph,inputs:[{name:'appearance',type:'ATELIER_APPEARANCE'}]},slotTo:0,e:{}});
assert.equal(menu[0].content, 'Prompt Mage · Appearance Overrides');
menu[0].callback();
assert.equal(connections.at(-1).from, 'DanbooruTagsTransformerAppearanceOverrides');
assert.equal(connections.at(-1).args[0], 0);
assert.equal(connections.at(-1).args[2], 0);
class Recipe {
    constructor() {
        this.size=[420,500]; this.properties={};
        this.widgets=[{name:'hair_color',type:'combo',value:'Keep unchanged'},{name:'hair_color_custom',value:''},
            {name:'subject',type:'combo',value:'Main subject'},{name:'subject_custom',value:''},{name:'custom_overrides',value:''}];
    }
    computeSize(){return this.size;} setSize(size){this.size=size;} setDirtyCanvas(){}
}
extension.beforeRegisterNodeDef(Recipe, {name:'DanbooruTagsTransformerAppearanceOverrides'});
const recipe=new Recipe(); recipe.onNodeCreated();
assert.equal(recipe.widgets[1].hidden,true);
recipe.widgets[0].value='Custom'; recipe.widgets[0].callback();
assert.equal(recipe.widgets[1].hidden,false);
recipe.widgets[2].value='Custom subject'; recipe.widgets[2].callback();
assert.equal(recipe.widgets[3].hidden,false);
console.log("Drag menus create and connect the intended node sockets; other plugins retain their menu.");
const batchSource={type:'DanbooruTagsTransformerImageBatchSelector',graph,outputs:[{name:'image',type:'IMAGE'},{name:'filename',type:'STRING'}],connect(...args){connections.push({from:'batch',args});}};
canvas.showConnectionMenu({nodeFrom:batchSource,slotFrom:0,e:{}});
menu[0].callback();
assert.equal(connections.at(-2).args[0],0);
assert.equal(connections.at(-2).args[2],0);
assert.equal(connections.at(-1).args[0],1);
assert.equal(connections.at(-1).args[2],1);
batchSource.type='DanbooruTagsTransformerImageBatchUpload';
canvas.showConnectionMenu({nodeFrom:batchSource,slotFrom:0,e:{}});menu[0].callback();
assert.equal(connections.at(-1).args[0],1);
const captionTarget={type:'DanbooruTagsTransformerImageToText',graph,inputs:[{name:'image',type:'IMAGE'},{name:'source_name',type:'STRING'}],findInputSlot(name){return this.inputs.findIndex(slot=>slot.name===name);}};
canvas.showConnectionMenu({nodeTo:captionTarget,slotTo:0,e:{}});
const uploadChoice=menu.find(entry=>entry?.content==='Prompt Mage · Upload Images');assert.ok(uploadChoice);uploadChoice.callback();
assert.equal(connections.at(-2).args[0],0);assert.equal(connections.at(-2).args[2],0);
assert.equal(connections.at(-1).args[0],1);assert.equal(connections.at(-1).args[2],1);
canvas.showConnectionMenu({nodeTo:{type:'DanbooruTagsTransformerSceneComposer',graph,inputs:[{name:'appearance',type:'ATELIER_APPEARANCE'}]},slotTo:0,e:{}});
assert.ok(menu[0].content.includes('Appearance'));menu[0].callback();
assert.equal(connections.at(-1).from,'DanbooruTagsTransformerAppearanceOverrides');
assert.equal(connections.at(-1).args[0],0);assert.equal(connections.at(-1).args[2],0);

// Beta retains canvas context widgets and sockets in both output formats.
class Beta {
    constructor(){
        this.type='DanbooruTagsTransformerArchmageBeta';this.size=[420,600];this.properties={};
        this.widgets=[{name:'output_format',value:'Prose'},{name:'width',value:768},{name:'height',value:1024},{name:'canvas_source',value:'Manual'}];
        this.inputs=[{name:'width',type:'INT',link:123}];
    }
    setSize(size){this.size=size;} computeSize(){return [420,600];} setDirtyCanvas(){}
    addCustomWidget(widget){this.widgets.push(widget);return widget;}
    addInput(name,type,options){const slot={name,type,...options};this.inputs.push(slot);return slot;}
}
globalThis.document = {createElement(){return {};}};
extension.beforeRegisterNodeDef(Beta,{name:'DanbooruTagsTransformerArchmageBeta'});
const betaNode=new Beta();betaNode.onNodeCreated();
for(const mode of ['MOSS JSON layout','Prose']){
    const format=betaNode.widgets.find(w=>w.name==='output_format');format.value=mode;format.callback();
    assert.notEqual(betaNode.widgets.find(w=>w.name==='width').hidden,true);assert.notEqual(betaNode.widgets.find(w=>w.name==='height').hidden,true);
    assert.notEqual(betaNode.inputs[0].dartInactive,true);assert.equal(betaNode.inputs[0].link,123);
}
const savedBeta={};betaNode.onSerialize(savedBeta);
assert.deepEqual(Array.from(savedBeta.widgets_values),['Prose',768,1024,'Manual']);
betaNode.onConfigure({widgets_values:['MOSS JSON layout',1568,2368,'Manual']});
assert.equal(betaNode.widgets.find(w=>w.name==='width').value,1568);
assert.equal(betaNode.inputs.at(-1).name,'source_tags');
assert.equal(betaNode.inputs[0].link,123);
betaNode.onConfigure({dart_widget_values:savedBeta.dart_widget_values});
assert.equal(betaNode.widgets.find(w=>w.name==='width').value,768);
// A newly introduced control must not inherit a positional preview value from an old graph.
betaNode.mageWidgetDefaults.set('memory_mode','Automatic');
betaNode.widgets.push({name:'memory_mode',value:false});
betaNode.onConfigure({dart_widget_values:savedBeta.dart_widget_values});
assert.equal(betaNode.widgets.find(w=>w.name==='memory_mode').value,'Automatic');
betaNode.onExecuted({text:['Schema error'],mage_report:[{status:'blocked',issues:['Schema error'],post_edits:[]}]});
assert.equal(betaNode.atelierLastReport.title,'Archmage: output blocked');
assert.equal(betaNode.atelierLastReport.message,'Schema error');

class UploadControls {
    constructor(){this.type='DanbooruTagsTransformerImageBatchUpload';this.properties={};this.size=[420,600];this.inputs=[];
        this.widgets=[{name:'batch_mode',value:'One image per queued run'},{name:'index',value:99},{name:'wrap_index',value:true},{name:'max_images',value:16},{name:'control_after_generate',value:'increment'},{name:'batch_run_id',value:''}];}
    setSize(size){this.size=size;} computeSize(){return [420,600];} setDirtyCanvas(){}
}
extension.beforeRegisterNodeDef(UploadControls,{name:'DanbooruTagsTransformerImageBatchUpload'});
const uploadControls=new UploadControls();uploadControls.onNodeCreated();
assert.ok(uploadControls.widgets.every(w=>w.hidden));
const uploadOptions=[];uploadControls.getExtraMenuOptions(null,uploadOptions);
uploadOptions.find(o=>o.content==='Show advanced manual image controls').callback();
assert.equal(uploadControls.widgets[0].hidden,false);assert.equal(uploadControls.widgets[1].hidden,false);
assert.equal(uploadControls.widgets[5].hidden,true);
