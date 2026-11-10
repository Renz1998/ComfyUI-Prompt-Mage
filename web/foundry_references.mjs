export function installReferences({mount,api,changed,notify,max=12}){
    const make=(tag,text,parent)=>{const e=document.createElement(tag);if(text)e.textContent=text;parent?.append(e);return e;};
    mount.className='foundry-references';
    const bar=make('div','',mount);bar.className='ref-bar';
    const upload=make('button','Upload images',bar),folder=make('button','Folder',bar),clear=make('button','Clear',bar),count=make('small','0 / '+max,bar);
    for(const b of [upload,folder,clear])b.type='button';
    const hint=make('small','Drop images here · numbered in plan order · choose what to borrow below each image.',mount);
    const grid=make('div','',mount);grid.className='ref-grid';
    const picker=make('input','',mount);picker.type='file';picker.accept='image/*';picker.multiple=true;picker.hidden=true;picker.setAttribute('aria-label','Upload planning reference images');
    const directory=make('input','',mount);directory.type='file';directory.accept='image/*';directory.multiple=true;directory.webkitdirectory=true;directory.hidden=true;directory.setAttribute('aria-label','Choose planning reference folder');
    let files=[],busy=0,epoch=0,dead=false;
    const emit=()=>changed?.(files.map(f=>f.id),Object.fromEntries(files.map(f=>[f.id,f.role||'Reference'])));
    function render(){grid.replaceChildren();count.textContent=files.length+' / '+max+(busy?' · uploading…':'');upload.disabled=folder.disabled=!!busy;
        files.forEach((f,index)=>{const card=make('article','',grid);const img=make('img','',card);img.src=f.preview;img.alt='Image '+(index+1)+': '+f.name;
            const row=make('div','',card);make('strong',String(index+1),row);const remove=make('button','×',row);remove.type='button';remove.title='Remove '+f.name;remove.setAttribute('aria-label','Remove reference '+(index+1));remove.onclick=()=>{files=files.filter(v=>v.id!==f.id);render();emit();};
            const role=make('select','',card);role.setAttribute('aria-label','Image '+(index+1)+' role');for(const name of ['Reference','Outfit','Pose','Props','Setting','Visual style','Character']){const o=make('option',name,role);o.value=name;}role.value=f.role||'Reference';role.onchange=()=>{f.role=role.value;emit();};
            const order=make('div','',card);const left=make('button','←',order),right=make('button','→',order);left.type=right.type='button';left.disabled=index===0;right.disabled=index===files.length-1;left.setAttribute('aria-label','Move reference '+(index+1)+' earlier');right.setAttribute('aria-label','Move reference '+(index+1)+' later');
            function move(delta){const next=index+delta;[files[index],files[next]]=[files[next],files[index]];render();emit();}left.onclick=()=>move(-1);right.onclick=()=>move(1);card.title=f.name;
        });hint.hidden=files.length>0;
    }
    async function addFiles(values){const generation=epoch;busy++;render();try{for(const file of values){
        if(dead||generation!==epoch)break;if(files.length>=max){notify('Use up to '+max+' planning images. Remove one before adding more.');break;}
        if(!file.size||file.size>16*1024*1024){notify(file.name+': choose a nonempty image under 16 MB.');continue;}
        if(!file.type?.startsWith('image/')&&!/\.(png|jpe?g|webp|gif|bmp|tiff?)$/i.test(file.name))continue;
        const body=new FormData();body.append('file',file,file.name);
        try{const response=await api.fetchApi('/prompt_mage/grimoire/attachment',{method:'POST',body});const value=await response.json();if(!response.ok||value.kind!=='image')throw Error(value.error||'Choose a supported image.');if(dead||generation!==epoch)break;if(files.length>=max){notify('Reference limit reached.');break;}files.push({...value,role:'Reference'});render();emit();notify(value.name+' added to planning references.');}catch(e){notify(file.name+': '+e.message);}
    }}finally{busy--;if(!dead)render();}}
    upload.onclick=()=>picker.click();folder.onclick=()=>directory.click();picker.onchange=()=>{void addFiles(Array.from(picker.files||[]));picker.value='';};directory.onchange=()=>{void addFiles(Array.from(directory.files||[]));directory.value='';};
    clear.onclick=()=>{epoch++;files=[];render();emit();};
    const over=e=>{if(Array.from(e.dataTransfer?.types||[]).includes('Files')){e.preventDefault();e.stopPropagation();mount.classList.add('dragging');}};
    const leave=()=>mount.classList.remove('dragging');const drop=e=>{if(!e.dataTransfer?.files?.length)return;e.preventDefault();e.stopPropagation();leave();void addFiles(Array.from(e.dataTransfer.files));};
    mount.addEventListener('dragover',over);mount.addEventListener('dragleave',leave);mount.addEventListener('drop',drop);
    render();return {get busy(){return busy>0;},ids:()=>files.map(f=>f.id),
        async restore(ids,roles={}){const generation=++epoch;const restored=[];for(const id of (ids||[]).slice(0,max)){try{const response=await api.fetchApi('/prompt_mage/grimoire/attachment/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});const value=await response.json();if(!response.ok||value.kind!=='image')throw Error(value.error||'Image reference unavailable.');restored.push({...value,role:roles[id]||'Reference'});}catch(e){notify(e.message);}}if(!dead&&generation===epoch){files=restored;render();emit();}},
        destroy(){dead=true;epoch++;mount.removeEventListener('dragover',over);mount.removeEventListener('dragleave',leave);mount.removeEventListener('drop',drop);}
    };
}
