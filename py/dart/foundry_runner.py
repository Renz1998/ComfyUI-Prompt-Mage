"""Server-owned bounded controller. It queues between native jobs, never inside a node."""
import asyncio
import copy
import inspect
import json
import time
import uuid
from . import foundry as store
from .foundry_review import assessment

TASKS={}
FOUNDRY='DanbooruTagsTransformerFoundry'


def recipe_path(run_id):return store.root()/'jobs'/(store.checked_id(run_id)+'-workflow.json')


def link(value,node,slot):return isinstance(value,list) and len(value)==2 and str(value[0])==str(node) and value[1]==slot


def validate_recipe(job,node_id):
    if not isinstance(job,dict) or not isinstance(job.get('output'),dict):raise ValueError('A connected Foundry workflow is required.')
    graph=copy.deepcopy(job['output']);node_id=str(node_id)
    if graph.get(node_id,{}).get('class_type')!=FOUNDRY:raise ValueError('Foundry is missing from this workflow.')
    sinks=[key for key,n in graph.items() if n.get('class_type')==FOUNDRY+'ReviewOutput' and link(n.get('inputs',{}).get('run_id'),node_id,4) and link(n.get('inputs',{}).get('attempt_id'),node_id,5)]
    if len(sinks)!=1:raise ValueError('Connect exactly one Foundry Review Output to this node’s run_id and attempt_id.')
    def ancestors(key,seen=None,stack=None):
        key=str(key);seen=set() if seen is None else seen;stack=set() if stack is None else stack
        if key in stack:raise ValueError('Workflow input cycle.')
        if key in seen:return seen
        if key not in graph:raise ValueError('Missing workflow input.')
        seen.add(key);stack.add(key)
        for value in graph[key].get('inputs',{}).values():
            if isinstance(value,list) and len(value)==2 and isinstance(value[1],int):ancestors(value[0],seen,stack)
        stack.remove(key);return seen
    image=graph[sinks[0]].get('inputs',{}).get('image')
    if not isinstance(image,list) or len(image)!=2:raise ValueError('Connect the final decoded image to Review Output.')
    chain=ancestors(image[0])
    if not any(link(v,node_id,0) for k in chain for v in graph[k].get('inputs',{}).values()):raise ValueError('The image must use this Foundry prompt.')
    if not any('seed' in name and link(v,node_id,3) for k in chain for name,v in graph[k].get('inputs',{}).items()):raise ValueError('Connect Foundry’s seed output to the sampler seed.')
    if any(isinstance(graph[k].get('inputs',{}).get('batch_size'),(int,float)) and graph[k]['inputs']['batch_size']!=1 for k in chain):raise ValueError('Foundry needs latent batch_size = 1.')
    targets=sinks[:]
    for key,n in graph.items():
        if n.get('class_type')=='SaveImage' and link(n.get('inputs',{}).get('filename_prefix'),node_id,6) and n['inputs'].get('images')==image:targets.append(key)
    # References are used when planning, not decoded again on every retry.
    for key in list(graph[node_id]['inputs']):
        if key=='image' or key.startswith('image_') or key=='attachments':del graph[node_id]['inputs'][key]
    return dict(output=graph,workflow=job.get('workflow',{}),targets=targets,node_id=node_id)


def save_recipe(run_id,job,node_id,client_id=''):
    value=validate_recipe(job,node_id);value['client_id']=str(client_id)[:128]
    raw=json.dumps(value,ensure_ascii=False)
    if len(raw.encode())>4*1024*1024:raise ValueError('Foundry workflow snapshot exceeds 4 MB.')
    path=recipe_path(run_id);path.parent.mkdir(exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(raw,encoding='utf-8');temp.replace(path)


def load_recipe(run_id):
    path=recipe_path(run_id)
    if not path.exists():raise ValueError('Save the connected workflow with Approve & start or Render next frame first.')
    return json.loads(path.read_text(encoding='utf-8'))


def job_active(server,job_id):
    if not job_id:return False
    running,pending=server.prompt_queue.get_current_queue()
    return any(str(item[1])==job_id for item in running+pending)


async def submit(server,run_id,attempt,recipe,operation='render'):
    import execution
    if 'partial_execution_list' not in inspect.signature(execution.validate_prompt).parameters:raise ValueError('Update ComfyUI for Foundry automatic partial execution.')
    with store.LOCK:value=store.read(run_id)
    graph=copy.deepcopy(recipe['output']);node_id=recipe['node_id'];inputs=graph[node_id]['inputs']
    inputs.update(run_id=run_id,attempt_id=attempt['id'],width=value['width'],height=value['height'])
    targets=recipe['targets'] if operation=='render' else [node_id]
    if operation=='review_saved':graph[node_id]['class_type']=FOUNDRY+'ReviewSaved'
    if value['config']['assistant_backend']!='Local Qwen':
        inputs.pop('clip',None)
        for target in recipe['targets']:
            if graph[target]['class_type']==FOUNDRY+'ReviewOutput':graph[target]['inputs'].pop('clip',None)
    payload=dict(prompt=graph,partial_execution_targets=targets,client_id=recipe['client_id'],extra_data={'extra_pnginfo':{'workflow':recipe['workflow']}})
    if hasattr(server,'trigger_on_prompt'):payload=server.trigger_on_prompt(payload)
    prompt=payload['prompt']
    if hasattr(server,'node_replace_manager'):server.node_replace_manager.apply_replacements(prompt)
    job_id=str(uuid.uuid4());valid=await execution.validate_prompt(job_id,prompt,targets)
    if not valid[0]:
        details=[]
        for key,item in (valid[3] or {}).items():
            for error in item.get('errors',[]):details.append(f"{item.get('class_type',key)} ({key}): {error.get('message','Invalid input')} — {error.get('details','')}")
        fallback=valid[1].get('message',valid[1]) if isinstance(valid[1],dict) else valid[1]
        raise ValueError('ComfyUI rejected the workflow: '+('; '.join(details) or str(fallback))[:1000])
    with store.LOCK:
        current=store.read(run_id)
        if current['status'] in ('paused','stopped'):return None
        if current['status']!=('rendering' if operation=='render' else 'reviewing') or current['attempts'][-1]['id']!=attempt['id']:raise ValueError('Foundry attempt changed before queue submission.')
        extra=payload.get('extra_data',{});extra['client_id']=recipe['client_id'];extra['create_time']=int(time.time()*1000)
        sensitive={k:extra.pop(k) for k in getattr(execution,'SENSITIVE_EXTRA_DATA_KEYS',[]) if k in extra}
        number=server.number;server.number+=1;current['job_id']=job_id;store.write(current)
        server.prompt_queue.put((number,job_id,prompt,extra,valid[2],sensitive))
    return job_id


def notify(server,value):
    if hasattr(server,'send_sync'):server.send_sync('prompt_mage_foundry',{'foundry':[store.public(value)]})


async def run(server,run_id,poll=0.5):
    try:
        recipe=load_recipe(run_id)
        while True:
            with store.LOCK:value=store.read(run_id)
            if not value.get('automation_enabled') or value['status'] in ('paused','stopped','complete','needs_attention'):
                notify(server,value)
                return
            job_id=value.get('job_id')
            if job_active(server,job_id):await asyncio.sleep(poll);continue
            if job_id:
                history=server.prompt_queue.get_history(prompt_id=job_id).get(job_id)
                if not history or (history.get('status') or {}).get('status_str')!='success':raise ValueError('The Foundry image job was cancelled, removed or failed. Captured images are retained; review them before continuing.')
                with store.LOCK:
                    value=store.read(run_id)
                    if value.get('job_id')==job_id:value.pop('job_id',None);store.write(value)
            if value['status']=='awaiting_approval':
                attempt=value['attempts'][-1];criteria=value['plan']['shots'][value['current']]['criteria']
                decision=assessment(attempt['review'],criteria,value.get('review_tolerance','Balanced'))
                if decision['acceptable']:
                    value=store.action(run_id,'accept',{'attempt_id':attempt['id'],'automatic':True});notify(server,value)
                    if value['status']=='complete':return
                elif sum(a['shot_id']==attempt['shot_id'] for a in value['attempts'])>=value['limits']['attempts']:
                    raise ValueError('This frame reached its retry limit. '+decision['decision_reason']+' Accept a usable attempt to continue, or stop the run.')
                else:
                    with store.LOCK:
                        value=store.read(run_id)
                        if value['status']!='awaiting_approval':continue
                        value['last_decision']='Retrying this frame: '+decision['decision_reason'];store.write(value)
            elif value['status']!='ready':
                raise ValueError('The previous job ended without a usable image review. Review a saved image or recover the interrupted job.')
            with store.LOCK:
                latest=store.read(run_id)
                if latest['status'] in ('paused','stopped','complete'):return
                operation='review_saved' if latest.pop('resume_review',False) else 'render'
                if operation=='review_saved':
                    attempt=latest['attempts'][-1];latest['status']='reviewing';store.write(latest)
                else:attempt=store.reserve(run_id)
            notify(server,store.read(run_id));queued=await submit(server,run_id,attempt,recipe,operation)
            if not queued:return
    except asyncio.CancelledError:raise
    except Exception as error:
        store.fail(run_id,str(error));notify(server,store.read(run_id))


def start(server,run_id):
    previous=TASKS.get(run_id)
    if previous is not None and not previous.done():return previous
    task=asyncio.create_task(run(server,run_id));TASKS[run_id]=task
    task.add_done_callback(lambda done:TASKS.pop(run_id,None) if TASKS.get(run_id) is done else None)
    return task


async def retry_saved_review(server,run_id,client_id='',continue_run=True):
    """Recover only the saved review; never reserve another image attempt."""
    from .foundry_ai import cached_review_response
    with store.LOCK:
        value=store.read(run_id)
        if job_active(server,value.get('job_id')):raise ValueError('The current Foundry job has not finished yet.')
        if value['status']!='needs_attention':raise ValueError('Choose a stopped run with an unfinished image review.')
        if not value['attempts']:raise ValueError('This run has no image to review.')
        attempt=value['attempts'][-1]
        if not attempt.get('image') or attempt.get('review'):raise ValueError('Choose a captured image whose review is unfinished.')
        if value['usage']['calls']>=value['limits']['calls'] and not cached_review_response(run_id,attempt['id']):raise ValueError('Assistant-call budget reached. The image is still saved.')
        recipe=load_recipe(run_id)
        if client_id:recipe['client_id']=str(client_id)[:128]
        if not isinstance(continue_run,bool):raise ValueError('Choose whether to continue the sequence after review.')
        if not continue_run:value['automation_enabled']=False
        value['status']='reviewing';value['last_error']='';value.pop('job_id',None);store.write(value)
    try:
        await submit(server,run_id,attempt,recipe,'review_saved')
        if value.get('automation_enabled'):start(server,run_id)
        current=store.read(run_id);notify(server,current);return store.public(current)
    except Exception as error:
        store.fail(run_id,str(error),attempt['id']);notify(server,store.read(run_id));raise
