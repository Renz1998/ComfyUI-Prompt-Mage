// Small safe Markdown renderer: no raw HTML, remote images or executable URLs.
export function renderMarkdown(root, text, copy=()=>{}) {
    const make=(tag,value)=>{const e=document.createElement(tag);if(value!==undefined)e.textContent=value;return e;};
    function inline(parent,value){
        const pattern=/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g;
        let start=0;
        for(const match of value.matchAll(pattern)){
            parent.append(make('span',value.slice(start,match.index)));
            const token=match[0];
            if(token.startsWith('**'))parent.append(make('strong',token.slice(2,-2)));
            else if(token.startsWith('*'))parent.append(make('em',token.slice(1,-1)));
            else if(token.startsWith('`'))parent.append(make('code',token.slice(1,-1)));
            else {const m=token.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);const a=make('a',m[1]);a.href=m[2];a.target='_blank';a.rel='noopener noreferrer';parent.append(a);}
            start=match.index+token.length;
        }
        parent.append(make('span',value.slice(start)));
    }
    const lines=String(text).split('\n');
    for(let i=0;i<lines.length;i++){
        if(/^\s*```/.test(lines[i])){
            const language=lines[i].trim().slice(3),code=[];
            while(++i<lines.length&&!/^\s*```/.test(lines[i]))code.push(lines[i]);
            const box=make('section'),bar=make('div',language||'code'),button=make('button','Copy code');button.type='button';
            button.addEventListener('click',()=>copy(code.join('\n')));bar.append(button);
            const pre=make('pre');pre.style.cssText='overflow:auto;padding:10px;background:#0e101b;white-space:pre';pre.append(make('code',code.join('\n')));box.append(bar,pre);root.append(box);continue;
        }
        const heading=lines[i].match(/^(#{1,3})\s+(.+)$/);
        const list=lines[i].match(/^\s*(?:[-*]|\d+\.)\s+(.+)$/);
        const element=make(heading?'h'+heading[1].length:list?'div':'p');element.style.cssText='margin:6px 0;overflow-wrap:anywhere';
        inline(element,heading?heading[2]:list?'• '+list[1]:lines[i]);root.append(element);
    }
}
