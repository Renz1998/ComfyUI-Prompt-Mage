export const BRIEF_TYPE='MAGE_PRODUCTION_BRIEF';
const GRIMOIRE='DanbooruTagsTransformerGrimoire';
export function briefSource(node){
    const input=node.inputs?.find(i=>i.name==='production_brief');if(input?.link==null)return null;
    const graph=node.graph,link=graph?.links?.get?.(input.link)||graph?.links?.[input.link];
    const source=graph?.getNodeById?.(link?.origin_id)||graph?._nodes?.find(n=>String(n.id)===String(link?.origin_id));
    return (source?.comfyClass||source?.type)===GRIMOIRE?source:null;
}
export function briefTargets(node){
    const graph=node.graph;return (graph?._nodes||[]).filter(n=>(n.comfyClass||n.type)==='DanbooruTagsTransformerFoundry'&&briefSource(n)===node);
}
export function ensureBriefOutput(node){if(!node.outputs?.some(o=>o.name==='production_brief'))node.addOutput?.('production_brief',BRIEF_TYPE);}
export function ensureBriefInput(node){if(!node.inputs?.some(o=>o.name==='production_brief'))node.addInput?.('production_brief',BRIEF_TYPE,{shape:7});}
export function announceBrief(brief){if(typeof window.dispatchEvent==='function'&&typeof CustomEvent==='function')window.dispatchEvent(new CustomEvent('prompt-mage-production-brief',{detail:brief}));}
export function installFoundryBrief({node,mount,api,canApply,canAutoApply,onApply,notify,changed=()=>{}}){
    const make=(tag,text)=>{const e=document.createElement(tag);e.textContent=text||'';return e;};
    const title=make('strong','Grimoire production brief'),hint=make('small','Connect Grimoire.production_brief to import an agreed brief.'),check=make('button','Check sent brief'),body=make('div'),apply=make('button','Use this brief for a new plan');
    body.style.maxHeight='220px';body.style.overflow='auto';check.type=apply.type='button';mount.append(title,hint,check,body,apply);let pending=null,loading=false,version=0,removed=false;
    function refresh(){const source=briefSource(node),chapter=source?.widgets?.find(w=>w.name==='conversation_id')?.value;if(pending&&pending.conversation_id!==chapter){pending=null;body.replaceChildren();}check.disabled=loading||!source;apply.hidden=!pending;apply.disabled=loading||!canApply();if(source&&!pending)hint.textContent='Connected to Grimoire · send the agreed brief from chat, or check its last snapshot.';if(!source)hint.textContent='Connect Grimoire.production_brief. Then choose Send brief to Foundry in the chat.';}
    async function use(){if(!pending||!canApply())return;loading=true;refresh();try{await onApply(pending);node.properties.mage_production_brief_applied=pending.id;hint.textContent='Imported snapshot · later chat does not change it. Review the fields, then Preview plan.';}catch(e){notify(e.message);}finally{loading=false;refresh();changed();}}
    async function load(auto=false){const source=briefSource(node),chapter=source?.widgets?.find(w=>w.name==='conversation_id')?.value,request=++version;if(!chapter){refresh();return;}loading=true;refresh();try{
        const response=await api.fetchApi('/prompt_mage/grimoire/production_brief',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({conversation_id:chapter})});const data=await response.json();if(!response.ok)throw Error(data.error||'Could not read the production brief.');
        if(removed||request!==version||briefSource(node)!==source||source.widgets?.find(w=>w.name==='conversation_id')?.value!==chapter)return;if(data.brief&&data.brief.conversation_id!==chapter)throw Error('Production brief belongs to another chat. Refresh it.');pending=data.brief;body.replaceChildren();if(!pending){hint.textContent='Nothing sent yet. In Grimoire choose Send brief to Foundry after agreeing on the project.';return;}
        const b=pending.settings;hint.textContent='From '+pending.title+' · saved snapshot';
        for(const text of [b.brief,`${b.shot_count??'Keep current'} frames · ${b.style_preset||'Keep current style'} · ${b.aspect_ratio||(b.width?b.width+' × '+b.height:'Keep current canvas')}`,`${b.references.length} image references · model, API keys and spending caps stay in Foundry`])body.append(make('p',text));
        if(auto&&canAutoApply()){loading=false;await use();}
    }catch(e){notify(e.message);}finally{loading=false;refresh();changed();}}
    const sent=event=>{const chapter=briefSource(node)?.widgets?.find(w=>w.name==='conversation_id')?.value;if(event.detail?.conversation_id===chapter)void load(true);};
    window.addEventListener('prompt-mage-production-brief',sent);check.onclick=()=>void load();apply.onclick=()=>void use();refresh();
    return {refresh,load,get busy(){return loading;},destroy(){removed=true;version++;window.removeEventListener('prompt-mage-production-brief',sent);}};
}
