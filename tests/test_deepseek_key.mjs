import assert from 'node:assert/strict';
import {installDeepSeekKeyWidget,refreshDeepSeekKeyWidget} from '../web/deepseek_key.mjs';
class Element {
    constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.value='';}
    append(...items){this.children.push(...items);}
    setAttribute(name,value){this[name]=value;}
    addEventListener(name,callback){this.listeners[name]=callback;}
}
globalThis.document={createElement:tag=>new Element(tag)};
globalThis.window=new EventTarget();
let configured=false,secretSent='';
const api={async fetchApi(path,options){
    assert.equal(path,'/prompt_mage/deepseek/key');
    if(options?.method==='POST'){secretSent=JSON.parse(options.body).key;configured=Boolean(secretSent);}
    return {ok:true,async json(){return {configured,session_configured:configured};}};
}};
const node={properties:{},size:[550,800],widgets:[{name:'assistant_backend',value:'DeepSeek API'}],
    addDOMWidget(name,type,root,options){this.root=root;this.widget={name,serialize:options.serialize};this.widgets.push(this.widget);return this.widget;},
    computeSize(){return this.size;},setSize(){},setDirtyCanvas(){}};
installDeepSeekKeyWidget(node,api);
await new Promise(resolve=>setTimeout(resolve,0));
const [bar,form]=node.root.children;
const [status,change]=bar.children;
const [input,save,remove]=form.children;
assert.equal(input.type,'password');assert.equal(node.widget.serialize,false);
input.value='sk-synthetic-test-only';save.listeners.click();
await new Promise(resolve=>setTimeout(resolve,0));
assert.equal(secretSent,'sk-synthetic-test-only');
assert.equal(input.value,'');assert.equal(form.hidden,true);
assert.match(status.textContent,/configured/);
assert.equal(JSON.stringify(node.properties),'{}');
assert.equal(node.widgets.some(w=>w.value==='sk-synthetic-test-only'),false);
node.widgets[0].value='Local Qwen';refreshDeepSeekKeyWidget(node);assert.equal(node.widget.hidden,true);
remove.listeners.click();await new Promise(resolve=>setTimeout(resolve,0));assert.equal(configured,false);
node.onRemoved();
console.log('Masked session-key UI clears/collapses after save and never stores credentials in workflow widgets.');
