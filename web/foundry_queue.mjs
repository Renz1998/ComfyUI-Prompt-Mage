export const FOUNDRY='DanbooruTagsTransformerFoundry';
export const REVIEW=FOUNDRY+'ReviewOutput';
const link=(value,id,slot)=>Array.isArray(value)&&String(value[0])===String(id)&&value[1]===slot;

export function foundryPrompt(snapshot,nodeId,operation,{runId,attemptId='',remote=false}={}) {
    const id=String(nodeId),graph=JSON.parse(JSON.stringify(snapshot.output));
    if(graph[id]?.class_type!==FOUNDRY)throw Error('Foundry is disabled or missing.');
    delete graph[id].inputs.production_brief;
    graph[id].inputs.run_id=runId;graph[id].inputs.attempt_id=attemptId;
    if(remote)delete graph[id].inputs.clip;
    if(operation==='review_saved')for(const key of Object.keys(graph[id].inputs))if(key==='image'||key.startsWith('image_')||key==='attachments')delete graph[id].inputs[key];
    function ancestors(key,seen=new Set(),stack=new Set()) {
        key=String(key);if(stack.has(key))throw Error('Foundry input cycle.');if(seen.has(key))return seen;
        if(!graph[key])throw Error('Missing workflow input '+key);stack.add(key);seen.add(key);
        for(const value of Object.values(graph[key].inputs||{}))if(Array.isArray(value)&&value.length===2&&Number.isInteger(value[1]))ancestors(value[0],seen,stack);
        stack.delete(key);return seen;
    }
    let targets=[id];
    if(operation==='plan'||operation==='review_saved') {
        if([...ancestors(id)].some(key=>/KSampler|SamplerCustom|SaveImage|SaveVideo/.test(graph[key].class_type)))throw Error('Planning inputs must not depend on image generation.');
        graph[id].class_type=FOUNDRY+(operation==='plan'?'Plan':'ReviewSaved');
    } else if(operation==='render') {
        for(const key of Object.keys(graph[id].inputs))if(key==='image'||key.startsWith('image_')||key==='attachments')delete graph[id].inputs[key];
        const sinks=Object.entries(graph).filter(([,n])=>n.class_type===REVIEW&&link(n.inputs.run_id,id,4)&&link(n.inputs.attempt_id,id,5));
        if(sinks.length!==1)throw Error('Connect exactly one Foundry Review Output to this node’s run_id and attempt_id.');
        const [sinkId,sink]=sinks[0];if(remote)delete sink.inputs.clip;
        if(!Array.isArray(sink.inputs.image))throw Error('Connect the final decoded image to Review Output.');
        const chain=ancestors(sink.inputs.image[0]);
        if(!chain.has(id)||![...chain].some(key=>Object.values(graph[key].inputs||{}).some(v=>link(v,id,0))))throw Error('The reviewed image must use this Foundry prompt.');
        if(![...chain].some(key=>Object.entries(graph[key].inputs||{}).some(([name,v])=>/seed/.test(name)&&link(v,id,3))))throw Error('Connect Foundry’s seed output to the sampler or RandomNoise seed input.');
        if([...chain].some(key=>typeof graph[key].inputs?.batch_size==='number'&&graph[key].inputs.batch_size!==1))throw Error('Set latent batch_size to 1 for Foundry review.');
        targets=[sinkId];
        // Only explicitly paired image savers join this job; unrelated outputs stay idle.
        for(const [key,n]of Object.entries(graph))if(n.class_type==='SaveImage'&&link(n.inputs.filename_prefix,id,6)&&JSON.stringify(n.inputs.images)===JSON.stringify(sink.inputs.image))targets.push(key);
    } else throw Error('Unknown Foundry queue action.');
    return {output:graph,workflow:snapshot.workflow,targets};
}

export async function queueFoundry(api,job) {
    const capability=await api.fetchApi('/prompt_mage/grimoire/capabilities');
    if(!capability.ok||!(await capability.json()).partial_execution)throw Error('Update and restart ComfyUI for Foundry’s bounded execution.');
    const response=await api.fetchApi('/prompt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        client_id:api.clientId||'',prompt:job.output,partial_execution_targets:job.targets,extra_data:{extra_pnginfo:{workflow:job.workflow}}
    })});
    const result=await response.json();if(!response.ok)throw Error(result.error?.message||'ComfyUI rejected the Foundry job.');return result;
}
