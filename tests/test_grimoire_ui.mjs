import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
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
const context={chatPrompt,renderMarkdown,document:{createElement:tag=>new Element(tag)},crypto:{getRandomValues:bytes=>bytes.fill(7)},
    navigator:{clipboard:{async writeText(value){copied=value;}}},window:{confirm:()=>true},
    app:{registerExtension(){},async graphToPrompt(){return snapshot;},async queuePrompt(){imageJobs++;}},api:{async queuePrompt(index,value){queued++;job=value;return {prompt_id:'test-job'};},async fetchApi(path,options){assert.equal(options.method,'POST');return {ok:true,async json(){if(path.endsWith('/chats'))return {chats:[{id:'older-chat',title:'An older chat',updated:1,turns:2}]};return JSON.parse(options.body).id==='older-chat'?{turns:[{role:'assistant',content:'Saved answer'}],summary:'Saved summary',settings:{task_instructions:'Restored task'}}:{turns:[],summary:''};}};},addEventListener(){},removeEventListener(){}},
    installOpenAIKeyWidget(){},refreshOpenAIKeyWidget(){},installDeepSeekKeyWidget(){},refreshDeepSeekKeyWidget(){}};
vm.runInNewContext(readFileSync(new URL('../web/grimoire.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function','function'),context);
globalThis.document=context.document;
const node={id:7,size:[650,900],widgets:['task_instructions','message','conversation_id','action','assistant_backend','summary_override','openai_model','deepseek_model','local_model'].map(name=>({name,value:name==='assistant_backend'?'Local Qwen':''})),
    addDOMWidget(name,type,root,options){this.root=root;this.chatWidget={serialize:options.serialize};return this.chatWidget;},computeSize(){return this.size;},setSize(){},setDirtyCanvas(){}};
context.installGrimoire(node);
await new Promise(resolve=>setTimeout(resolve,0));
assert.equal(node.widgets.find(w=>w.name==='conversation_id').value,'07070707070707070707070707070707');assert.equal(node.chatWidget.serialize,false);
const buttons=node.root.children.at(-1).children;
node.root.children[6].value='Hello **Grimoire**';buttons[0].listeners.click();await new Promise(resolve=>setTimeout(resolve,0));
assert.equal(queued,1);assert.equal(imageJobs,0);assert.deepEqual(Object.keys(job.output),['7']);buttons[0].listeners.click();assert.equal(queued,1);
node.onExecuted({grimoire:[{turns:[{role:'assistant',content:'<script>unsafe()</script>'}],summary:'Remember green cloak'}]});
assert.equal(node.root.children[4].children[0].children[1].children[0].textContent,'<script>unsafe()</script>');
await buttons[7].listeners.click();assert.equal(copied,'<script>unsafe()</script>');
buttons[8].listeners.click();assert.equal(node.widgets.find(w=>w.name==='summary_override').value,'Remember green cloak');
await buttons[9].listeners.click();assert.equal(imageJobs,1);assert.equal(node.widgets.find(w=>w.name==='action').value,'Use latest');
const tree=new Element('div');renderMarkdown(tree,'# Title\n**Bold**\n```json\n{"x":1}\n```',value=>{copied=value;});assert.equal(tree.children[0].tag,'h1');tree.children[2].children[0].children[0].listeners.click();assert.equal(copied,'{"x":1}');
assert.throws(()=>chatPrompt({output:{7:{class_type:'DanbooruTagsTransformerGrimoire',inputs:{image:['9',0]}},9:{class_type:'KSampler',inputs:{}}}},7,'Send','hello'),/image generation/);
node.onExecuted({grimoire:[{turns:[],summary:''}]});node.root.children[3].value='older-chat';node.root.children[3].listeners.change();await new Promise(resolve=>setTimeout(resolve,0));assert.equal(node.widgets.find(w=>w.name==='conversation_id').value,'older-chat');assert.equal(node.widgets.find(w=>w.name==='task_instructions').value,'Restored task');
node.onRemoved();
console.log('Grimoire restores history, uses text-only DOM, prevents duplicate queued sends, copies output and exposes summary edits.');
