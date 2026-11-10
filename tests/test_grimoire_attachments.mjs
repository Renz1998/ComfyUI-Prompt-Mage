import assert from 'node:assert/strict';
import {ensureImageInputs} from '../web/grimoire_images.mjs';
import {installAttachments} from '../web/grimoire_attachments.mjs';

const node={inputs:[{name:'clip',link:null},{name:'image',link:11},{name:'appearance',link:12},{name:'width',link:13}],graph:{links:{11:{target_slot:1},12:{target_slot:2},13:{target_slot:3}}},addInput(name,type,options){this.inputs.push({name,type,link:null,...options});},removeInput(index){this.inputs.splice(index,1);},setDirtyCanvas(){}};
ensureImageInputs(node);assert.deepEqual(node.inputs.map(s=>s.name),['clip','image','image_2','appearance','width']);assert.equal(node.graph.links[12].target_slot,3);
node.inputs[2].link=14;node.graph.links[14]={target_slot:2};ensureImageInputs(node);assert.equal(node.inputs[3].name,'image_3');assert.equal(node.graph.links[14].target_slot,2);
node.inputs[1].link=null;ensureImageInputs(node);assert.equal(node.inputs[3].name,'image_3');node.inputs[2].link=null;ensureImageInputs(node);assert.deepEqual(node.inputs.map(s=>s.name),['clip','image','appearance','width']);assert.equal(node.graph.links[12].target_slot,2);
for(let n=1;n<=6;n++){ensureImageInputs(node);const slot=node.inputs.find(s=>s.name===(n===1?'image':'image_'+n));slot.link=100+n;node.graph.links[100+n]={target_slot:0};}
ensureImageInputs(node);assert.equal(node.inputs.filter(s=>s.name.startsWith('image')).length,6);assert.equal(node.inputs.some(s=>s.name==='image_7'),false);

class Element{
    constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.style={};this.classList={add(){},remove(){}};}
    append(...items){this.children.push(...items);}replaceChildren(){this.children=[];}setAttribute(name,value){this[name]=value;}
    addEventListener(name,fn){this.listeners[name]=fn;}removeEventListener(name){delete this.listeners[name];}
}
globalThis.document={createElement:tag=>new Element(tag)};
let uploads=0,notification='',changes=0;
const root=new Element('section'),mount=new Element('div'),buttonMount=new Element('div');
const api={async fetchApi(path,options){assert.equal(options.method,'POST');if(path.endsWith('/read'))return {ok:true,async json(){return {id:'b'.repeat(32),kind:'text',name:'saved.txt',excerpt:'Saved reference'};}};uploads++;assert.ok(options.body instanceof FormData);return {ok:true,async json(){return {id:String(uploads).padStart(32,'0'),kind:'text',name:options.body.get('file').name,truncated:false,excerpt:'Reference text'};}};}};
const tray=installAttachments({root,mount,buttonMount,api,notify:value=>notification=value,changed:()=>changes++});
const picker=mount.children[0];picker.files=[new File(['Reference text'],'notes.md')];await picker.listeners.change();await new Promise(r=>setTimeout(r,0));assert.equal(uploads,1);assert.equal(tray.ids().length,1);assert.equal(mount.hidden,false);assert.match(notification,/attached/);assert.equal(tray.busy,false);
tray.consume(tray.ids());assert.equal(tray.ids().length,0);assert.equal(mount.hidden,true);
let prevented=false,stopped=false;root.listeners.drop({dataTransfer:{files:[new File(['Another ref'],'ref.json')]},preventDefault(){prevented=true;},stopPropagation(){stopped=true;}});await new Promise(r=>setTimeout(r,0));assert.equal(prevented,true);assert.equal(stopped,true);assert.equal(uploads,2);
await tray.reuse([{id:'b'.repeat(32)}]);assert.equal(tray.ids().length,2);assert.equal(uploads,2);
tray.clear();assert.equal(tray.ids().length,0);assert.ok(changes>0);tray.destroy();assert.equal(root.listeners.drop,undefined);
console.log('Attachments upload/drop/reuse/remove without model calls; image sockets grow to six and preserve existing graph links.');
