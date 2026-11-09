import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {layoutGrimoire} from '../web/grimoire_layout.mjs';
import {chatPrompt} from '../web/grimoire_queue.mjs';
import {renderMarkdown} from '../web/grimoire_markdown.mjs';
class Element {
    constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.style={};this.value='';}
    append(...items){this.children.push(...items);}
    replaceChildren(){this.children=[];}
    setAttribute(name,value){this[name]=value;}
    addEventListener(name,fn){this.listeners[name]=fn;}
}
let queued=0,copied='',imageJobs=0,job;
const snapshot={output:{7:{class_type:'DanbooruTagsTransformerGrimoire',inputs:{}},8:{class_type:'SaveImage',inputs:{images:['7',0]}}},workflow:{nodes:[]}};
const context={layoutGrimoire,chatPrompt,renderMarkdown,document:{createElement:tag=>new Element(tag)},crypto:{getRandomValues:bytes=>bytes.fill(7)},
    navigator:{clipboard:{async writeText(value){copied=value;}}},window:{confirm:()=>true},
    app:{registerExtension(){},async graphToPrompt(){return snapshot;},async queuePrompt(){imageJobs++;}},api:{async queuePrompt(index,value){queued++;job=value;return {prompt_id:'test-job'};},async fetchApi(path,options){assert.equal(options.method,'POST');return {ok:true,async json(){if(path.endsWith('/chats'))return {chats:[{id:'older-chat',title:'An older chat',updated:1,turns:2}]};return JSON.parse(options.body).id==='older-chat'?{turns:[{role:'assistant',content:'Saved answer'}],summary:'Saved summary',settings:{task_instructions:'Restored task'}}:{turns:[],summary:''};}};},addEventListener(){},removeEventListener(){}},
    installOpenAIKeyWidget(){},refreshOpenAIKeyWidget(){},installDeepSeekKeyWidget(){},refreshDeepSeekKeyWidget(){}};
vm.runInNewContext(readFileSync(new URL('../web/grimoire.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function','function'),context);
globalThis.document=context.document;
const node={id:7,size:[650,900],widgets:['system_prompt','pinned_facts','task_instructions','message','conversation_id','action','assistant_backend','summary_override','openai_model','deepseek_model','local_model'].map(name=>({name,value:name==='assistant_backend'?'Local Qwen':'',options:name==='assistant_backend'?{values:['Local Qwen','OpenAI API','DeepSeek API']}:{}})),
    addDOMWidget(name,type,root,options){this.root=root;this.domOptions=options;this.chatWidget={serialize:options.serialize};return this.chatWidget;},computeSize(){return [650,680];},setSize(size){this.size=size;},setDirtyCanvas(){}};
context.installGrimoire(node);
await new Promise(resolve=>setTimeout(resolve,0));
assert.equal(node.widgets.find(w=>w.name==='conversation_id').value,'07070707070707070707070707070707');assert.equal(node.chatWidget.serialize,false);assert.equal(node.widgets.find(w=>w.name==='action').value,'Use latest');assert.equal(node.domOptions.getMinHeight(),560);assert.equal(node.domOptions.getMaxHeight,undefined);node.size=[800,1300];
function all(root){return [root,...root.children.flatMap(all)];}
const button=name=>all(node.root).find(e=>e.tag==='button'&&e.textContent===name);
const composer=all(node.root).find(e=>e['aria-label']==='Message Grimoire');
composer.value='Hello **Grimoire**';button('Send').listeners.click();await new Promise(resolve=>setTimeout(resolve,0));
assert.deepEqual(Array.from(node.size),[800,1300]);assert.equal(queued,1);assert.equal(imageJobs,0);assert.deepEqual(Object.keys(job.output),['7']);assert.equal(job.output['7'].inputs.action,'Send');assert.equal(node.widgets.find(w=>w.name==='action').value,'Use latest');button('Send').listeners.click();assert.equal(queued,1);
node.onExecuted({grimoire:[{turns:[{role:'assistant',content:'<script>unsafe()</script>'}],summary:'Remember green cloak'}]});
assert.ok(all(node.root).some(e=>e.textContent==='<script>unsafe()</script>'));assert.equal(all(node.root).some(e=>e.tag==='script'),false);
const menu=all(node.root).find(e=>e['aria-label']==='Conversation actions');menu.value='Copy latest';await menu.listeners.change();assert.equal(copied,'<script>unsafe()</script>');
button('Edit summary').listeners.click();assert.equal(node.widgets.find(w=>w.name==='summary_override').value,'Remember green cloak');
await button('Generate image').listeners.click();assert.equal(imageJobs,1);assert.equal(node.widgets.find(w=>w.name==='action').value,'Use latest');
button('Settings').listeners.click();
const provider=all(node.root).find(e=>e['aria-label']==='Assistant provider');provider.value='DeepSeek API';provider.listeners.change();assert.equal(node.widgets.find(w=>w.name==='assistant_backend').value,'DeepSeek API');
assert.ok(node.widgets.every(w=>w.hidden));
const tree=new Element('div');renderMarkdown(tree,'# Title\n**Bold**\n```json\n{"x":1}\n```',value=>{copied=value;});assert.equal(tree.children[0].tag,'h1');tree.children[2].children[0].children[0].listeners.click();assert.equal(copied,'{"x":1}');
assert.throws(()=>chatPrompt({output:{7:{class_type:'DanbooruTagsTransformerGrimoire',inputs:{image:['9',0]}},9:{class_type:'KSampler',inputs:{}}}},7,'Send','hello'),/image generation/);
node.onExecuted({grimoire:[{turns:[],summary:''}]});const picker=all(node.root).find(e=>e['aria-label']==='Saved chats');picker.value='older-chat';picker.listeners.change();await new Promise(resolve=>setTimeout(resolve,0));assert.equal(node.widgets.find(w=>w.name==='conversation_id').value,'older-chat');assert.equal(node.widgets.find(w=>w.name==='task_instructions').value,'Restored task');
assert.deepEqual(Array.from(node.size),[800,1300]);assert.equal(node.widgets[0].computeLayoutSize().maxHeight,0);
node.onRemoved();
console.log('Grimoire restores history, uses text-only DOM, prevents duplicate queued sends, copies output and exposes summary edits.');
