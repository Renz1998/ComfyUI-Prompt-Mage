// Keep connected sockets plus one empty image input; preserve every graph link by name.
const updating=new WeakSet();
export function ensureImageInputs(node){
    if(updating.has(node)||!node.inputs?.some(s=>s.name==='image'))return;
    updating.add(node);
    try{
        let last=0;
        for(const slot of node.inputs){
            const n=slot.name==='image'?1:/^image_[2-6]$/.test(slot.name)?Number(slot.name.slice(6)):0;
            if(n&&slot.link!=null)last=Math.max(last,n);
        }
        const count=Math.min(6,Math.max(1,last+1));
        for(let n=2;n<=count;n++)if(!node.inputs.some(s=>s.name==='image_'+n))node.addInput('image_'+n,'IMAGE',{shape:7,tooltip:'Additional reference image. Connect to reveal another image input (up to six).'});
        for(let i=node.inputs.length-1;i>=0;i--){const s=node.inputs[i];if(/^image_[2-6]$/.test(s.name)&&Number(s.name.slice(6))>count&&s.link==null)node.removeInput?.(i);}
        const images=node.inputs.filter(s=>s.name==='image'||/^image_[2-6]$/.test(s.name)).sort((a,b)=>(a.name==='image'?1:Number(a.name.slice(6)))-(b.name==='image'?1:Number(b.name.slice(6))));
        const first=node.inputs.findIndex(s=>s.name==='image');
        const rest=node.inputs.filter(s=>!images.includes(s));rest.splice(first,0,...images);node.inputs.splice(0,node.inputs.length,...rest);
        for(const [index,slot]of node.inputs.entries())if(slot.link!=null){const link=node.graph?.links?.get?.(slot.link)||node.graph?.links?.[slot.link];if(link)link.target_slot=index;}
        node.setDirtyCanvas?.(true,true);
    }finally{updating.delete(node);}
}
