import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {ensureCanvasInputs} from '../web/grimoire_sockets.mjs';
import {layoutGrimoire} from '../web/grimoire_layout.mjs';
import {chatPrompt,queueChat} from '../web/grimoire_queue.mjs';
import {renderMarkdown} from '../web/grimoire_markdown.mjs';
class Element {
    constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.style={};this.value='';}
    append(...items){this.children.push(...items);}
    replaceChildren(){this.children=[];}
    setAttribute(name,value){this[name]=value;}
    addEventListener(name,fn){this.listeners[name]=fn;}
}
let queued=0,copied='',imageJobs=0,job,applied=[],edits=[];
const snapshot={output:{7:{class_type:'DanbooruTagsTransformerGrimoire',inputs:{}},8:{class_type:'SaveImage',inputs:{images:['7',0]}}},workflow:{nodes:[]}};
const context={ensureCanvasInputs,layoutGrimoire,chatPrompt,queueChat,renderMarkdown,document:{createElement:tag=>new Element(tag)},crypto:{getRandomValues:bytes=>bytes.fill(7)},
    navigator:{clipboard:{async writeText(value){copied=value;}}},window:{confirm:()=>true},
    app:{registerExtension(){},async graphToPrompt(){return snapshot;},async queuePrompt(){imageJobs++;}},api:{async queuePrompt(index,value){queued++;job=value;return {prompt_id:'test-job'};},async fetchApi(path,options){if(path.endsWith('/capabilities'))return {ok:true,async json(){return {partial_execution:true};}};assert.equal(options.method,'POST');if(path==='/prompt'){queued++;const body=JSON.parse(options.body);job={output:body.prompt};assert.deepEqual(body.partial_execution_targets,['7']);return {ok:true,async json(){return {prompt_id:'test-job'};}};}return {ok:true,async json(){if(path.endsWith('/message')){const body=JSON.parse(options.body);edits.push(body);return {turns:[{role:'user',content:'Edited question'},{role:'assistant',content:body.text}],summary:''};}if(path.endsWith('/scroll')){const body=JSON.parse(options.body);if(body.apply)applied.push(body);return {active:null};}if(path.endsWith('/chats'))return {chats:[{id:'older-chat',title:'An older chat',updated:1,turns:2}]};return JSON.parse(options.body).id==='older-chat'?{turns:[{role:'assistant',content:'Saved answer'}],summary:'Saved summary',settings:{task_instructions:'Restored task'}}:{turns:[],summary:''};}};},addEventListener(){},removeEventListener(){}},
    installOpenAIKeyWidget(){},refreshOpenAIKeyWidget(){},installDeepSeekKeyWidget(){},refreshDeepSeekKeyWidget(){}};
vm.runInNewContext(readFileSync(new URL('../web/grimoire.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function','function'),context);
globalThis.document=context.document;
const node={inputs:[{name:'clip',link:23}],addInput(name,type,options){this.inputs.push({name,type,...options});},graph:{_nodes:[{type:'DanbooruTagsTransformerSpellScroll',widgets:[{name:'scroll_id',value:'main-scroll'}]}]},id:7,size:[650,900],widgets:['system_prompt','pinned_facts','task_instructions','message','conversation_id','action','assistant_backend','summary_override','openai_model','deepseek_model','local_model','chat_mode','style_preset','style_notes','edit_original','edit_index','output_selection'].map(name=>({name,value:name==='assistant_backend'?'Local Qwen':name==='chat_mode'?'Conversation':name==='style_preset'?'None (model choice)':'',options:name==='assistant_backend'?{values:['Local Qwen','OpenAI API','DeepSeek API']}:name==='style_preset'?{values:['None (model choice)','Photo · Bright lifestyle','Photo · Amateur Instagram']}:{}})),
    addDOMWidget(name,type,root,options){this.root=root;this.domOptions=options;this.chatWidget={serialize:options.serialize};return this.chatWidget;},computeSize(){return [650,680];},setSize(size){this.size=size;},setDirtyCanvas(){}};
context.installGrimoire(node);assert.deepEqual(node.inputs.map(s=>s.name),['clip','width','height']);node.inputs[1].hidden=true;node.inputs[1].widget={name:'width'};node.inputs[1].link=42;ensureCanvasInputs(node);assert.equal(node.inputs.length,3);assert.equal(node.inputs[1].hidden,false);assert.equal(node.inputs[1].widget,undefined);assert.equal(node.inputs[1].link,42);
await new Promise(resolve=>setTimeout(resolve,0));
assert.equal(node.widgets.find(w=>w.name==='conversation_id').value,'07070707070707070707070707070707');assert.equal(node.chatWidget.serialize,false);assert.equal(node.widgets.find(w=>w.name==='action').value,'Use latest');assert.equal(node.domOptions.getMinHeight(),560);assert.equal(node.domOptions.getMaxHeight,undefined);node.size=[800,1300];
function all(root){return [root,...root.children.flatMap(all)];}
const button=name=>all(node.root).find(e=>e.tag==='button'&&e.textContent===name);
const composer=all(node.root).find(e=>e['aria-label']==='Message Grimoire');
composer.value='Hello **Grimoire**';button('Send').listeners.click();await new Promise(resolve=>setTimeout(resolve,0));
assert.deepEqual(Array.from(node.size),[800,1300]);assert.equal(queued,1);assert.equal(imageJobs,0);assert.deepEqual(Object.keys(job.output),['7','8']);assert.equal(job.output['7'].inputs.action,'Send');assert.equal(job.output['7'].class_type,'DanbooruTagsTransformerGrimoireTurn');assert.equal(node.widgets.find(w=>w.name==='action').value,'Use latest');button('Send').listeners.click();assert.equal(queued,1);
node.onExecuted({grimoire:[{turns:[{role:'assistant',content:'<script>unsafe()</script>'}],summary:'Remember green cloak'}]});
assert.ok(all(node.root).some(e=>e.textContent==='<script>unsafe()</script>'));assert.equal(all(node.root).some(e=>e.tag==='script'),false);
const menu=all(node.root).find(e=>e['aria-label']==='Conversation actions');menu.value='Copy latest';await menu.listeners.change();assert.equal(copied,'<script>unsafe()</script>');
button('Edit summary').listeners.click();assert.equal(node.widgets.find(w=>w.name==='summary_override').value,'Remember green cloak');
assert.equal(button('Generate image'),undefined);assert.equal(imageJobs,0);button('Use this prompt').listeners.click();await new Promise(resolve=>setTimeout(resolve,0));assert.equal(applied.length,1);assert.equal(applied[0].text,'<script>unsafe()</script>');assert.equal(applied[0].scroll_id,'main-scroll');assert.equal(queued,1);
button('Settings').listeners.click();
const provider=all(node.root).find(e=>e['aria-label']==='Assistant provider');provider.value='DeepSeek API';provider.listeners.change();assert.equal(node.widgets.find(w=>w.name==='assistant_backend').value,'DeepSeek API');
assert.ok(node.widgets.every(w=>w.hidden));
const tree=new Element('div');renderMarkdown(tree,'# Title\n**Bold**\n```json\n{"x":1}\n```',value=>{copied=value;});assert.equal(tree.children[0].tag,'h1');tree.children[2].children[0].children[0].listeners.click();assert.equal(copied,'{"x":1}');
assert.throws(()=>chatPrompt({output:{7:{class_type:'DanbooruTagsTransformerGrimoire',inputs:{image:['9',0]}},9:{class_type:'KSampler',inputs:{}}}},7,'Send','hello'),/image generation/);
node.onExecuted({grimoire:[{turns:[],summary:''}]});const picker=all(node.root).find(e=>e['aria-label']==='Saved chats');picker.value='older-chat';picker.listeners.change();await new Promise(resolve=>setTimeout(resolve,0));assert.equal(node.widgets.find(w=>w.name==='conversation_id').value,'older-chat');assert.equal(node.widgets.find(w=>w.name==='task_instructions').value,'Restored task');
assert.deepEqual(Array.from(node.size),[800,1300]);assert.equal(node.widgets[0].computeLayoutSize().maxHeight,0);
const saved={};node.onSerialize(saved);node.size=[650,680];node.onConfigure(saved);await new Promise(resolve=>setTimeout(resolve,0));assert.deepEqual(Array.from(node.size),[800,1300]);
node.onExecuted({grimoire:[{turns:[{role:'user',content:'Original question'},{role:'assistant',content:'**A reply**'}],summary:''}]});
const message=role=>all(node.root).find(e=>e.className==='gm-message '+role);
const localButton=(element,name)=>all(element).find(e=>e.tag==='button'&&e.textContent===name);
await localButton(message('gm-user'),'Copy').listeners.click();assert.equal(copied,'Original question');assert.equal(queued,1);
localButton(message('gm-user'),'Edit').listeners.click();assert.equal(composer.value,'Original question');composer.value='Edited question';button('Send edited message').listeners.click();await new Promise(resolve=>setTimeout(resolve,0));assert.equal(queued,2);assert.equal(job.output['7'].inputs.action,'Edit message');assert.equal(job.output['7'].inputs.edit_original,'Original question');assert.equal(job.output['7'].inputs.edit_index,0);
node.onExecuted({grimoire:[{turns:[{role:'user',content:'Edited question'},{role:'assistant',content:'A reply'}],summary:''}]});
localButton(message('gm-assistant'),'Edit').listeners.click();all(message('gm-assistant')).find(e=>e.tag==='textarea').value='Manually improved reply';await button('Save edit (no API call)').listeners.click();assert.equal(edits.length,1);assert.equal(queued,2);assert.equal(edits[0].text,'Manually improved reply');
const raw=new Element('div');renderMarkdown(raw,'{"summary":{"caption":"A mug"}}');assert.equal(raw.children[0].tag,'section');assert.ok(all(raw).some(e=>e.tag==='pre'));
const rich=new Element('div');renderMarkdown(rich,'__Bold__ and _italic_\n- One\n- Two\n> Quote\n| A | B |\n| --- | --- |\n| x | y |');assert.ok(all(rich).some(e=>e.tag==='strong'));assert.ok(all(rich).some(e=>e.tag==='ul'));assert.ok(all(rich).some(e=>e.tag==='blockquote'));assert.ok(all(rich).some(e=>e.tag==='table'));
const remote=chatPrompt({output:{7:{class_type:'DanbooruTagsTransformerGrimoire',inputs:{assistant_backend:'DeepSeek API',clip:['9',0]}},9:{class_type:'CLIPLoader',inputs:{}},10:{class_type:'SaveImage',inputs:{}}}},7,'Send','Hi');assert.equal(remote.output['7'].inputs.clip,undefined);assert.ok(remote.output['9']);assert.ok(remote.output['10']);
let rejectedPosts=0;await assert.rejects(()=>queueChat({async fetchApi(path){if(path==='/prompt')rejectedPosts++;return {ok:true,async json(){return {partial_execution:false};}};}},remote,7),/Update/);assert.equal(rejectedPosts,0);
const legacyNames=['conversation_id','system_prompt','task_instructions','pinned_facts','message','action','assistant_backend','openai_model','deepseek_model','local_model','thinking','max_tokens','auto_compact','summary_override','output_selection','json_field','unload_after_generation'];
const legacyValues=legacyNames.map(name=>node.widgets.find(w=>w.name===name)?.value??'');legacyValues.push(1024,1024);node.widgets.find(w=>w.name==='chat_mode').value=1024;node.onConfigure({widgets_values:legacyValues,size:[900,1400]});await new Promise(resolve=>setTimeout(resolve,0));assert.equal(node.widgets.find(w=>w.name==='chat_mode').value,'Conversation');assert.deepEqual(Array.from(node.size),[900,1400]);
assert.equal(all(node.root).some(e=>e['aria-label']==='Mode'),false);
const styleSelect=all(node.root).find(e=>e['aria-label']==='Style / theme');assert.equal(styleSelect.tag,'select');styleSelect.value='Photo · Amateur Instagram';styleSelect.listeners.change();assert.equal(node.widgets.find(w=>w.name==='style_preset').value,'Photo · Amateur Instagram');assert.equal(queued,2);assert.ok(all(node.root).some(e=>e.textContent?.includes('no request sent')));
node.onRemoved();
console.log('Grimoire restores history, uses text-only DOM, prevents duplicate queued sends, copies output and exposes summary edits.');
