import assert from 'node:assert/strict';
import {installReferences} from '../web/foundry_references.mjs';
class Element{
    constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.style={};this.classList={add(){},remove(){}};}
    append(...v){this.children.push(...v);}replaceChildren(){this.children=[];}setAttribute(k,v){this[k]=v;}addEventListener(k,v){this.listeners[k]=v;}removeEventListener(k){delete this.listeners[k];}
}
globalThis.document={createElement:t=>new Element(t)};
let uploads=0,ids=[],roles={},notification='';const mount=new Element('section');
const api={async fetchApi(path,options){if(path.endsWith('/read')){const id=JSON.parse(options.body).id;return {ok:true,json:async()=>({id,kind:'image',name:'restored.png',preview:'data:image/png;base64,AA=='})};}uploads++;const file=options.body.get('file');return {ok:true,json:async()=>({id:String(uploads).padStart(32,'0'),kind:'image',name:file.name,preview:'data:image/png;base64,AA=='})};}};
const gallery=installReferences({mount,api,changed:(v,r)=>{ids=v;roles=r;},notify:v=>notification=v});
const all=e=>[e,...e.children.flatMap(all)];const tick=()=>new Promise(r=>setTimeout(r,0));
let prevented=false;mount.listeners.drop({dataTransfer:{files:Array.from({length:9},(_,i)=>new File(['image'],'outfit-'+i+'.png',{type:'image/png'}))},preventDefault(){prevented=true;},stopPropagation(){}});await tick();await tick();
assert.equal(prevented,true);assert.equal(uploads,9);assert.equal(ids.length,9,'Gallery accepts more than six references');
const firstId=ids[0],secondId=ids[1];const role=all(mount).find(e=>e.tag==='select');role.value='Outfit';role.onchange();assert.equal(roles[firstId],'Outfit');
const right=all(mount).find(e=>e['aria-label']==='Move reference 1 later');right.onclick();assert.deepEqual(ids.slice(0,2),[secondId,firstId]);assert.equal(roles[firstId],'Outfit');assert.equal(uploads,9,'Reordering must not upload again or call AI');
all(mount).find(e=>e['aria-label']==='Remove reference 1').onclick();assert.equal(ids.length,8);
const folder=all(mount).find(e=>e.tag==='input'&&e.webkitdirectory);assert.ok(folder);assert.equal(folder.multiple,true);
all(mount).find(e=>e.tag==='button'&&e.textContent==='Clear').onclick();assert.equal(ids.length,0);
await gallery.restore([firstId],{[firstId]:'Props'});assert.deepEqual(ids,[firstId]);assert.equal(roles[firstId],'Props');assert.equal(uploads,9);
gallery.destroy();assert.equal(mount.listeners.drop,undefined);
console.log('Foundry reference gallery: drag/drop, nine images, roles, reorder, remove, folder and persisted restore passed.');
