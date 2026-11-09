// Queue only the conversation and upstream inputs. Never queue image samplers for Send.
export function chatPrompt(snapshot, nodeId, action, message) {
    const id=String(nodeId), output=snapshot.output;
    if(output?.[id]?.class_type!=='DanbooruTagsTransformerGrimoire')throw Error('Grimoire is disabled or missing.');
    const selected={}, visiting=new Set();
    function visit(key){
        key=String(key);if(selected[key])return;if(visiting.has(key))throw Error('Conversation input cycle.');
        const item=output[key];if(!item)throw Error('Missing conversation input.');
        if(/KSampler|SamplerCustom|SaveImage|SaveVideo/.test(item.class_type))throw Error('Chat input depends on image generation. Use a loaded reference image or disconnect it before chatting.');
        visiting.add(key);
        for(const value of Object.values(item.inputs||{}))if(Array.isArray(value)&&value.length===2&&Number.isInteger(value[1]))visit(value[0]);
        visiting.delete(key);selected[key]=JSON.parse(JSON.stringify(item));
    }
    visit(id);selected[id].class_type='DanbooruTagsTransformerGrimoireTurn';selected[id].inputs.action=action;selected[id].inputs.message=message;
    return {...snapshot,output:selected};
}
