// Canvas sockets must not depend on native widget visibility or saved-node age.
export function ensureCanvasInputs(node) {
    for(const name of ['width','height']) {
        let slot=node.inputs?.find(input=>input.name===name);
        if(!slot&&node.addInput){node.addInput(name,'INT',{shape:7,tooltip:'Connect Resolution '+name+' for matching canvas dimensions.'});slot=node.inputs?.find(input=>input.name===name);}
        if(slot){slot.hidden=false;slot.type='INT';delete slot.widget;}
    }
}
