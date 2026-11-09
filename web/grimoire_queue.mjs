// Keep the full graph in the server cache, executing only the explicit chat target.
export function chatPrompt(snapshot, nodeId, action, message) {
    const id=String(nodeId), output=snapshot.output;
    if(output?.[id]?.class_type!=='DanbooruTagsTransformerGrimoire')throw Error('Grimoire is disabled or missing.');
    const selected={}, visiting=new Set();
    const graph=JSON.parse(JSON.stringify(output));
    if(graph[id].inputs.assistant_backend && graph[id].inputs.assistant_backend!=='Local Qwen')delete graph[id].inputs.clip;
    function visit(key){
        key=String(key);if(selected[key])return;if(visiting.has(key))throw Error('Conversation input cycle.');
        const item=graph[key];if(!item)throw Error('Missing conversation input.');
        if(/KSampler|SamplerCustom|SaveImage|SaveVideo/.test(item.class_type))throw Error('Chat input depends on image generation. Use a loaded reference image or disconnect it before chatting.');
        visiting.add(key);
        for(const value of Object.values(item.inputs||{}))if(Array.isArray(value)&&value.length===2&&Number.isInteger(value[1]))visit(value[0]);
        visiting.delete(key);selected[key]=JSON.parse(JSON.stringify(item));
    }
    visit(id);graph[id].class_type='DanbooruTagsTransformerGrimoireTurn';graph[id].inputs.action=action;graph[id].inputs.message=message;
    return {...snapshot,output:graph};
}

export async function queueChat(api, job, nodeId) {
    const capability=await api.fetchApi('/prompt_mage/grimoire/capabilities');
    if(!capability.ok || !(await capability.json()).partial_execution)throw Error('Update/restart ComfyUI and Prompt Mage for safe chat-only execution.');
    // Explicit wire format also works with frontends whose queuePrompt ignores its options argument.
    const response=await api.fetchApi('/prompt',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        client_id:api.clientId||'',prompt:job.output,partial_execution_targets:[String(nodeId)],
        extra_data:{extra_pnginfo:{workflow:job.workflow}}
    })});
    const result=await response.json();
    if(!response.ok)throw Error(result.error?.message||'ComfyUI rejected the chat request.');
    return result;
}
