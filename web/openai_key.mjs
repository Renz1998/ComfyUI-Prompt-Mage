const panels = new WeakMap();

export function refreshOpenAIKeyWidget(node) {
    const panel = panels.get(node);
    if (!panel) return;
    panel.widget.hidden = panel.root.hidden = node.widgets?.find(w => w.name === 'assistant_backend')?.value !== 'OpenAI API';
}

export function installOpenAIKeyWidget(node, api, container=null) {
    if (panels.has(node)) return;
    const root = document.createElement('section'); root.className = 'mage-api-key';
    const bar = document.createElement('div'); bar.className = 'mage-api-key-bar';
    const status = document.createElement('span'); status.setAttribute('role','status');
    const change = document.createElement('button'); change.type='button'; change.textContent='Add / replace key';
    const form = document.createElement('div'); form.className='mage-api-key-form';
    const input = document.createElement('input'); input.type='password'; input.autocomplete='off';
    input.placeholder='Paste OpenAI API key'; input.setAttribute('aria-label','OpenAI API key (not saved in workflow)');
    const save = document.createElement('button'); save.type='button'; save.textContent='Add key';
    const remove = document.createElement('button'); remove.type='button'; remove.textContent='Remove saved key';
    const help = document.createElement('small');
    help.textContent='Shared by this ComfyUI server. Saved in this server’s ComfyUI user directory; use persistent pod storage. Never included in workflows. API charges apply. Use a trusted/private server connection.';
    bar.append(status,change); form.append(input,save,remove); root.append(bar,form,help);
    let open=true, busy=false, session=false;
    const height=()=>open?166:96;
    const widget=container ? {serialize:false,hidden:false} : node.addDOMWidget('mage_openai_key','MAGE_OPENAI_KEY',root,
        {serialize:false,getMinHeight:height,getMaxHeight:height,hideOnZoom:true});
    if(container)container.append(root);
    widget.serialize=false;
    const resize=()=>{form.hidden=!open;if(container){node.setDirtyCanvas(true,true);return;}const size=node.computeSize();node.setSize([Math.max(500,node.size[0],size[0]),size[1]]);node.setDirtyCanvas(true,true);};
    const render=data=>{
        session=Boolean(data.session_configured || data.saved_configured);
        status.textContent=data.configured?(data.saved_configured?'✓ API key saved on this server':session?'✓ API key configured for this session':'✓ Using server environment key'):'API key not configured';
        remove.disabled=!session; open=!data.configured; input.value=''; resize();
    };
    const read=async()=>{
        try{const response=await api.fetchApi('/prompt_mage/openai/key');if(!response.ok)throw Error();render(await response.json());}
        catch{status.textContent='Key panel unavailable · restart ComfyUI after updating';}
    };
    const write=async key=>{
        if(busy)return;
        busy=true;save.disabled=change.disabled=remove.disabled=true;
        try{
            const response=await api.fetchApi('/prompt_mage/openai/key',{method:'POST',
                headers:{'Content-Type':'application/json'},body:JSON.stringify({key})});
            if(!response.ok){status.textContent='Key not saved · check format, storage permissions and connection';return;}
            render(await response.json());
            window.dispatchEvent(new Event('prompt-mage-openai-key-changed'));
        }catch{status.textContent='Key not added · check server connection';}
        finally{busy=false;save.disabled=change.disabled=false;remove.disabled=!session;}
    };
    change.addEventListener('click',()=>{open=!open;if(!open)input.value='';resize();});
    save.addEventListener('click',()=>{const key=input.value.trim();if(!key){status.textContent='Paste a key first';return;}void write(key);});
    remove.addEventListener('click',()=>void write(''));
    const onChange=()=>void read();window.addEventListener('prompt-mage-openai-key-changed',onChange);
    const removed=node.onRemoved;
    node.onRemoved=function(){window.removeEventListener('prompt-mage-openai-key-changed',onChange);input.value='';removed?.apply(this,arguments);};
    panels.set(node,{root,widget});refreshOpenAIKeyWidget(node);void read();
}
