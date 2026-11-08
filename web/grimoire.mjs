import { app } from '../../scripts/app.js';
import { api } from '../../scripts/api.js';
import { installOpenAIKeyWidget, refreshOpenAIKeyWidget } from './openai_key.mjs?v=1.15.0';
import { installDeepSeekKeyWidget, refreshDeepSeekKeyWidget } from './deepseek_key.mjs?v=1.15.0';

// Plain text only: model/user messages never become executable HTML.
export function installGrimoire(node) {
    const field = name => node.widgets?.find(w=>w.name===name);
    if (!field('conversation_id')?.value) field('conversation_id').value=crypto.randomUUID();
    const root=document.createElement('section');
    root.style.cssText='padding:14px;background:linear-gradient(135deg,#211a32,#152c31);border:1px solid #ba9957;border-radius:12px;color:#eee;display:flex;flex-direction:column;gap:10px;box-sizing:border-box;height:100%;font:13px sans-serif';
    const title=document.createElement('strong');title.textContent='✦ GRIMOIRE · Your living spellbook';
    const notice=document.createElement('small');notice.textContent='Saved on this ComfyUI server · Send queues the connected workflow';
    const status=document.createElement('div');status.setAttribute('role','status');
    const history=document.createElement('div');history.style.cssText='overflow:auto;flex:1;min-height:180px;white-space:pre-wrap;user-select:text';history.setAttribute('aria-label','Conversation history');history.setAttribute('role','log');
    const summary=document.createElement('textarea');summary.readOnly=true;summary.setAttribute('aria-label','Current compacted memory');summary.style.cssText='min-height:65px;width:100%;box-sizing:border-box;background:#151620;color:#ddd';summary.placeholder='Compacted memory appears here. System, task and pinned fields remain separate.';
    const buttons=document.createElement('div');buttons.style.cssText='display:flex;flex-wrap:wrap;gap:6px';
    let latest='', busy=false, requestVersion=0;
    function render(value) {
        history.replaceChildren();
        for(const turn of value.turns||[]) {
            const item=document.createElement('div');item.style.cssText='padding:10px;margin-bottom:8px;border-left:3px solid '+(turn.role==='user'?'#74bec6':'#d4af66')+';background:#ffffff08';
            item.textContent=(turn.role==='user'?'YOU':'GRIMOIRE')+'\n'+turn.content;history.append(item);
        }
        latest=[...(value.turns||[])].reverse().find(t=>t.role==='assistant')?.content||'';
        summary.value=value.summary||'';
        status.textContent=value.report?.compacted?'Older turns compacted · inspect the summary':`${(value.turns||[]).length} saved messages`;
        if(value.report?.note)status.textContent+=' · '+value.report.note;
        history.scrollTop=history.scrollHeight;
    }
    async function load() {
        const version=++requestVersion;
        try {const response=await api.fetchApi('/prompt_mage/grimoire/history?id='+encodeURIComponent(field('conversation_id').value));if(!response.ok)throw Error();const value=await response.json();if(version===requestVersion)render(value);}
        catch{status.textContent='History unavailable · start/restart ComfyUI or check the chapter ID';}
    }
    async function run(action) {
        if(busy)return;
        if(action==='Clear conversation'&&!window.confirm('Clear this chapter’s saved history and summary? Configured instructions and pinned facts remain.'))return;
        busy=true;status.textContent='Queueing '+action+'…';field('action').value=action;
        try{await app.queuePrompt(0,1);}catch{busy=false;status.textContent='Could not queue. Check ComfyUI status.';}
    }
    function button(label, callback) {const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',callback);buttons.append(b);}
    button('Send · queue workflow',()=>void run('Send'));
    button('Next step',()=>void run('Next step'));
    button('Regenerate',()=>void run('Regenerate'));
    button('Compact now',()=>void run('Compact now'));
    button('Clear conversation',()=>void run('Clear conversation'));
    button('New chapter',()=>{if(busy){status.textContent='Wait for this queued turn to finish or cancel it first.';return;}field('conversation_id').value=crypto.randomUUID();field('summary_override').value='';render({turns:[],summary:''});void load();});
    button('Copy latest',async()=>{try{await navigator.clipboard.writeText(latest);status.textContent='Latest response copied';}catch{status.textContent='Clipboard unavailable · select and copy the response';}});
    button('Edit summary',()=>{field('summary_override').value=summary.value;status.textContent='Edit Summary override below; it is applied on the next successful run.';});
    root.append(title,notice,status,history,summary,buttons);
    node.addDOMWidget('grimoire_chat','GRIMOIRE_CHAT',root,{serialize:false,getMinHeight:()=>470,getMaxHeight:()=>470,hideOnZoom:true}).serialize=false;
    installOpenAIKeyWidget(node,api);installDeepSeekKeyWidget(node,api);
    function controls() {
        const backend=field('assistant_backend')?.value;
        for(const name of ['openai_model'])if(field(name))field(name).hidden=backend!=='OpenAI API';
        if(field('deepseek_model'))field('deepseek_model').hidden=backend!=='DeepSeek API';
        if(field('local_model'))field('local_model').hidden=backend!=='Local Qwen';
        refreshOpenAIKeyWidget(node);refreshDeepSeekKeyWidget(node);
        node.setSize([Math.max(650,node.size[0]),node.computeSize()[1]]);node.setDirtyCanvas(true,true);
    }
    const callback=field('assistant_backend').callback;
    field('assistant_backend').callback=function(...args){callback?.apply(this,args);controls();};
    const idCallback=field('conversation_id').callback;
    field('conversation_id').callback=function(...args){idCallback?.apply(this,args);void load();};
    const executed=node.onExecuted;node.onExecuted=function(message){busy=false;executed?.apply(this,arguments);if(message.grimoire?.[0])render(message.grimoire[0]);};
    const failed=()=>{busy=false;status.textContent='Execution ended or failed. Review the ComfyUI error before retrying.';};
    api.addEventListener('execution_error',failed);api.addEventListener('execution_interrupted',failed);
    const removed=node.onRemoved;node.onRemoved=function(){api.removeEventListener('execution_error',failed);api.removeEventListener('execution_interrupted',failed);removed?.apply(this,arguments);};
    const configured=node.onConfigure;node.onConfigure=function(){configured?.apply(this,arguments);if(!field('conversation_id').value)field('conversation_id').value=crypto.randomUUID();controls();void load();};
    controls();void load();
}

app.registerExtension({name:'PromptMage.Grimoire',beforeRegisterNodeDef(type,data){
    if(data.name!=='DanbooruTagsTransformerGrimoire')return;
    const created=type.prototype.onNodeCreated;
    type.prototype.onNodeCreated=function(){created?.apply(this,arguments);installGrimoire(this);};
}});
