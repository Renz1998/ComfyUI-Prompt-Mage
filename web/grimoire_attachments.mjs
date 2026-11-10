const TYPES='.png,.jpg,.jpeg,.webp,.gif,.bmp,.tif,.tiff,.txt,.md,.markdown,.json,.csv,.tsv,.pdf,.docx,.yaml,.yml,.toml,.log,.py,.js,.ts,.html,.css,.xml,.ini,.sql,.rst';
export function installAttachments({root,mount,buttonMount,api,notify,changed}){
    const make=(tag,text)=>{const e=document.createElement(tag);if(text)e.textContent=text;return e;};
    mount.hidden=true;
    const picker=make('input');picker.type='file';picker.multiple=true;picker.accept=TYPES;picker.hidden=true;picker.setAttribute('aria-label','Choose reference attachments');
    const button=make('button','Attach');button.type='button';button.title='Drop files onto this chat or browse. Up to 6 files, 16 MB each. Images, text/code, PDF text and DOCX. Files go to this ComfyUI server; Send shares references with your selected assistant.';
    const list=make('div');list.className='gm-attachment-list';mount.append(picker,list);buttonMount.append(button);
    let selected=[],uploads=0,epoch=0,dead=false;const cache=new Map();
    const update=()=>{list.replaceChildren();for(const file of selected){
        const chip=make('div');chip.className='gm-attachment';
        if(file.kind==='image'&&file.preview){const img=make('img');img.src=file.preview;img.alt=file.name;chip.append(img);}
        const name=make('span',file.name+(file.truncated?' · excerpt':''));name.title=file.truncated?'Only the first 24,000 text characters / up to 16 PDF pages are read.':file.name;chip.append(name);
        const remove=make('button','×');remove.type='button';remove.title='Remove from this message; saved server files are retained.';remove.setAttribute('aria-label','Remove attachment '+file.name);remove.addEventListener('click',()=>{selected=selected.filter(f=>f.id!==file.id);update();});chip.append(remove);list.append(chip);
    }mount.hidden=!selected.length&&!uploads;button.disabled=uploads>0;button.textContent=uploads?'Uploading…':'Attach';changed?.();};
    async function metadata(ref){
        if(cache.has(ref.id))return cache.get(ref.id);
        const response=await api.fetchApi('/prompt_mage/grimoire/attachment/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:ref.id})});
        const value=await response.json();if(!response.ok)throw Error(value.error||'Attachment unavailable.');cache.set(ref.id,value);return value;
    }
    async function addFiles(files){
        const generation=epoch;uploads++;update();
        try{for(const file of files){
            if(dead||generation!==epoch)break;
            if(selected.length>=6){notify('Six attachments per message. Remove one before adding more.');break;}
            if(!file.size||file.size>16*1024*1024){notify(file.name+': choose a nonempty file under 16 MB.');continue;}
            try{
                const form=new FormData();form.append('file',file,file.name);
                const response=await api.fetchApi('/prompt_mage/grimoire/attachment',{method:'POST',body:form});const value=await response.json();
                if(!response.ok||!value.id||!['image','text'].includes(value.kind))throw Error(value.error||'Upload rejected. Update/restart Prompt Mage.');
                if(dead||generation!==epoch)break;
                cache.set(value.id,value);selected.push(value);update();notify(value.name+' attached'+(value.truncated?' · only an excerpt will be read.':'.'));
            }catch(error){notify(file.name+': '+error.message);}
        }}finally{uploads--;if(!dead)update();}
    }
    button.addEventListener('click',()=>picker.click());picker.addEventListener('change',()=>{void addFiles(Array.from(picker.files||[]));picker.value='';});
    const over=event=>{if(Array.from(event.dataTransfer?.types||[]).includes('Files')){event.preventDefault();event.stopPropagation();root.classList.add('gm-dragging');}};
    const leave=()=>root.classList.remove('gm-dragging');
    const drop=event=>{if(!event.dataTransfer?.files?.length)return;event.preventDefault();event.stopPropagation();leave();void addFiles(Array.from(event.dataTransfer.files));};
    const paste=event=>{const files=Array.from(event.clipboardData?.files||[]);if(files.length){event.preventDefault();event.stopPropagation();void addFiles(files);}};
    root.addEventListener('dragover',over);root.addEventListener('dragleave',leave);root.addEventListener('drop',drop);root.addEventListener('paste',paste);
    return {
        get busy(){return uploads>0;},ids(){return selected.map(f=>f.id);},
        consume(ids){selected=selected.filter(f=>!ids.includes(f.id));update();},
        clear(){epoch++;selected=[];update();},
        async reuse(refs){const generation=epoch;for(const ref of refs||[]){if(selected.some(f=>f.id===ref.id)||selected.length>=6)continue;try{const file=await metadata(ref);if(generation===epoch&&!dead&&!selected.some(f=>f.id===file.id))selected.push(file);}catch(error){notify(error.message);}}if(!dead)update();},
        renderSaved(parent,refs){if(!refs?.length)return;const saved=make('div');saved.className='gm-saved-attachments';parent.append(saved);for(const ref of refs){
            const details=make('details'),label=make('summary',ref.name+(ref.truncated?' · excerpt':'')),body=make('div');details.append(label,body);saved.append(details);
            let loaded=false;details.addEventListener('toggle',async()=>{if(!details.open||loaded)return;loaded=true;try{const file=await metadata(ref);if(file.kind==='image'){const img=make('img');img.src=file.preview;img.alt=file.name;body.append(img);}else body.append(make('pre',file.excerpt||''));}catch(error){body.append(make('small',error.message));}});
            const again=make('button','Attach again');again.type='button';again.addEventListener('click',()=>void this.reuse([ref]));body.append(again);
        }},
        destroy(){dead=true;epoch++;root.removeEventListener('dragover',over);root.removeEventListener('dragleave',leave);root.removeEventListener('drop',drop);root.removeEventListener('paste',paste);cache.clear();selected=[];}
    };
}
