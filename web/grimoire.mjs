import { ensureCanvasInputs } from './grimoire_sockets.mjs?v=1.19.2';
import { layoutGrimoire } from './grimoire_layout.mjs?v=1.19.2';
import { chatPrompt, queueChat } from './grimoire_queue.mjs?v=1.19.2';
import { renderMarkdown } from './grimoire_markdown.mjs?v=1.19.2';
import { app } from '../../scripts/app.js';
import { api } from '../../scripts/api.js';
import { installOpenAIKeyWidget, refreshOpenAIKeyWidget } from './openai_key.mjs?v=1.19.2';
import { installDeepSeekKeyWidget, refreshDeepSeekKeyWidget } from './deepseek_key.mjs?v=1.19.2';

// Plain text only: model/user messages never become executable HTML.
export function installGrimoire(node) {
    ensureCanvasInputs(node);
    const chapterId=()=>{
        if(typeof crypto.randomUUID==='function')return crypto.randomUUID();
        const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);
        return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
    };
    const field = name => node.widgets?.find(w=>w.name===name);
    const fieldDefaults=new Map((node.widgets||[]).map(w=>[w.name,w.value]));
    const legacyFields=['conversation_id','system_prompt','task_instructions','pinned_facts','message','action','assistant_backend','openai_model','deepseek_model','local_model','thinking','max_tokens','auto_compact','summary_override','output_selection','json_field','unload_after_generation'];
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
    const targets=document.createElement('select');targets.setAttribute('aria-label','Spell Scroll destination');
    const active=document.createElement('div'),activeTitle=document.createElement('strong'),activePreview=document.createElement('pre');active.append(activeTitle,activePreview);activeTitle.textContent='Active prompt: none applied';activePreview.style.cssText='white-space:pre-wrap;max-height:160px;overflow:auto';
    node.properties ||= {};
    function destinations(){
        const readers=(node.graph?._nodes||app.graph?._nodes||[]).filter(n=>(n.comfyClass||n.type)==='DanbooruTagsTransformerSpellScroll');
        const ids=readers.map(n=>n.widgets?.find(w=>w.name==='scroll_id')?.value).filter(Boolean);
        targets.replaceChildren();targets.disabled=!ids.length;if(!ids.length){const empty=document.createElement('option');empty.value='';empty.textContent='Add a Spell Scroll node to apply prompts';targets.append(empty);}for(const id of [...new Set(ids)]){const o=document.createElement('option');o.value=id;o.textContent='Spell Scroll: '+id;targets.append(o);}
        targets.value=ids.includes(node.properties.mage_scroll_id)?node.properties.mage_scroll_id:ids[0]||'';
        node.properties.mage_scroll_id=targets.value;
    }
    async function activePrompt(){
        if(!targets.value){activeTitle.textContent='Active prompt: add a Spell Scroll node';activePreview.textContent='Connect Spell Scroll.prompt to your positive encoder. Chat is independent.';return;}
        const requested=targets.value;try{const r=await api.fetchApi('/prompt_mage/grimoire/scroll',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scroll_id:requested})});if(!r.ok)throw Error();const v=(await r.json()).active;if(targets.value!==requested)return;activeTitle.textContent=v?'Active prompt: '+v.title+' · response '+(v.response_index+1):'Active prompt: none applied';activePreview.textContent=v?.text||'Choose Use this prompt on an assistant response. Chatting will not replace it.';}catch{activeTitle.textContent='Could not load active prompt';}
    }
    targets.addEventListener('change',()=>{node.properties.mage_scroll_id=targets.value;void activePrompt();});
    async function applyResponse(index,text,chapter,mode){
        if(busy)return;destinations();if(!targets.value){status.textContent='Add a Spell Scroll node first and connect its prompt output to the image encoder.';return;}
        try{const r=await api.fetchApi('/prompt_mage/grimoire/scroll',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({apply:true,scroll_id:targets.value,conversation_id:chapter,index,text,mode:mode||field('output_selection')?.value||'Latest response',field:field('json_field')?.value||''})});const v=await r.json();if(!r.ok)throw Error(v.error);status.textContent='Prompt applied. Run the image workflow to use it; no assistant call is needed.';await activePrompt();}catch(error){status.textContent='Could not apply prompt: '+error.message;}
    }
    let latest='', busy=false, requestVersion=0, layout, pendingEdit=null;const actions=new Map();
    function render(value) {
        history.replaceChildren();
        for(const [index,turn] of (value.turns||[]).entries()) {
            const item=document.createElement('div');item.className='gm-message '+(turn.role==='user'?'gm-user':'gm-assistant');
            const role=document.createElement('small');role.className='gm-role';role.textContent=turn.role==='user'?'You':'Grimoire';item.append(role);
            const copy=async text=>{try{await navigator.clipboard.writeText(text);status.textContent='Copied';}catch{status.textContent='Clipboard unavailable · select the text to copy';}};
            renderMarkdown(item,turn.content,copy);
            const tools=document.createElement('div');tools.className='gm-message-actions';
            const action=(label,fn)=>{const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',()=>{if(label==='Copy'||!busy)return fn();});tools.append(b);return b;};
            action('Copy',()=>void copy(turn.content));
            const chapter=field('conversation_id').value;
            const branch=()=>index>=value.turns.length-(turn.role==='user'?2:1)||window.confirm('This replaces later messages in this chat after the edit succeeds. The applied Spell Scroll stays unchanged. Continue?');
            if(turn.role==='user'){
                action('Edit',()=>{if(!branch())return;pendingEdit={index,original:turn.content,chapter};composer.value=turn.content;layout?.setEditing(true);composer.focus?.();status.textContent='Editing your message · Send edited message makes a new request.';});
                action('Resend',()=>{if(branch())void run('Edit message',turn.content,index,turn.content);});
            }else{
                action('Retry',()=>{const previous=value.turns[index-1];if(previous?.role==='user'&&branch())void run('Edit message',previous.content,index-1,previous.content);});
                action('Edit',()=>{
                    if(!branch())return;
                    const editor=document.createElement('textarea');editor.value=turn.content;editor.setAttribute('aria-label','Edit assistant response');item.append(editor);
                    const save=action('Save edit (no API call)',async()=>{
                        try{save.disabled=true;const r=await api.fetchApi('/prompt_mage/grimoire/message',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:chapter,index,original:turn.content,text:editor.value})});const v=await r.json();if(!r.ok)throw Error(v.error);if(field('conversation_id').value===chapter)render(v);status.textContent='Response edited · applied Spell Scroll unchanged';}catch(error){save.disabled=false;status.textContent=error.message;}
                    });action('Cancel',()=>render(value));editor.focus?.();
                });
                const apply=action('Use this prompt',()=>void applyResponse(index,turn.content,chapter,turn.mode));
                apply.disabled=turn.valid===false;if(turn.valid===false)apply.title='Invalid prompt format. Edit this reply or retry before applying.';
            }
            item.append(tools);history.append(item);
        }
        if(!(value.turns||[]).length){const empty=document.createElement('div');empty.className='gm-empty';empty.textContent='✦\nWhat would you like to create?\nStart a conversation, or open a saved chat above.';history.append(empty);}
        latest=[...(value.turns||[])].reverse().find(t=>t.role==='assistant')?.content||'';
        summary.value=value.summary||'';
        for(const [name,content] of Object.entries(value.settings||{}))if(field(name)&&name!=='conversation_id')field(name).value=content;
        status.textContent=value.report?.compacted?'Older turns compacted · inspect the summary':'';
        if(value.report?.note)status.textContent+=(status.textContent?' · ':'')+value.report.note;
        history.scrollTop=history.scrollHeight;controls();
    }
    async function listChats(){
        try{const r=await api.fetchApi('/prompt_mage/grimoire/chats',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});if(!r.ok)throw Error();const value=await r.json();
            destinations();void activePrompt();
            chats.replaceChildren();const current=field('conversation_id').value;
            const add=(id,title)=>{const option=document.createElement('option');option.value=id;option.textContent=title;chats.append(option);};
            if(!(value.chats||[]).some(c=>c.id===current))add(current,'New conversation (not saved yet)');
            for(const c of value.chats||[])add(c.id,c.title+' · '+new Date(c.updated*1000).toLocaleDateString());chats.value=current;
        }catch{status.textContent='Could not list saved chats. Update/restart ComfyUI.';}
    }
    chats.addEventListener('change',()=>{if(busy){chats.value=field('conversation_id').value;return;}field('conversation_id').value=chats.value;field('summary_override').value='';composer.value='';pendingEdit=null;layout?.setEditing(false);void load();});
    composer.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();void run('Send');}});
    async function load() {
        const version=++requestVersion;
        try {const response=await api.fetchApi('/prompt_mage/grimoire/history',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:field('conversation_id').value})});if(!response.ok){let error={};try{error=await response.json();}catch{}throw Error('HTTP '+response.status+': '+(error.error||'History endpoint unavailable; restart the updated backend.'));}const value=await response.json();if(version===requestVersion){render(value);controls();}await listChats();}
        catch(error){status.textContent='History unavailable · '+(error.message||'Check the server connection.');}
    }
    async function run(action, text=composer.value, editIndex=-1, original='') {
        if(busy)return;
        if(action==='Send'&&pendingEdit){if(pendingEdit.chapter!==field('conversation_id').value){status.textContent='Chat changed; cancel the edit first.';return;}action='Edit message';editIndex=pendingEdit.index;original=pendingEdit.original;}
        if(action==='Clear conversation'&&!window.confirm('Clear this chapter’s saved history and summary? Configured instructions and pinned facts remain.'))return;
        if(['Send','Edit message'].includes(action)&&!text.trim()){status.textContent='Write a message first.';return;}
        busy=true;controls();status.textContent='Queueing '+action+'…';field('message').value=text;
        try{const snapshot=await app.graphToPrompt();const job=chatPrompt(snapshot,node.id,action,text);job.output[String(node.id)].inputs.edit_index=editIndex;job.output[String(node.id)].inputs.edit_original=original;const result=await queueChat(api,job,node.id);if(!result?.prompt_id||Object.keys(result.node_errors||{}).length)throw Error();
            status.textContent='Waiting for Grimoire…';
            if(['Send','Edit message'].includes(action)){pendingEdit=null;layout?.setEditing(false);const pending=document.createElement('div');pending.className='gm-message gm-user';pending.textContent=text;history.append(pending);composer.value='';history.scrollTop=history.scrollHeight;}} catch(error){busy=false;controls();status.textContent='Could not queue: '+(error?.message||'Check ComfyUI status.');}
    }
    function button(label, callback) {actions.set(label,callback);const b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',callback);buttons.append(b);}
    button('Send',()=>void run('Send'));
    actions.set('Cancel edit',()=>{pendingEdit=null;composer.value='';layout?.setEditing(false);status.textContent='Edit cancelled';});
    button('Next step',()=>void run('Next step'));
    button('Regenerate',()=>void run('Regenerate'));
    button('Compact now',()=>void run('Compact now'));
    button('Clear conversation',()=>void run('Clear conversation'));
    button('New chat',()=>{if(busy){status.textContent='Wait for this queued turn to finish or cancel it first.';return;}field('conversation_id').value=chapterId();field('summary_override').value='';composer.value='';pendingEdit=null;layout?.setEditing(false);render({turns:[],summary:''});void load();});
    button('Refresh history',()=>void load());
    button('Copy latest',async()=>{try{await navigator.clipboard.writeText(latest);status.textContent='Latest response copied';}catch{status.textContent='Clipboard unavailable · select and copy the response';}});
    button('Edit summary',()=>{field('summary_override').value=summary.value;status.textContent='Edit Summary override below; it is applied on the next successful run.';});
    button('Refresh chats',()=>void listChats());
    layout=layoutGrimoire(root,{title,status,chats,history,summary,composer,actions,field,targets,active,changed:name=>{controls();if(['style_preset','style_notes'].includes(name))status.textContent='Style updated · applies with your next message; no request sent.';}});
    // An unset maximum lets ComfyUI allocate extra node height to the chat.
    node.addDOMWidget('grimoire_chat','GRIMOIRE_CHAT',root,{serialize:false,getMinHeight:()=>560,hideOnZoom:true}).serialize=false;
    const chatWidget=node.widgets?.find(w=>w.name==='grimoire_chat');if(chatWidget)node.widgets=[chatWidget,...node.widgets.filter(w=>w!==chatWidget)];
    installOpenAIKeyWidget(node,api,layout.keyMount);installDeepSeekKeyWidget(node,api,layout.keyMount);
    function controls() {
        ensureCanvasInputs(node);
        if(field('action'))field('action').value='Use latest';
        if(field('chat_mode'))field('chat_mode').value='Conversation';
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
    const executed=node.onExecuted;node.onExecuted=function(message){busy=false;executed?.apply(this,arguments);if(message.grimoire?.[0]){render(message.grimoire[0]);void listChats();}};
    const failed=()=>{busy=false;controls();status.textContent='Execution ended or failed. Review the ComfyUI error before retrying.';};
    api.addEventListener('execution_error',failed);api.addEventListener('execution_interrupted',failed);
    const removed=node.onRemoved;node.onRemoved=function(){api.removeEventListener('execution_error',failed);api.removeEventListener('execution_interrupted',failed);removed?.apply(this,arguments);};
    const serialized=node.onSerialize;node.onSerialize=function(data){serialized?.apply(this,arguments);data.properties ||= {};data.properties.mage_grimoire_size=Array.from(this.size);data.mage_grimoire_fields=Object.fromEntries((this.widgets||[]).filter(w=>w.serialize!==false).map(w=>[w.name,w.value]));};
    const configured=node.onConfigure;node.onConfigure=function(data){const saved=data?.properties?.mage_grimoire_size||data?.size;configured?.apply(this,arguments);if(data?.mage_grimoire_fields){for(const [name,value]of Object.entries(data.mage_grimoire_fields))if(field(name))field(name).value=value;}else if(Array.isArray(data?.widgets_values)){legacyFields.forEach((name,i)=>{if(field(name)&&i<data.widgets_values.length)field(name).value=data.widgets_values[i];});for(const name of ['chat_mode','style_preset','style_notes','edit_original','edit_index'])if(field(name))field(name).value=fieldDefaults.get(name);for(const [i,name]of [[17,'width'],[18,'height']])if(field(name)&&Number.isFinite(data.widgets_values[i]))field(name).value=data.widgets_values[i];}if(Array.isArray(saved)&&saved.length===2&&saved.every(Number.isFinite))this.setSize(saved);ensureCanvasInputs(this);if(!field('conversation_id').value)field('conversation_id').value=chapterId();controls();void load();};
    controls();Promise.resolve().then(controls);void load();
}

app.registerExtension({name:'PromptMage.Grimoire',beforeRegisterNodeDef(type,data){
    if(data.name!=='DanbooruTagsTransformerGrimoire')return;
    const created=type.prototype.onNodeCreated;
    type.prototype.onNodeCreated=function(){created?.apply(this,arguments);installGrimoire(this);};
}});
