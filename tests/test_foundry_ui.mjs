import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {FOUNDRY,REVIEW,foundryPrompt,queueFoundry} from '../web/foundry_queue.mjs';

const snapshot={workflow:{nodes:[]},output:{
    1:{class_type:FOUNDRY,inputs:{clip:['9',0],width:1024,height:1024}},
    2:{class_type:'CLIPTextEncode',inputs:{text:['1',0]}},
    3:{class_type:'RandomNoise',inputs:{noise_seed:['1',3]}},
    4:{class_type:'EmptyLatentImage',inputs:{batch_size:1}},
    5:{class_type:'SamplerCustomAdvanced',inputs:{positive:['2',0],noise:['3',0],latent:['4',0]}},
    6:{class_type:'VAEDecode',inputs:{samples:['5',0]}},
    7:{class_type:REVIEW,inputs:{image:['6',0],run_id:['1',4],attempt_id:['1',5],clip:['9',0]}},
    8:{class_type:'SaveImage',inputs:{images:['6',0],filename_prefix:['1',6]}},
    9:{class_type:'CLIPLoader',inputs:{}},10:{class_type:'SaveImage',inputs:{images:['6',0],filename_prefix:'unrelated'}}}};
let job=foundryPrompt(snapshot,1,'plan',{runId:'a'.repeat(32),remote:true});
assert.deepEqual(job.targets,['1']);assert.equal(job.output[1].class_type,FOUNDRY+'Plan');assert.equal(job.output[1].inputs.clip,undefined);assert.ok(job.output[10]);assert.ok(snapshot.output[1].inputs.clip);
job=foundryPrompt(snapshot,1,'render',{runId:'a'.repeat(32),attemptId:'b'.repeat(32),remote:true});assert.deepEqual(job.targets,['7','8']);assert.equal(job.output[7].inputs.clip,undefined);
const change=fn=>{const v=structuredClone(snapshot);fn(v.output);return v;};
assert.throws(()=>foundryPrompt(change(g=>delete g[7]),1,'render'),/exactly one/);
assert.throws(()=>foundryPrompt(change(g=>g[3].inputs.noise_seed=12),1,'render'),/seed/);
assert.throws(()=>foundryPrompt(change(g=>g[4].inputs.batch_size=5),1,'render'),/batch_size/);
assert.throws(()=>foundryPrompt(change(g=>g[1].inputs.clip=['5',0]),1,'plan'),/cycle|generation/);
assert.throws(()=>foundryPrompt(change(g=>g[2].inputs.text='unrelated'),1,'render'),/must use/);
let sent;
await queueFoundry({clientId:'x',async fetchApi(path,options){if(path.includes('capabilities'))return {ok:true,json:async()=>({partial_execution:true})};sent=JSON.parse(options.body);return {ok:true,json:async()=>({prompt_id:'job'})};}},job);
assert.deepEqual(sent.partial_execution_targets,['7','8']);assert.equal(Object.keys(sent.prompt).length,10);
await assert.rejects(()=>queueFoundry({fetchApi:async()=>({ok:true,json:async()=>({partial_execution:false})})},job),/Update/);

class Element {
    constructor(tag){this.tag=tag;this.children=[];this.style={};this.value='';this.classList={add(){},remove(){}};}
    append(...children){this.children.push(...children);}
    replaceChildren(){this.children=[];}
    setAttribute(k,v){this[k]=v;}
}
let calls=[],queueCount=0,events={};
let run={id:'a'.repeat(32),status:'plan_ready',assistant:'Local Qwen',width:1024,height:1024,current:0,shot_count:1,usage:{renders:0,calls:1},limits:{renders:3,calls:8},attempts:[],plan:{title:'Inn',shots:[{title:'Map',brief:'Traveler holding map',criteria:['Map visible']}]}};
const api={addEventListener(k,f){events[k]=f;},removeEventListener(k){delete events[k];},async fetchApi(path,options){const d=JSON.parse(options?.body||'{}');calls.push(d.operation||path);if(path.endsWith('capabilities'))return {ok:true,json:async()=>({partial_execution:true})};if(path==='/prompt'){queueCount++;return {ok:true,json:async()=>({prompt_id:'job'})};}if(d.operation==='approve')run={...run,approved:true,status:'ready'};if(d.operation==='reserve')run={...run,status:'rendering',attempts:[{id:'b'.repeat(32),seed:3,status:'reserved'}]};return {ok:true,json:async()=>d.operation==='catalog'?{templates:[],runs:[]}:path.endsWith('chats')?{chats:[]}:d.operation==='reserve'?{run,attempt:run.attempts[0]}:{run}};}};
const context={FOUNDRY,foundryPrompt,queueFoundry,installDeepSeekKeyWidget(){},document:{createElement:t=>new Element(t)},crypto:{randomUUID:()=> 'a'.repeat(32)},window:{confirm:()=>true},app:{registerExtension(){},graphToPrompt:async()=>snapshot},api};
vm.runInNewContext(readFileSync(new URL('../web/foundry.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function','function'),context);
const names=['run_id','conversation_id','template_id','brief','shared_rules','review_rules','shot_count','max_attempts','max_renders','max_calls','attempt_id','assistant_profile'];
const node={id:1,size:[620,900],properties:{},widgets:names.map(name=>({name,value:name==='run_id'?run.id:name==='shot_count'?1:''})),setSize(s){this.size=s;},addDOMWidget(name,type,root,options){this.root=root;return {serialize:options.serialize};}};
context.installFoundry(node);const tick=()=>new Promise(resolve=>setTimeout(resolve,0));await tick();
const all=e=>[e,...e.children.flatMap(all)],find=text=>all(node.root).find(e=>e.tag==='button'&&e.textContent===text);
assert.equal(queueCount,0,'Opening a saved plan must not call AI or queue generation');
const profile=all(node.root).find(e=>e.tag==='select'&&e['aria-label']==='Assistant model');profile.value='DeepSeek V4.1 Flash · Recommended · Text + images';profile.onchange();assert.equal(node.widgets.find(w=>w.name==='assistant_profile').value,profile.value);assert.equal(queueCount,0,'Selecting DeepSeek must not make a model request');
await find('Approve plan').onclick();assert.equal(queueCount,0,'Approval must be a record-only action');
await find('Render & review one frame').onclick();assert.equal(queueCount,1);assert.equal(run.status,'rendering');
run={...run,status:'awaiting_approval',attempts:[{...run.attempts[0],image:false,review:{verdict:'pass',summary:'Map visible',checks:[]}}]};
events.executed({detail:{output:{foundry:[run]}}});await tick();
await find('Accept frame').onclick();assert.equal(queueCount,1,'Acceptance must never automatically queue another frame');
node.onSerialize({});const data={};node.onSerialize(data);assert.deepEqual(Array.from(data.properties.mage_foundry_size),[620,900]);
node.onRemoved();assert.deepEqual(Object.keys(events),[]);
console.log('Foundry queue and manual-gate UI checks passed');
