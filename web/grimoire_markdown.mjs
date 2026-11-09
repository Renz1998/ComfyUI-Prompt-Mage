// Small safe Markdown renderer: no raw HTML, remote images or executable URLs.
export function renderMarkdown(root, text, copy=()=>{}) {
    const make=(tag,value)=>{const e=document.createElement(tag);if(value!==undefined)e.textContent=value;return e;};
    function inline(parent,value){
        const pattern=/(\*\*[^*]+\*\*|__[^_]+__|~~[^~]+~~|`[^`]+`|\*[^*]+\*|(?<!\w)_[^_]+_(?!\w)|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g;
        let start=0;
        for(const match of value.matchAll(pattern)){
            parent.append(make('span',value.slice(start,match.index)));
            const token=match[0];
            if(token.startsWith('**')||token.startsWith('__'))parent.append(make('strong',token.slice(2,-2)));
            else if(token.startsWith('~~'))parent.append(make('del',token.slice(2,-2)));
            else if(token.startsWith('*')||token.startsWith('_'))parent.append(make('em',token.slice(1,-1)));
            else if(token.startsWith('`'))parent.append(make('code',token.slice(1,-1)));
            else {const m=token.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);const a=make('a',m[1]);a.href=m[2];a.target='_blank';a.rel='noopener noreferrer';parent.append(a);}
            start=match.index+token.length;
        }
        parent.append(make('span',value.slice(start)));
    }
    // Models often return bare JSON. Display it as readable, copyable code without changing saved content.
    let source=String(text).replace(/\r\n/g,'\n');
    try{const value=JSON.parse(source);if(value&&typeof value==='object')source='```json\n'+JSON.stringify(value,null,2)+'\n```';}catch{}
    const lines=source.split('\n');
    let listRoot=null,listType='';
    for(let i=0;i<lines.length;i++){
        if(/^\s*```/.test(lines[i])){
            const language=lines[i].trim().slice(3),code=[];
            while(++i<lines.length&&!/^\s*```/.test(lines[i]))code.push(lines[i]);
            const box=make('section'),bar=make('div',language||'code'),button=make('button','Copy code');button.type='button';
            button.addEventListener('click',()=>copy(code.join('\n')));bar.append(button);
            const pre=make('pre');pre.style.cssText='overflow:auto;padding:10px;background:#0e101b;white-space:pre';pre.append(make('code',code.join('\n')));box.append(bar,pre);root.append(box);continue;
        }
        const heading=lines[i].match(/^(#{1,6})\s+(.+)$/);
        const list=lines[i].match(/^\s*([-*+]|\d+[.)])\s+(.+)$/);
        if(list){
            const type=/\d/.test(list[1])?'ol':'ul';
            if(!listRoot||listType!==type){listRoot=make(type);listType=type;root.append(listRoot);}
            const item=make('li');inline(item,list[2]);listRoot.append(item);continue;
        }
        listRoot=null;listType='';
        const quote=lines[i].match(/^>\s?(.*)$/);
        if(quote){const block=make('blockquote');inline(block,quote[1]);root.append(block);continue;}
        if(/^\s*(?:---+|\*\*\*+)\s*$/.test(lines[i])){root.append(make('hr'));continue;}
        if(lines[i].includes('|')&&i+1<lines.length&&/^\s*\|?\s*:?-+:?\s*\|/.test(lines[i+1])){
            const table=make('table'),cells=line=>line.trim().replace(/^\||\|$/g,'').split('|');
            const add=(line,tag)=>{const row=make('tr');for(const cell of cells(line)){const e=make(tag);inline(e,cell.trim());row.append(e);}table.append(row);};
            add(lines[i],'th');i++;while(i+1<lines.length&&lines[i+1].includes('|'))add(lines[++i],'td');root.append(table);continue;
        }
        const element=make(heading?'h'+heading[1].length:'p');element.style.cssText='margin:6px 0;overflow-wrap:anywhere';
        inline(element,heading?heading[2]:lines[i]);root.append(element);
    }
}
