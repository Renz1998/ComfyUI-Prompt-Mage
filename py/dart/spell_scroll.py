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
    with LOCK:
        path=scroll_path(scroll_id)
        if not path.exists():return None
        if path.stat().st_size>2*1024*1024:raise ValueError('Spell Scroll file is too large.')
        value=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value.get('text'),str):raise ValueError('Invalid Spell Scroll.')
        # Bind old snapshots before compaction moves their source position. Never guess another reply.
        if not value.get('response_id') and isinstance(value.get('response_index'),int):
            try:
                from .grimoire_prompt import prepare_turn
                state=read_memory(memory_path(value['conversation_id']))
                index=value['response_index']
                if 0<=index<len(state['turns']):
                    turn=prepare_turn(state['turns'][index])
                    if turn['role']=='assistant' and value['text'] in (turn['content'],turn.get('prompt_text')):
                        value['response_id']=turn['id'];save_memory(path,value)
            except (ValueError,KeyError,TypeError,OSError):
                pass
        return value


def approve(scroll_id,conversation_id,index,text,mode,field):
    with LOCK:
        state=read_memory(memory_path(conversation_id))
        if not isinstance(index,int) or not 0<=index<len(state['turns']):raise ValueError('Response changed; refresh the conversation.')
        turn=state['turns'][index]
        if turn['role']!='assistant' or turn['content']!=text:raise ValueError('Response changed; refresh before selecting it.')
        from .grimoire_prompt import prepare_turn
        turn = prepare_turn(dict(turn, mode=turn.get('mode',mode)), state.get('settings'))
        if turn.get('valid') is False:
            raise ValueError('Response failed prompt validation. Edit or retry it before applying.')
        mode = turn.get('mode', mode)
        field = turn.get('field', field)
        if mode == 'MOSS JSON layout':
            text = turn['prompt_text']
        select_output(text,'JSON only' if mode=='MOSS JSON layout' else mode,field)
        title=next((t['content'][:80] for t in state['turns'] if t['role']=='user'),'Conversation')
        value=dict(text=text,mode=mode,field=field,conversation_id=conversation_id,response_index=index,response_id=turn['id'],
                   title=title,updated=time.time())
        save_memory(scroll_path(scroll_id),value)
        return value


def prompt_from_scroll(value,width,height):
    if not value:raise ValueError('No applied prompt. In Grimoire, choose Use this prompt on a response first.')
    if value['mode']=='MOSS JSON layout':
        return json.dumps(read_layout(select_output(value['text'],'JSON only',''),width,height),ensure_ascii=False,separators=(',',':'))
    return select_output(value['text'],value['mode'],value['field'])
