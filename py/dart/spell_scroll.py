import json
import time
from .grimoire import memory_path, read_memory, save_memory, select_output, LOCK
from .moss import read_layout


def scroll_path(scroll_id):
    checked=memory_path(scroll_id)
    root=checked.parent.parent/'spell_scroll'
    root.mkdir(parents=True,exist_ok=True)
    return root/checked.name


def active_scroll(scroll_id):
    path=scroll_path(scroll_id)
    if not path.exists():return None
    if path.stat().st_size>2*1024*1024:raise ValueError('Spell Scroll file is too large.')
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value.get('text'),str):raise ValueError('Invalid Spell Scroll.')
    return value


def approve(scroll_id,conversation_id,index,text,mode,field):
    with LOCK:
        state=read_memory(memory_path(conversation_id))
        if not isinstance(index,int) or not 0<=index<len(state['turns']):raise ValueError('Response changed; refresh the conversation.')
        turn=state['turns'][index]
        if turn['role']!='assistant' or turn['content']!=text:raise ValueError('Response changed; refresh before selecting it.')
        if turn.get('valid') is False:
            raise ValueError('Response failed prompt validation. Edit or retry it before applying.')
        mode = turn.get('mode', mode)
        field = turn.get('field', field)
        if mode == 'MOSS JSON layout':
            read_layout(select_output(text,'JSON only',''),turn.get('width',1024),turn.get('height',1024))
        select_output(text,'JSON only' if mode=='MOSS JSON layout' else mode,field)
        title=next((t['content'][:80] for t in state['turns'] if t['role']=='user'),'Conversation')
        value=dict(text=text,mode=mode,field=field,conversation_id=conversation_id,response_index=index,
                   title=title,updated=time.time())
        save_memory(scroll_path(scroll_id),value)
        return value


def prompt_from_scroll(value,width,height):
    if not value:raise ValueError('No applied prompt. In Grimoire, choose Use this prompt on a response first.')
    if value['mode']=='MOSS JSON layout':
        return json.dumps(read_layout(select_output(value['text'],'JSON only',''),width,height),ensure_ascii=False,indent=2)
    return select_output(value['text'],value['mode'],value['field'])
