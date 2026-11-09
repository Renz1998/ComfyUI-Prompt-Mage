import { layoutGrimoire } from './grimoire_layout.mjs?v=1.17.1';
import { chatPrompt } from './grimoire_queue.mjs?v=1.16.0';
import { renderMarkdown } from './grimoire_markdown.mjs?v=1.16.0';
import { app } from '../../scripts/app.js';
import { api } from '../../scripts/api.js';
import { installOpenAIKeyWidget, refreshOpenAIKeyWidget } from './openai_key.mjs?v=1.17.0';
import { installDeepSeekKeyWidget, refreshDeepSeekKeyWidget } from './deepseek_key.mjs?v=1.17.0';

// Plain text only: model/user messages never become executable HTML.
export function installGrimoire(node) {
    const chapterId=()=>{
        if(typeof crypto.randomUUID==='function')return crypto.randomUUID();
        const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);
        return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
    };
    const field = name => node.widgets?.find(w=>w.name===name);
    if (!field('conversation_id')?.value) field('conversation_id').value=chapterId();
    const root=document.createElement('section');
    root.style.cssText='padding:14px;background:linear-gradient(135deg,#211a32,#152c31);border:1px solid #ba9957;border-radius:12px;color:#eee;display:flex;flex-direction:column;gap:10px;box-sizing:border-box;height:100%;font:13px sans-serif';
    const title=document.createElement('strong');title.textContent='✦ GRIMOIRE · Your living spellbook';
    const notice=document.createElement('small');notice.textContent='Saved chats on this server · Send chats only · Generate image runs the workflow';
    const status=document.createElement('div');status.setAttribute('role','status');
    const history=document.createElement('div');history.style.cssText='overflow:auto;flex:1;min-height:180px;white-space:pre-wrap;user-select:text';history.setAttribute('aria-label','Conversation history');history.setAttribute('role','log');
    const summary=document.createElement('textarea');summary.readOnly=true;summary.setAttribute('aria-label','Current compacted memory');summary.style.cssText='min-height:65px;width:100%;box-sizing:border-box;background:#151620;color:#ddd';summary.placeholder='Compacted memory appears here. System, task and pinned fields remain separate.';
    const chats=document.createElement('select');chats.setAttribute('aria-label','Saved chats');chats.style.cssText='width:100%;padding:8px;background:#18202d;color:#eee';
    const composer=document.createElement('textarea');composer.setAttribute('aria-label','Message Grimoire');composer.placeholder='Message Grimoire… Enter to send · Shift+Enter for a new line';composer.style.cssText='min-height:100px;width:100%;box-sizing:border-box;background:#101722;color:#eee;padding:12px;border:1px solid #b69962;border-radius:8px';
    const buttons=document.createElement('div');buttons.style.cssText='display:flex;flex-wrap:wrap;gap:6px';
    let latest='', busy=false, requestVersion=0, layout;const actions=new Map();
    function render(value) {
        history.replaceChildren();
        for(const turn of value.turns||[]) {
            const item=document.createElement('div');item.className='gm-message '+(turn.role==='user'?'gm-user':'gm-assistant');
            const role=document.createElement('small');role.className='gm-role';role.textContent=turn.role==='user'?'You':'Grimoire';item.append(role);
            renderMarkdown(item,turn.content,async text=>{try{await navigator.clipboard.writeText(text);status.textContent='Copied';}catch{status.textContent='Clipboard unavailable · select the text to copy';}});history.append(item);
        }
        if(!(value.turns||[]).length){const empty=document.createElement('div');empty.className='gm-empty';empty.textContent='✦\nWhat would you like to create?\nStart a conversation, or open a saved chat above.';history.append(empty);}
        latest=[...(value.turns||[])].reverse().find(t=>t.role==='assistant')?.content||'';
        summary.value=value.summary||'';
        for(const [name,content] of Object.entries(value.settings||{}))if(field(name)&&name!=='conversation_id')field(name).value=content;
        status.textContent=value.report?.compacted?'Older turns compacted · inspect the summary':`${(value.turns||[]).length} saved messages`;
        if(value.report?.note)status.textContent+=' · '+value.report.note;
        history.scrollTop=history.scrollHeight;controls();
    }
    async function listChats(){
        try{const r=await api.fetchApi('/prompt_mage/grimoire/chats',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!r.ok)throw Error();const value=await r.json();
            chats.replaceChildren();const current=field('conversation_id').value;
            const add=(id,title)=>{const option=document.createElement('option');option.value=id;option.textContent=title;chats.append(option);};
            if(!(value.chats||[]).some(c=>c.id===current))add(current,'New conversation (not saved yet)');
            for(const c of value.chats||[])add(c.id,c.title+' · '+new Date(c.updated*1000).toLocaleDateString());chats.value=current;
        }catch{status.textContent='Could not list saved chats. Update/restart ComfyUI.';}
    }
    chats.addEventListener('change',()=>{if(busy){chats.value=field('conversation_id').value;return;}field('conversation_id').value=chats.value;field('summary_override').value='';composer.value='';void load();});
    composer.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();void run('Send');}});
    async function load() {
        const version=++requestVersion;
        try {const response=await api.fetchApi('/prompt_mage/grimoire/history',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:field('conversation_id').value})});if(!response.ok)throw Error();const value=await response.json();if(version===requestVersion){render(value);controls();}await listChats();}
        catch{status.textContent='History unavailable · start/restart ComfyUI or check the chapter ID';}
    }
    async function run(action) {
        if(busy)return;
        if(action==='Clear conversation'&&!window.confirm('Clear this chapter’s saved history and summary? Configured instructions and pinned facts remain.'))return;
        if(action==='Send'&&!composer.value.trim()){status.textContent='Write a message first.';return;}
        busy=true;controls();status.textContent='Queueing '+action+'…';field('message').value=composer.value;
        try{const snapshot=await app.graphToPrompt();const job=chatPrompt(snapshot,node.id,action,composer.value);const result=await api.queuePrompt(0,job);if(!result?.prompt_id||Object.keys(result.node_errors||{}).length)throw Error();
            status.textContent='Waiting for Grimoire…';
            if(action==='Send'){const pending=document.createElement('div');pending.className='gm-message gm-user';pending.textContent=composer.value;history.append(pending);composer.value='';history.scrollTop=history.scrollHeight;}} catch(error){busy=false;controls();status.textContent='Could not queue: '+(error?.message||'Check ComfyUI status.');}
    }
    function button(label, callback) {actions.set(label,callback);const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',callback);buttons.append(b);}
    button('Send',()=>void run('Send'));
    button('Next step',()=>void run('Next step'));
    button('Regenerate',()=>void run('Regenerate'));
    button('Compact now',()=>void run('Compact now'));
    button('Clear conversation',()=>void run('Clear conversation'));
    button('New chat',()=>{if(busy){status.textContent='Wait for this queued turn to finish or cancel it first.';return;}field('conversation_id').value=chapterId();field('summary_override').value='';composer.value='';render({turns:[],summary:''});void load();});
    button('Refresh history',()=>void load());
    button('Copy latest',async()=>{try{await navigator.clipboard.writeText(latest);status.textContent='Latest response copied';}catch{status.textContent='Clipboard unavailable · select and copy the response';}});
    button('Edit summary',()=>{field('summary_override').value=summary.value;status.textContent='Edit Summary override below; it is applied on the next successful run.';});
    button('Generate image',async()=>{if(busy||!latest){status.textContent='Finish a chat response first.';return;}busy=true;field('action').value='Use latest';try{await app.queuePrompt(0,1);}catch{busy=false;status.textContent='Could not queue image workflow.';}});
    button('Refresh chats',()=>void listChats());
    layout=layoutGrimoire(root,{title,status,chats,history,summary,composer,actions,field,changed:()=>controls()});
    // An unset maximum lets ComfyUI allocate extra node height to the chat.
    node.addDOMWidget('grimoire_chat','GRIMOIRE_CHAT',root,{serialize:false,getMinHeight:()=>560,hideOnZoom:true}).serialize=false;
    const chatWidget=node.widgets?.find(w=>w.name==='grimoire_chat');if(chatWidget)node.widgets=[chatWidget,...node.widgets.filter(w=>w!==chatWidget)];
    installOpenAIKeyWidget(node,api,layout.keyMount);installDeepSeekKeyWidget(node,api,layout.keyMount);
    function controls() {
        const backend=field('assistant_backend')?.value;
        for(const widget of node.widgets||[]){
            if(widget.name==='grimoire_chat')continue;
            widget.hidden=true;widget.computeSize=()=>[0,-4];
            widget.computeLayoutSize=()=>({minHeight:0,maxHeight:0,minWidth:0});
            if(widget.element?.style)widget.element.style.display='none';
            if(widget.inputEl?.style)widget.inputEl.style.display='none';
        }
        layout?.sync(backend,busy,Boolean(latest));
        refreshOpenAIKeyWidget(node);refreshDeepSeekKeyWidget(node);
        const minimum=node.computeSize();
        node.setSize([Math.max(650,node.size[0],minimum[0]),Math.max(node.size[1],minimum[1])]);node.setDirtyCanvas(true,true);
    }
    const callback=field('assistant_backend').callback;
    field('assistant_backend').callback=function(...args){callback?.apply(this,args);controls();};
    const idCallback=field('conversation_id').callback;
    field('conversation_id').callback=function(...args){idCallback?.apply(this,args);void load();};
    const executed=node.onExecuted;node.onExecuted=function(message){busy=false;executed?.apply(this,arguments);if(message.grimoire?.[0]){render(message.grimoire[0]);composer.value='';void listChats();}};
    const failed=()=>{busy=false;controls();status.textContent='Execution ended or failed. Review the ComfyUI error before retrying.';};
    api.addEventListener('execution_error',failed);api.addEventListener('execution_interrupted',failed);
    const removed=node.onRemoved;node.onRemoved=function(){api.removeEventListener('execution_error',failed);api.removeEventListener('execution_interrupted',failed);removed?.apply(this,arguments);};
    const configured=node.onConfigure;node.onConfigure=function(){configured?.apply(this,arguments);for(const name of ['width','height'])if(this.addInput&&!this.inputs?.some(slot=>slot.name===name))this.addInput(name,'INT',{shape:7,tooltip:'Connect matching Resolution '+name+' for canvas context.'});if(!field('conversation_id').value)field('conversation_id').value=chapterId();controls();void load();};
    controls();Promise.resolve().then(controls);void load();
}

app.registerExtension({name:'PromptMage.Grimoire',beforeRegisterNodeDef(type,data){
    if(data.name!=='DanbooruTagsTransformerGrimoire')return;
    const created=type.prototype.onNodeCreated;
    type.prototype.onNodeCreated=function(){created?.apply(this,arguments);installGrimoire(this);};
}});
