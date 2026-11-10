function stable(value){
    if(Array.isArray(value))return value.map(stable);
    if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(key=>[key,stable(value[key])]));
    return value;
}
function normalized(text){try{return JSON.stringify(stable(JSON.parse(text)));}catch{return text;}}

export function isAppliedResponse(active,chapter,index,turn){
    if(!active||active.conversation_id!==chapter||typeof active.text!=='string')return false;
    const sameSource=active.response_id&&turn.id?active.response_id===turn.id:active.response_index===index;
    if(!sameSource)return false;
    // Index alone is insufficient: regeneration/editing can replace the selected reply.
    return active.text===turn.content||Boolean(turn.prompt_text&&normalized(active.text)===normalized(turn.prompt_text));
}
