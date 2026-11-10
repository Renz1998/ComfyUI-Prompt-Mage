import assert from 'node:assert/strict';
import {briefSource,briefTargets,ensureBriefOutput,installFoundryBrief} from '../web/production_bridge.mjs';
class Element{constructor(tag){this.tag=tag;this.children=[];this.style={};}append(...e){this.children.push(...e);}replaceChildren(){this.children=[];}}
globalThis.document={createElement:t=>new Element(t)};const handlers=new Map();globalThis.window={addEventListener:(n,f)=>handlers.set(n,f),removeEventListener:n=>handlers.delete(n)};
const chat={id:1,type:'DanbooruTagsTransformerGrimoire',widgets:[{name:'conversation_id',value:'chapter-test'}],outputs:[],addOutput(name,type){this.outputs.push({name,type});}},foundry={id:2,type:'DanbooruTagsTransformerFoundry',properties:{},inputs:[{name:'production_brief',link:3}]};
const graph={_nodes:[chat,foundry],links:{3:{origin_id:1,target_id:2}},getNodeById:id=>[chat,foundry].find(n=>n.id===id)};chat.graph=foundry.graph=graph;
assert.equal(briefSource(foundry),chat);assert.deepEqual(briefTargets(chat),[foundry]);ensureBriefOutput(chat);ensureBriefOutput(chat);assert.equal(chat.outputs.length,1);
const value={id:'a'.repeat(32),conversation_id:'chapter-test',title:'Agreed travel carousel',settings:{brief:'Green cloak in a village',shot_count:3,style_preset:'Photo · Travel diary',aspect_ratio:'4:5',references:[]}};
let reads=0,applied=0,allowed=true,lastError='';const mount=new Element('section');const api={async fetchApi(path,options){assert.equal(path,'/prompt_mage/grimoire/production_brief');reads++;return {ok:true,json:async()=>({brief:value})};}};
const bridge=installFoundryBrief({node:foundry,mount,api,canApply:()=>allowed,canAutoApply:()=>true,onApply:async v=>{assert.equal(v.id,value.id);applied++;},notify:e=>{lastError=e;}});
assert.equal(reads,0);await bridge.load();assert.equal(applied,0,'Opening/checking a brief cannot apply it');await bridge.load(true);assert.equal(applied,1);assert.equal(foundry.properties.mage_production_brief_applied,value.id);
allowed=false;await bridge.load(true);assert.equal(applied,1,'Active runs cannot be overwritten');chat.widgets[0].value='another-chat';bridge.refresh();assert.equal(mount.children.at(-1).hidden,true,'Changing chats clears a stale pending brief');
bridge.destroy();assert.equal(handlers.size,0);assert.equal(lastError,'');
console.log('Production brief sockets, explicit import, busy protection, stale-chat handling and cleanup passed.');
