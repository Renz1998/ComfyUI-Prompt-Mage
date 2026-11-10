import {grimoireTheme} from './grimoire_theme.mjs?v=1.22.1';
let layoutCounter=0;
export function layoutGrimoire(root, {title,status,chats,history,summary,composer,actions,field,targets,active,changed}) {
    const layoutId='grimoire-panel-'+(++layoutCounter);
    const previousWidth=root.style.width,previousHeight=root.style.height;
    root.className='grimoire-app';root.style.cssText='height:100%;box-sizing:border-box';
    if(previousWidth)root.style.width=previousWidth;if(previousHeight)root.style.height=previousHeight;
    const make=(tag,cls,text)=>{const e=document.createElement(tag);e.className=cls||'';if(text)e.textContent=text;return e;};
    const style=make('style');style.textContent=`
    .grimoire-app{color-scheme:dark;--line:#41435a;--muted:#b7bfd0;background:#171b29;color:#eef1fa;border:1px solid #59506d;border-radius:14px;font:14px/1.45 system-ui,sans-serif;display:flex;flex-direction:column;overflow:hidden}
    .grimoire-app *{box-sizing:border-box}.grimoire-app [hidden]{display:none!important}
    .grimoire-app button,.grimoire-app select,.grimoire-app input,.grimoire-app textarea{font:inherit;color:inherit;border:1px solid var(--line);background:#252b3c;border-radius:8px;padding:9px 12px;min-height:38px}
    .grimoire-app button{cursor:pointer;font-weight:600;white-space:nowrap}.grimoire-app button:hover{background:#353d55}.grimoire-app button:focus-visible,.grimoire-app :is(select,input,textarea):focus-visible{outline:2px solid #c5a3ff;outline-offset:2px}.grimoire-app button:disabled{opacity:.5;cursor:default}
    .grimoire-app .gm-header,.grimoire-app .gm-chats,.grimoire-app .gm-footer{display:flex;align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid var(--line)}
    .grimoire-app :is(.gm-header,.gm-chats,.gm-tabs,.gm-status,.gm-composer,.gm-footer){flex-shrink:0}
    .grimoire-app .gm-header strong{font-size:17px;flex:0}.grimoire-app .gm-header button{font-size:12px;color:#d7c3fb}.grimoire-app .gm-header select{flex:1;min-width:0;width:0}
    .grimoire-app .gm-tabs{display:flex;gap:4px;padding:0 16px;border-bottom:1px solid var(--line)}.grimoire-app .gm-tabs button{border:0;border-radius:0;background:transparent;color:var(--muted);padding:7px 10px;min-height:32px}.grimoire-app .gm-tabs button[aria-selected=true]{color:#e5d3ff;box-shadow:inset 0 -3px #c2a0ff}
    .grimoire-app .gm-page{flex:1;min-height:0;display:flex;flex-direction:column;overflow:auto}.grimoire-app .gm-form{padding:18px;gap:16px}.grimoire-app .gm-form label{display:flex;flex-direction:column;gap:6px;font-weight:600}.grimoire-app small{font-size:12px;color:var(--muted);font-weight:400}.grimoire-app textarea{width:100%;resize:vertical;min-height:90px;background:#121725}
    .grimoire-app .gm-history{display:flex;flex-direction:column;gap:14px;flex:1;min-height:140px;padding:18px;overflow:auto;user-select:text}.grimoire-app .gm-status{padding:8px 18px;color:var(--muted);font-size:12px;border-bottom:1px solid var(--line)}
    .grimoire-app .gm-message{max-width:86%;padding:12px 16px;border-radius:16px;overflow-wrap:anywhere;flex-shrink:0}.grimoire-app .gm-user{align-self:flex-end;background:#674d94;border-bottom-right-radius:4px}.grimoire-app .gm-assistant{align-self:flex-start;background:#282f42;border-bottom-left-radius:4px}.grimoire-app .gm-role{display:block;margin-bottom:5px;color:#cfc8e1;font-size:11px}.grimoire-app .gm-message p{margin:4px 0}.grimoire-app .gm-empty{margin:auto;text-align:center;white-space:pre-line;color:var(--muted);padding:25px;line-height:2}
    .grimoire-app .gm-composer{padding:8px 12px;border-top:1px solid var(--line)}.grimoire-app .gm-composer textarea{min-height:60px;max-height:180px}.grimoire-app .gm-footer{padding:0 12px 10px;border:0;flex-wrap:wrap}.grimoire-app .gm-primary{background:#c8a6ff;color:#21172f;border-color:#c8a6ff}.grimoire-app .gm-spacer{flex:1}.grimoire-app details{border:1px solid var(--line);border-radius:8px;padding:10px}.grimoire-app summary{cursor:pointer;color:#d4c2ec}
    .grimoire-app .mage-api-key{padding:14px;border:1px solid var(--line);border-radius:10px;display:flex;flex-direction:column;gap:10px;background:#202638}.grimoire-app .mage-api-key-bar,.grimoire-app .mage-api-key-form{display:flex;gap:8px;flex-wrap:wrap}.grimoire-app .mage-api-key-bar span{flex:1}.grimoire-app .mage-api-key-form input{width:100%}.grimoire-app a{color:#ceadff}.grimoire-app pre{font-size:12px;max-width:100%;white-space:pre;overflow:auto}.grimoire-app pre code{white-space:pre;font:12px/1.6 ui-monospace,monospace;display:block}
    .grimoire-app .gm-message{min-width:0}.grimoire-app .gm-message strong{font-weight:750}.grimoire-app .gm-message em{font-style:italic}.grimoire-app .gm-message del{text-decoration:line-through}
    .grimoire-app .gm-message :is(h1,h2,h3,h4,h5,h6){font-weight:750;line-height:1.3;margin:14px 0 8px}.grimoire-app .gm-message h1{font-size:1.5em}.grimoire-app .gm-message h2{font-size:1.3em}.grimoire-app .gm-message h3{font-size:1.15em}
    .grimoire-app .gm-message :is(ul,ol){padding-left:24px;margin:8px 0}.grimoire-app .gm-message ul{list-style:disc}.grimoire-app .gm-message ol{list-style:decimal}.grimoire-app .gm-message li{display:list-item;margin:4px 0}
    .grimoire-app blockquote{border-left:3px solid #b99add;padding-left:12px;color:#cbd0df}.grimoire-app table{border-collapse:collapse;display:block;overflow:auto}.grimoire-app :is(th,td){border:1px solid var(--line);padding:6px;text-align:left}
    .grimoire-app .gm-message-actions{display:flex;flex-wrap:wrap;gap:6px;border-top:1px solid #ffffff18;margin-top:10px;padding-top:8px}.grimoire-app .gm-message-actions button{font-size:11px;padding:5px 8px;min-height:28px;background:transparent}.grimoire-app .gm-mode{flex-shrink:0;padding:10px 16px;border-bottom:1px solid var(--line)}
    .grimoire-app .gm-status:empty{display:none}
    .grimoire-app .gm-toolbar{display:flex;align-items:flex-start;flex-wrap:wrap;gap:8px;padding:8px 12px;border-bottom:1px solid var(--line);flex-shrink:0}
    .grimoire-app .gm-toolbar label{display:flex;flex:1;align-items:center;gap:8px;min-width:0;font-size:12px;font-weight:600}
    .grimoire-app .gm-toolbar label select{flex:1;min-width:0;width:0;padding:6px 8px;min-height:34px}
    .grimoire-app .gm-applied{padding:6px 9px;min-height:34px;font-size:12px;flex-shrink:0}
    .grimoire-app .gm-applied[open]{flex-basis:100%;max-height:260px;overflow:auto}
    .grimoire-app .gm-applied select{width:100%;margin:10px 0;font-size:12px}.grimoire-app .gm-applied strong{font-size:12px}.grimoire-app .gm-applied pre{margin-bottom:0}
    .grimoire-app.gm-dragging{outline:3px solid #c8a6ff;outline-offset:-4px}
    .grimoire-app .gm-attachment-list{display:flex;gap:6px;flex-wrap:wrap;max-height:140px;overflow:auto;margin-bottom:8px}
    .grimoire-app .gm-attachment{display:flex;align-items:center;gap:6px;background:#30364b;border:1px solid var(--line);border-radius:8px;padding:5px;max-width:100%}
    .grimoire-app .gm-attachment span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px;font-size:12px}.grimoire-app .gm-attachment img{width:40px;height:40px;object-fit:cover;border-radius:5px}
    .grimoire-app .gm-attachment button{min-height:26px;padding:2px 7px}.grimoire-app .gm-saved-attachments{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;font-size:12px}
    .grimoire-app .gm-saved-attachments img{display:block;max-width:192px;max-height:192px;margin:8px 0}.grimoire-app .gm-saved-attachments pre{max-height:160px;white-space:pre-wrap}.grimoire-app .gm-saved-attachments button{min-height:28px;padding:4px 8px}
    .grimoire-app .gm-format-note{display:block;margin:8px 0;padding:8px;border-left:3px solid #e5ad72;color:#f0c99f}
    .grimoire-app .gm-prompt pre,.grimoire-app .gm-prompt pre code{white-space:pre-wrap!important;overflow-wrap:anywhere}
    `;
    style.textContent+=grimoireTheme;
    const button=(name,fn,cls='')=>{const b=make('button',cls,name);b.type='button';b.addEventListener('click',fn);return b;};
    const invoke=name=>()=>actions.get(name)?.();
    const header=make('div','gm-header');title.textContent='✦ Grimoire';
    const provider=button('Settings',()=>tab('Settings'));title.textContent='✦';title.title='Grimoire';chats.style.cssText='';header.append(title,chats,button('＋ New chat',invoke('New chat')),provider);
    const tabs=make('div','gm-tabs');tabs.setAttribute('role','tablist');
    const chatPage=make('div','gm-page'),instructions=make('div','gm-page gm-form'),settings=make('div','gm-page gm-form');
    const pages={Chat:chatPage,Instructions:instructions,Settings:settings},tabButtons={};
    function tab(name){for(const [key,page]of Object.entries(pages)){page.hidden=key!==name;tabButtons[key]?.setAttribute('aria-selected',String(key===name));tabButtons[key]?.setAttribute('tabindex',key===name?'0':'-1');}}
    for(const [index,name] of Object.keys(pages).entries()){const b=button(name,()=>tab(name));b.id=layoutId+'-tab-'+index;b.setAttribute('role','tab');b.setAttribute('aria-controls',layoutId+'-'+index);pages[name].id=layoutId+'-'+index;pages[name].setAttribute('role','tabpanel');pages[name].setAttribute('aria-labelledby',b.id);b.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight'].includes(event.key))return;event.preventDefault();const names=Object.keys(pages),next=names[(index+(event.key==='ArrowRight'?1:2))%3];tab(next);tabButtons[next].focus();});tabButtons[name]=b;tabs.append(b);}
    const bindings=[];
    function control(parent,name,label,help){
        const widget=field(name);if(!widget)return;
        const row=make('label','',label),isCombo=Array.isArray(widget.options?.values),isText=['system_prompt','task_instructions','pinned_facts','summary_override','style_notes'].includes(name);
        const input=make(isCombo?'select':isText?'textarea':'input');input.setAttribute('aria-label',label);
        if(isCombo)for(const value of widget.options.values){const label=name==='output_selection'?({'Latest response':'Natural language / Markdown','JSON only':'Generic JSON (task schema)','JSON field':'JSON (extract field)'}[value]||value):value;const o=make('option','',label);o.value=value;input.append(o);}
        else if(typeof widget.value==='boolean')input.type='checkbox';else if(!isText)input.type=typeof widget.value==='number'?'number':'text';
        function sync(){if(input.type==='checkbox')input.checked=widget.value;else if(input.value!==String(widget.value))input.value=widget.value;}
        input.addEventListener('input',()=>{widget.value=input.type==='checkbox'?input.checked:input.type==='number'?Number(input.value):input.value;changed(name);});
        input.addEventListener('change',()=>{widget.value=input.type==='checkbox'?input.checked:input.type==='number'?Number(input.value):input.value;changed(name);});
        row.append(input);if(help)row.append(make('small','',help));parent.append(row);bindings.push({name,row,sync});sync();
    }
    control(instructions,'system_prompt','System prompt','The assistant’s role and general rules. Always included.');
    control(instructions,'task_instructions','Task instructions','What you are working on, your sequence and requested output format.');
    control(instructions,'pinned_facts','Pinned facts','Important details to keep through compaction. Appearance Overrides also applies every turn.');
    const modeBar=make('div','gm-toolbar');
    control(modeBar,'style_preset','Style / theme');
    const styleBinding=bindings.find(b=>b.name==='style_preset');if(styleBinding)styleBinding.row.title='Applies with your next message. Changing style makes no request. Ask Grimoire to create or revise a prompt when ready.';
    const applied=make('details','gm-applied');applied.append(make('summary','','Applied prompt'));if(targets){targets.title='Spell Scroll destination';applied.append(targets,active);modeBar.append(applied);}
    const production=button('Send brief → Foundry',invoke('Send brief to Foundry'));production.title='After agreeing on the project, prepare a saved production brief. One assistant request; no image generation.';modeBar.append(production);
    control(settings,'style_notes','Custom style notes');
    control(settings,'assistant_backend','Assistant provider','Choose OpenAI or DeepSeek below to add an API key. Local Qwen needs no API key.');
    const keyMount=make('div');settings.append(keyMount);
    const keyHint=make('small','','Local mode uses your connected CLIP or installed Qwen. Select an API provider to reveal its saved-key controls.');settings.append(keyHint);
    for(const [name,label]of [['openai_model','OpenAI model'],['deepseek_model','DeepSeek model'],['local_model','Local model'],['thinking','Thinking'],['max_tokens','Generation token limit'],['auto_compact','Automatically compact older messages'],['output_selection','Prompt format'],['json_field','JSON field'],['unload_after_generation','Unload local assistant after generation'],['width','Canvas width'],['height','Canvas height']])control(settings,name,label);
    const memory=make('details');memory.append(make('summary','','Conversation memory'));summary.style.cssText='';memory.append(summary,button('Edit summary',()=>{actions.get('Edit summary')?.();tab('Settings');}));
    const memoryEdit=make('details');memoryEdit.append(make('summary','','Advanced memory override'));control(memoryEdit,'summary_override','Summary override','Apply an edited summary on the next successful turn, then clear this field.');settings.append(memoryEdit);
    history.className='gm-history';history.style.cssText='';status.className='gm-status';
    const composerBox=make('div','gm-composer'),attachmentMount=make('div','gm-attachments'),attachmentButtonMount=make('div');composer.style.cssText='';composer.rows=2;composer.title='Enter to send · Shift+Enter for a new line';composerBox.append(attachmentMount,composer);
    const footer=make('div','gm-footer');const send=button('Send',invoke('Send'),'gm-primary');const cancelEdit=button('Cancel edit',invoke('Cancel edit'));cancelEdit.hidden=true;
    send.title='Send a new assistant request.';
    const thinking=button('✧ Thinking',()=>{const widget=field('thinking');if(!widget)return;widget.value=!Boolean(widget.value);changed('thinking');},'gm-thinking');
    thinking.setAttribute('aria-label','Thinking mode');
    thinking.title='Ask a supported model to spend more effort planning the next reply. May take longer and use more tokens. Support depends on the selected model. Changing this toggle sends no request.';
    const more=make('select');more.setAttribute('aria-label','Conversation actions');
    const blank=make('option','','More actions…');blank.value='';more.append(blank);
    for(const action of ['Send brief to Foundry','Next step','Regenerate','Copy latest','Refresh history','Refresh chats','Compact now','Clear conversation']){const option=make('option','',action==='Next step'?'Ask for next scene (new request)':action==='Regenerate'?'Rewrite reply (new request)':action==='Compact now'?'Compact memory (new request)':action);option.value=action;more.append(option);}
    more.addEventListener('change',()=>{actions.get(more.value)?.();more.value='';});
    footer.append(attachmentButtonMount,send,thinking,cancelEdit,make('div','gm-spacer'),more);
    chatPage.append(modeBar,history,memory,composerBox,footer);
    root.replaceChildren();root.append(style,header,tabs,status,chatPage,instructions,settings);tab('Chat');
    return {keyMount,attachmentMount,attachmentButtonMount,tab,setEditing(editing){cancelEdit.hidden=!editing;send.textContent=editing?'Send edited message':'Send';},sync(backend,busy,hasAnswer,hasFoundry=false){
        production.disabled=busy||!hasAnswer||!hasFoundry;production.title=hasFoundry?'Prepare the agreed production brief. One assistant request; no image render.':'Connect production_brief to Foundry first.';provider.title=backend+' · Open settings';send.disabled=busy;thinking.hidden=!field('thinking');thinking.disabled=busy;thinking.setAttribute('aria-pressed',String(Boolean(field('thinking')?.value)));thinking.textContent=field('thinking')?.value?'✧ Thinking · On':'✧ Thinking';
        for(const b of bindings){b.sync();b.row.hidden=b.name==='openai_model'?backend!=='OpenAI API':b.name==='deepseek_model'?backend!=='DeepSeek API':b.name==='local_model'?backend!=='Local Qwen':b.name==='json_field'?field('output_selection')?.value!=='JSON field':false;}
        keyHint.hidden=backend!=='Local Qwen';memory.hidden=!summary.value;
    }};
}
