"""Persistent production runs; independent of chat and Spell Scroll."""
import copy
import json
import re
import secrets
import threading
import time
import uuid
from pathlib import Path

LOCK = threading.RLock()
ASSISTANTS=('Local Qwen','DeepSeek V4.1 Flash · Recommended · Text + images','From chat / Local Qwen')
BUILTINS = {
    'single': dict(name='Single scene test', brief='An adult traveler in a green wool cloak studies a map in a lantern-lit wooden inn.', shared_rules='Keep the chosen character, medium and canvas consistent.', review_rules='Check the requested action, major props and camera logic.', shot_count=1),
    'carousel': dict(name='Holiday carousel', brief='Plan a holiday photo carousel with varied framing and a clear opening, quieter middle and closing frame.', shared_rules='Keep the chosen palette and light treatment. Allow planned outfit and location changes.', review_rules='Check each shot against its own brief. Allow deliberate close-ups and planned variations.', shot_count=7),
    'lookbook': dict(name='Character lookbook', brief='Create an outfit lookbook with distinct looks and readable clothing details.', shared_rules='Keep the selected character traits; vary clothes and pose intentionally.', review_rules='Check requested clothes and visible character details; allow planned outfit changes.', shot_count=6),
    'storyboard': dict(name='Storyboard', brief='Develop a short visual story with clear actions and a readable sequence.', shared_rules='Track explicitly required character, object and location continuity.', review_rules='Check the action and required continuity for this frame only.', shot_count=6),
    'product': dict(name='Product campaign', brief='Plan a small product campaign with complementary compositions.', shared_rules='Keep product identity, colors and required visible wording accurate.', review_rules='Check the product, required text and requested placement.', shot_count=4),
}


def root():
    import folder_paths
    path=Path(folder_paths.get_user_directory())/'prompt_mage'/'foundry'
    path.mkdir(parents=True,exist_ok=True)
    return path


def checked_id(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-f0-9]{32}',value):
        raise ValueError('Choose a Foundry run, or create a new plan.')
    return value


def run_path(run_id):
    return root()/'runs'/(checked_id(run_id)+'.json')


def write(value):
    path=run_path(value['id']);path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(value,ensure_ascii=False,indent=2)
    if len(raw.encode())>2*1024*1024:raise ValueError('Run record exceeds 2 MB. Start a separate test.')
    value['updated']=time.time();raw=json.dumps(value,ensure_ascii=False,indent=2)
    temp=path.with_suffix('.tmp');temp.write_text(raw,encoding='utf-8');temp.replace(path)


def read(run_id):
    path=run_path(run_id)
    if not path.exists():raise ValueError('Run not found on this server. Create a plan first.')
    if path.stat().st_size>2*1024*1024:raise ValueError('Run record is too large.')
    value=json.loads(path.read_text(encoding='utf-8'))
    if value.get('version')!=1 or value.get('id')!=run_id:raise ValueError('Invalid run record.')
    return value


def text(value,label,limit=8000):
    if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError(label+' must be nonempty text under '+str(limit)+' characters.')
    return value.strip()


def validate_plan(value,expected_count):
    if not isinstance(value,dict):raise ValueError('Planner must return a JSON shot list.')
    title=text(value.get('title'),'Plan title',120)
    shots=value.get('shots')
    if not isinstance(shots,list) or len(shots)!=expected_count:raise ValueError('Plan must contain exactly '+str(expected_count)+' shots.')
    result=[]
    for index,shot in enumerate(shots):
        if not isinstance(shot,dict):raise ValueError('Each shot must be an object.')
        criteria=shot.get('criteria')
        if not isinstance(criteria,list) or not 1<=len(criteria)<=8:raise ValueError('Each shot needs 1–8 observable review criteria.')
        result.append(dict(id='shot-'+str(index+1),title=text(shot.get('title'),'Shot title',120),
            brief=text(shot.get('brief'),'Shot brief',6000),criteria=[text(c,'Review criterion',400) for c in criteria]))
    plan=dict(title=title,shots=result)
    notes=value.get('reference_notes')
    if isinstance(notes,(dict,list)):notes=json.dumps(notes,ensure_ascii=False)
    if isinstance(notes,str) and notes.strip():plan['reference_notes']=notes.strip()[:12000]
    return plan


def templates():
    result=[dict(id=key,**copy.deepcopy(value),builtin=True) for key,value in BUILTINS.items()]
    path=root()/'templates';path.mkdir(exist_ok=True)
    for file in sorted(path.glob('*.json'))[:100]:
        try:
            if file.stat().st_size>128000:continue
            value=json.loads(file.read_text(encoding='utf-8'));checked_id(value['id']);result.append(value)
        except (ValueError,KeyError,OSError):continue
    return result


def template(template_id):
    for value in templates():
        if value['id']==template_id:return value
    raise ValueError('Template not found. Refresh templates.')


def source_settings(conversation_id):
    if not conversation_id:return dict(assistant_backend='Local Qwen',local_model='Automatic',thinking=False,max_tokens=4096,style_preset='Photo · Bright lifestyle'),''
    from .grimoire import memory_path, read_memory, LOCK as CHAT_LOCK
    with CHAT_LOCK:state=read_memory(memory_path(conversation_id))
    settings=state.get('settings',{})
    allowed=('assistant_backend','local_model','openai_model','deepseek_model','thinking','max_tokens','style_preset','style_notes')
    config={key:settings[key] for key in allowed if key in settings}
    config.setdefault('assistant_backend','Local Qwen');config.setdefault('max_tokens',4096)
    context=json.dumps(dict(summary=state['summary'],task=settings.get('task_instructions',''),pinned=settings.get('pinned_facts',''),
        recent=[dict(role=t['role'],content=t['content']) for t in state['turns'][-8:]]),ensure_ascii=False)
    if len(context)>48000:context=context[-48000:]
    return config,context


def create(run_id,conversation_id,template_id,brief,shared_rules,review_rules,shot_count,width,height,max_attempts,max_renders,max_calls,appearance=None,assistant_profile=ASSISTANTS[0],style_preset='Photo · Bright lifestyle',style_notes='',review_tolerance='Balanced',run_mode='Automatic'):
    from .moss import canvas_size
    checked_id(run_id);canvas_size(width,height)
    if any(isinstance(n,bool) or not isinstance(n,int) for n in (shot_count,max_attempts,max_renders,max_calls)):
        raise ValueError('Run limits must be whole numbers.')
    if not 1<=shot_count<=24 or not 1<=max_attempts<=10 or not 1<=max_renders<=100 or not 1<=max_calls<=100:raise ValueError('Run limits are out of range.')
    if max_renders<shot_count or max_calls<1+2*shot_count:raise ValueError('Budgets must allow at least one render and two assistant calls per frame, plus planning. Use the suggested budgets.')
    if review_tolerance not in ('Relaxed','Balanced','Strict') or run_mode not in ('Automatic','Manual'):raise ValueError('Choose a valid review tolerance and run mode.')
    if run_path(run_id).exists():raise ValueError('Run already exists. New plans use a new run ID.')
    selected=template(template_id);config,context=source_settings(conversation_id)
    if assistant_profile not in ASSISTANTS:raise ValueError('Choose a supported Foundry assistant preset.')
    if assistant_profile=='Local Qwen':config.update(assistant_backend='Local Qwen',local_model='Automatic')
    if assistant_profile==ASSISTANTS[1]:
        from .deepseek_assistant import DEFAULT_MODEL
        config.update(assistant_backend='DeepSeek API',deepseek_model=DEFAULT_MODEL)
    from .style_presets import resolve_style
    resolved,_=resolve_style(style_preset,style_notes,secrets.randbelow(2**32))
    config.update(style_preset=resolved,style_notes=style_notes)
    if config['assistant_backend']=='DeepSeek API':
        from .deepseek_assistant import MODELS, DEFAULT_MODEL
        if MODELS.get(config.get('deepseek_model',DEFAULT_MODEL))!='deepseek-flash':
            raise ValueError('Foundry needs image review. Choose DeepSeek V4.1 Flash; V4 Pro is text-only.')
    value=dict(version=1,id=run_id,created=time.time(),status='planning',source_conversation=conversation_id,config=config,context=context,
        template=template_id,assistant_profile=assistant_profile,brief=text(brief or selected['brief'],'Brief'),shared_rules=shared_rules[:8000],review_rules=review_rules[:8000],
        shot_count=shot_count,width=width,height=height,appearance=copy.deepcopy(appearance),
        limits=dict(attempts=max_attempts,renders=max_renders,calls=max_calls),usage=dict(renders=0,calls=0),
        run_mode=run_mode,review_tolerance=review_tolerance,automation_enabled=False,
        plan=None,current=0,attempts=[],compiled={},accepted=[],last_error='')
    receipt=root()/'jobs'/(run_id+'.json')
    if receipt.exists():
        value['job_id']=json.loads(receipt.read_text(encoding='utf-8'))['job_id'];receipt.unlink()
    write(value);return value


def charge(run_id):
    with LOCK:
        value=read(run_id)
        if value['status'] in ('stopped','paused'):raise ValueError('This run is paused or stopped.')
        if value['usage']['calls']>=value['limits']['calls']:raise ValueError('Assistant-call budget reached. Start a new bounded test.')
        value['usage']['calls']+=1;write(value)


def fail(run_id,message,attempt_id=None):
    with LOCK:
        value=read(run_id)
        if value['status'] not in ('stopped','paused'):value['status']='needs_attention'
        value['last_error']=str(message)[:1200]
        for attempt in value['attempts']:
            if attempt['id']==attempt_id:attempt.update(status='error',error=value['last_error'])
        write(value)


def reserve(run_id):
    with LOCK:
        value=read(run_id)
        if value['status'] not in ('ready','awaiting_approval','needs_attention'):raise ValueError('Approve a plan or finish the current attempt first.')
        if not value.get('approved'):raise ValueError('Approve the shot list first.')
        shot=value['plan']['shots'][value['current']]
        if sum(a['shot_id']==shot['id'] for a in value['attempts'])>=value['limits']['attempts']:raise ValueError('Attempt limit reached for this frame.')
        if value['usage']['renders']>=value['limits']['renders']:raise ValueError('Render-attempt budget reached.')
        needed=1+(shot['id'] not in value['compiled'])
        if value['usage']['calls']+needed>value['limits']['calls']:raise ValueError('Not enough assistant calls remain for composition and review.')
        attempt=dict(id=uuid.uuid4().hex,shot_id=shot['id'],seed=secrets.randbelow(2**53),status='reserved',review=None,image=False)
        value['attempts'].append(attempt);value['usage']['renders']+=1;value.update(status='rendering',last_error='');write(value)
        return attempt


def attempt_for(value,attempt_id):
    checked_id(attempt_id)
    attempt=next((a for a in value['attempts'] if a['id']==attempt_id),None)
    if not attempt:raise ValueError('Attempt not found.')
    return attempt


def action(run_id,operation,data=None):
    data=data or {}
    with LOCK:
        value=read(run_id)
        if operation=='approve':
            if value['status']!='plan_ready':raise ValueError('Preview a plan before approving it.')
            value['plan']=validate_plan(data.get('plan',value['plan']),value['shot_count']);value.update(approved=True,status='ready')
        elif operation=='accept':
            if value['status'] not in ('awaiting_approval','needs_attention'):raise ValueError('Review a generated image before accepting it.')
            attempt=attempt_for(value,data.get('attempt_id',''))
            if attempt['shot_id']!=value['plan']['shots'][value['current']]['id'] or not attempt.get('review'):raise ValueError('Choose a reviewed attempt for the current frame.')
            value['accepted'].append(dict(shot_id=attempt['shot_id'],attempt_id=attempt['id'],automatic=bool(data.get('automatic',False))));attempt['status']='accepted';value['current']+=1
            value['last_error']=''
            value.pop('last_decision',None)
            value['status']='complete' if value['current']==len(value['plan']['shots']) else 'ready'
        elif operation=='pause':
            if value['status'] in ('complete','stopped','paused'):raise ValueError('This run has ended or is already paused.')
            value['paused_from']=value['status'];value['status']='paused'
        elif operation=='resume':
            if value['status']!='paused':raise ValueError('This run is not paused.')
            previous=value.pop('paused_from','ready');value['status']='needs_attention' if previous in ('rendering','reviewing','planning') else previous
            if value['attempts'] and value['attempts'][-1].get('review'):
                latest=value['attempts'][-1]
                if value.get('plan') and value['current']<len(value['plan']['shots']) and latest['shot_id']==value['plan']['shots'][value['current']]['id']:
                    value['status']='awaiting_approval'
        elif operation=='stop':value['status']='stopped'
        elif operation=='mark_interrupted':
            if value['status'] not in ('rendering','reviewing','planning'):raise ValueError('No unfinished job to recover.')
            value.update(status='needs_attention',last_error='Previous job was interrupted. Saved attempts are retained.')
        elif operation=='save_template':
            if not value.get('approved'):raise ValueError('Approve a plan before saving its template.')
            identifier=uuid.uuid4().hex;path=root()/'templates';path.mkdir(exist_ok=True)
            saved=dict(id=identifier,name=text(data.get('name'),'Template name',80),brief=value['brief'],shared_rules=value['shared_rules'],review_rules=value['review_rules'],shot_count=value['shot_count'],plan=value['plan'],builtin=False)
            (path/(identifier+'.json')).write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
        else:raise ValueError('Unknown Foundry action.')
        write(value);return value


def public(value):
    result={key:copy.deepcopy(v) for key,v in value.items() if key not in ('context','appearance','compiled','reference_context')}
    result['assistant']=value['config'].get('assistant_backend','Local Qwen')
    return result
