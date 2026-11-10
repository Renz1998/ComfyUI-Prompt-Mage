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
let briefHooks;let calls=[],queueCount=0,events={},approvedPayload=null,queuedGraphs=[],pollCallback=null,pollCleared=0;
let run={id:'a'.repeat(32),status:'plan_ready',run_mode:'Manual',assistant:'Local Qwen',width:1024,height:1024,current:0,shot_count:1,usage:{renders:0,calls:1},limits:{renders:3,calls:8},attempts:[],plan:{title:'Inn',shots:[{id:'shot-1',title:'Map',brief:'Traveler holding map',criteria:['Map visible']}]}};
const api={addEventListener(k,f){events[k]=f;},removeEventListener(k){delete events[k];},async fetchApi(path,options){const d=JSON.parse(options?.body||'{}');calls.push(d.operation||path);if(path.endsWith('capabilities'))return {ok:true,json:async()=>({partial_execution:true})};if(path==='/prompt'){queueCount++;queuedGraphs.push(JSON.parse(options.body));return {ok:true,json:async()=>({prompt_id:'job'})};}if(d.operation==='approve_start'){approvedPayload=d;run={...run,approved:true,status:'ready',automation_enabled:run.run_mode!=='Manual'};}if(d.operation==='reserve')run={...run,status:'rendering',attempts:[{id:'b'.repeat(32),seed:3,shot_id:'shot-1',status:'reserved'}]};return {ok:true,json:async()=>d.operation==='catalog'?{templates:[],runs:[]}:path.endsWith('chats')?{chats:[]}:d.operation==='reserve'?{run,attempt:run.attempts[0]}:{run}};}};
const context={ensureBriefInput(){},installFoundryBrief(options){briefHooks=options;return {refresh(){},destroy(){}};},setTimeout(fn){pollCallback=fn;return 1;},clearTimeout(){pollCleared++;},FOUNDRY,foundryPrompt,queueFoundry,installReferences(){return {busy:false,async restore(){},destroy(){}};},installDeepSeekKeyWidget(){},installOpenAIKeyWidget(){},installGeminiKeyWidget(){},document:{createElement:t=>new Element(t)},crypto:{randomUUID:()=> 'c'.repeat(32)},window:{confirm:()=>{throw Error('Acceptance must never ask for confirmation');}},app:{registerExtension(){},graphToPrompt:async()=>snapshot},api};
vm.runInNewContext(readFileSync(new URL('../web/foundry.mjs',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'').replace('export function','function'),context);
const names=['run_id','conversation_id','template_id','brief','shared_rules','review_rules','shot_count','max_attempts','max_renders','max_calls','attempt_id','assistant_profile','style_preset','style_notes','run_mode','review_tolerance','attachments','reference_roles','reference_instructions','physical_tolerance','passing_score','failure_policy','output_folder','brief_id'];
const node={id:1,size:[620,900],properties:{},widgets:names.map(name=>({name,value:name==='run_id'?run.id:name==='shot_count'?1:name==='run_mode'?'Manual':name==='style_preset'?'Photo · Bright lifestyle':name==='review_tolerance'?'Balanced':''})),setSize(s){this.size=s;},addDOMWidget(name,type,root,options){this.root=root;return {serialize:options.serialize};}};
context.installFoundry(node);const tick=()=>new Promise(resolve=>setTimeout(resolve,0));await tick();
const all=e=>[e,...e.children.flatMap(all)],find=text=>all(node.root).find(e=>e.tag==='button'&&e.textContent===text);
assert.equal(node.color,'#563021');assert.equal(node.bgcolor,'#251c1b');assert.ok(all(node.root).some(e=>e['aria-label']==='Physical inspection'));assert.ok(all(node.root).some(e=>e['aria-label']==='Custom folder name (optional)'));
assert.equal(all(node.root).filter(e=>e.tag==='button'&&e.textContent==='Preview plan').length,2);assert.ok(all(node.root).filter(e=>e.tag==='button'&&e.textContent==='Preview plan').every(e=>e.disabled),'Ready plans disable both previews');assert.ok(all(node.root).some(e=>e.textContent==='Planning settings'));assert.ok(find('Regenerate plan'));assert.ok(find('Edit brief'));
assert.equal(queueCount,0,'Opening a saved plan must not call AI or queue generation');
const profile=all(node.root).find(e=>e.tag==='select'&&e['aria-label']==='Assistant model');profile.value='DeepSeek V4.1 Flash · Recommended · Text + images';profile.onchange();assert.equal(node.widgets.find(w=>w.name==='assistant_profile').value,profile.value);assert.equal(queueCount,0,'Selecting DeepSeek must not make a model request');
await find('Edit brief').onclick();assert.ok(all(node.root).filter(e=>e.tag==='button'&&e.textContent==='Preview plan').every(e=>!e.disabled),'Editing the brief explicitly enables preview');assert.ok(find('Cancel editing'));await find('Cancel editing').onclick();assert.ok(all(node.root).filter(e=>e.tag==='button'&&e.textContent==='Preview plan').every(e=>e.disabled));
const project=all(node.root).find(e=>e['aria-label']==='Project name');project.value='A new project';await find('Approve plan').onclick();assert.equal(approvedPayload.plan.title,'A new project');assert.equal(queueCount,0,'Approval must be a record-only action');
await find('Render & review first frame').onclick();assert.equal(queueCount,1);assert.equal(run.status,'rendering');events.executed({detail:{output:{foundry:[run]}}});await tick();assert.ok(all(node.root).filter(e=>e.tag==='button'&&e.textContent==='Preview plan').every(e=>e.disabled));assert.equal(find('Preview plan').disabled,true,'Manual processing disables plan preview');assert.equal(find('New plan').disabled,true,'Cannot detach a running job by starting another plan');
const polledCalls=calls.length;await pollCallback();assert.ok(calls.length>polledCalls);assert.equal(queueCount,1,'Status polling never queues generation');
run={...run,status:'awaiting_approval',attempts:[{...run.attempts[0],image:false,review:{verdict:'pass',summary:'Map visible',checks:[]}}]};
events.executed({detail:{output:{foundry:[run]}}});await tick();
await find('Accept frame').onclick();assert.equal(queueCount,1,'Acceptance must never automatically queue another frame');
run={...run,status:'plan_ready',run_mode:'Automatic',approved:false};events.prompt_mage_foundry({detail:{foundry:[run]}});await tick();const before=queueCount;await find('Approve & start sequence').onclick();assert.equal(queueCount,before,'Automatic approval delegates to the server, not a browser loop');assert.deepEqual(approvedPayload.job.targets,['7','8']);assert.equal(run.automation_enabled,true);run={...run,status:'ready',run_mode:'Manual',automation_enabled:false,current:1,shot_count:2,plan:{...run.plan,shots:[...run.plan.shots,{id:'shot-2',title:'Next',brief:'Next shot',criteria:['Map']}]}};events.prompt_mage_foundry({detail:{foundry:[run]}});await tick();assert.ok(find('Render & review next frame'),'After acceptance Manual mode must name the next-frame action');node.setSize([720,1100]);const data={};node.onSerialize(data);assert.deepEqual(Array.from(data.properties.mage_foundry_size),[720,1100]);
run={...run,status:'plan_ready',approved:false,current:0,automation_enabled:false};events.executed({detail:{output:{foundry:[run]}}});await tick();const beforeRegenerate=queueCount;await find('Regenerate plan').onclick();assert.equal(queueCount,beforeRegenerate+1);const regen=queuedGraphs.at(-1);assert.equal(regen.prompt['1'].class_type,FOUNDRY+'Plan');assert.deepEqual(regen.partial_execution_targets,['1']);assert.notEqual(regen.prompt['1'].inputs.run_id,run.id);assert.ok(!calls.includes('stop'),'Regenerating a preview must not stop or delete saved runs');
const oldProvider=node.widgets.find(w=>w.name==='assistant_profile').value,oldCaps=['max_renders','max_calls'].map(name=>node.widgets.find(w=>w.name===name).value);await briefHooks.onApply({id:'d'.repeat(32),settings:{brief:'Agreed new story',shared_rules:'Same cloak',review_rules:'Plausible pose',style_notes:'',style_preset:'Photo · Travel diary',shot_count:7,aspect_ratio:'4:5',references:[]}});assert.equal(node.widgets.find(w=>w.name==='brief').value,'Agreed new story');assert.equal(node.widgets.find(w=>w.name==='shot_count').value,7);assert.equal(node.widgets.find(w=>w.name==='assistant_profile').value,oldProvider);assert.deepEqual(['max_renders','max_calls'].map(name=>node.widgets.find(w=>w.name===name).value),oldCaps);assert.equal(node.widgets.find(w=>w.name==='brief_id')?.value,'d'.repeat(32));assert.ok(node.properties.mage_brief_canvas.height>node.properties.mage_brief_canvas.width);
const resolution={id:10,type:'DanbooruTagsTransformerResolution',widgets:[{name:'aspect_ratio',value:'1:1'},{name:'megapixels',value:3.7}]};node.inputs=[{name:'width',link:30},{name:'height',link:31}];node.graph={links:{30:{origin_id:10},31:{origin_id:10}},getNodeById:id=>id===10?resolution:null};await briefHooks.onApply({id:'e'.repeat(32),settings:{brief:'Same idea',shared_rules:'',review_rules:'',style_notes:'',shot_count:3,aspect_ratio:'4:5',references:[]}});assert.equal(resolution.widgets[0].value,'4:5');assert.equal(resolution.widgets[1].value,3.7,'Aspect import preserves the existing pixel budget');
node.onRemoved();assert.ok(pollCleared>0,'Removing a node clears its status timer');assert.deepEqual(Object.keys(events),[]);
console.log('Foundry queue, automatic approval, immediate acceptance, style and persisted size checks passed');

const live=structuredClone(snapshot);live.output[1].inputs.production_brief=["11",4];live.output[11]={class_type:"DanbooruTagsTransformerGrimoire",inputs:{image:["6",0]}};const isolated=foundryPrompt(live,1,"plan",{runId:"a".repeat(32),remote:true});assert.equal(isolated.output[1].inputs.production_brief,undefined,"Foundry planning must never traverse or chat through its handoff socket");
