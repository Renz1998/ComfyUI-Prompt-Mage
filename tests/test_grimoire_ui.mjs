import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
class Element {
    constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.style={};this.value='';}
    append(...items){this.children.push(...items);}
    replaceChildren(){this.children=[];}
    setAttribute(name,value){this[name]=value;}
    addEventListener(name,fn){this.listeners[name]=fn;}
}
let queued=0,copied='';
const context={document:{createElement:tag=>new Element(tag)},crypto:{randomUUID:()=> 'test-chapter-uuid'},
    navigator:{clipboard:{async writeText(value){copied=value;}}},window:{confirm:()=>true},
    app:{registerExtension(){},async queuePrompt(){queued++;}},api:{async fetchApi(){return {ok:true,async json(){return {turns:[],summary:''};}};},addEventListener(){},removeEventListener(){}},
    installOpenAIKeyWidget(){},refreshOpenAIKeyWidget(){},installDeepSeekKeyWidget(){},refreshDeepSeekKeyWidget(){}};
vm.runInNewContext(readFileSync(new URL('../web/grimoire.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function','function'),context);
const node={size:[650,900],widgets:['conversation_id','action','assistant_backend','summary_override','openai_model','deepseek_model','local_model'].map(name=>({name,value:name==='assistant_backend'?'Local Qwen':''})),
    addDOMWidget(name,type,root,options){this.root=root;this.chatWidget={serialize:options.serialize};return this.chatWidget;},computeSize(){return this.size;},setSize(){},setDirtyCanvas(){}};
context.installGrimoire(node);
await new Promise(resolve=>setTimeout(resolve,0));
assert.equal(node.widgets[0].value,'test-chapter-uuid');assert.equal(node.chatWidget.serialize,false);
const buttons=node.root.children.at(-1).children;
buttons[0].listeners.click();await new Promise(resolve=>setTimeout(resolve,0));
assert.equal(queued,1);buttons[0].listeners.click();assert.equal(queued,1);
node.onExecuted({grimoire:[{turns:[{role:'assistant',content:'<script>unsafe()</script>'}],summary:'Remember green cloak'}]});
assert.equal(node.root.children[3].children[0].textContent,'GRIMOIRE\n<script>unsafe()</script>');
await buttons[6].listeners.click();assert.equal(copied,'<script>unsafe()</script>');
buttons[7].listeners.click();assert.equal(node.widgets.find(w=>w.name==='summary_override').value,'Remember green cloak');
node.onRemoved();
console.log('Grimoire restores history, uses text-only DOM, prevents duplicate queued sends, copies output and exposes summary edits.');
