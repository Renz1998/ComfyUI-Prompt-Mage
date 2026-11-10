"""Same-origin run controls; only explicit start/continue actions launch the controller."""
import asyncio
from . import foundry as store
from .openai_routes import trusted_request


def register_foundry_routes():
    try:
        from server import PromptServer
        from aiohttp import web
    except ImportError:return False
    if getattr(PromptServer,'instance',None) is None:return False

    def process(data):
        operation=data.get('operation','read')
        with store.LOCK:
            if operation=='catalog':
                runs=[]
                paths=sorted((store.root()/'runs').glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]
                for path in paths:
                    try:
                        v=store.read(path.stem)
                        runs.append(dict(id=v['id'],title=(v.get('plan') or {}).get('title',v['brief'][:60]),status=v['status']))
                    except (OSError,ValueError,KeyError):continue
                return dict(runs=runs,templates=store.templates())
            identifier=data['id'];store.checked_id(identifier)
            if operation=='bind_job' and not store.run_path(identifier).exists():
                job=data['job_id']
                if not isinstance(job,str) or not 1<=len(job)<=100:raise ValueError('Invalid queue job ID.')
                import json
                path=store.root()/'jobs';path.mkdir(exist_ok=True)
                (path/(identifier+'.json')).write_text(json.dumps({'job_id':job}),encoding='utf-8')
                return {'queued':True}
            value=store.read(identifier)
            if operation in ('reserve','reserve_review'):
                queue=getattr(PromptServer.instance,'prompt_queue',None)
                if queue is not None:
                    running,pending=queue.get_current_queue()
                    if any(str(item[1])==value.get('job_id') for item in running+pending):
                        raise ValueError('The previous Foundry job is still in the ComfyUI queue. Wait for it to finish.')
            if operation=='read':
                from .foundry_runner import TASKS,job_active
                result=store.public(value);task=TASKS.get(identifier)
                result['controller_running']=bool(task and not task.done()) or job_active(PromptServer.instance,value.get('job_id'))
                return dict(run=result)
            if operation in ('approve_start','accept_continue','continue_auto','retry_auto'):
                from . import foundry_runner as runner
                server=PromptServer.instance
                if runner.job_active(server,value.get('job_id')):raise ValueError('Wait for the current Foundry job to finish before continuing.')
                if operation=='approve_start':
                    if value['status']!='plan_ready':raise ValueError('Preview a plan before approving it.')
                    runner.save_recipe(identifier,data['job'],data['node_id'],data.get('client_id',''))
                    value=store.action(identifier,'approve',data)
                elif operation=='accept_continue':value=store.action(identifier,'accept',data)
                else:
                    if data.get('job') and not runner.recipe_path(identifier).exists():runner.save_recipe(identifier,data['job'],data['node_id'],data.get('client_id',''))
                    else:runner.load_recipe(identifier)
                    if not value.get('approved') or value['status'] in ('complete','stopped'):raise ValueError('Approve a new plan before starting.')
                    if value['status']=='paused':value=store.action(identifier,'resume')
                    if value['status']=='needs_attention':
                        latest=value['attempts'][-1] if value['attempts'] else {}
                        if latest.get('image') and not latest.get('review'):raise ValueError('Review the captured image before continuing. Use Review saved image.')
                        value.update(status='ready',last_error='')
                value['automation_enabled']=value.get('run_mode','Automatic')=='Automatic'
                value.pop('job_id',None);store.write(value)
                return dict(run=store.public(value))
            if operation=='preview':
                from .foundry_ai import preview
                attempt=store.attempt_for(value,data['attempt_id'])
                if not attempt.get('image'):raise ValueError('No captured image for this attempt.')
                return dict(image=preview(identifier,attempt['id']))
            if operation=='reserve':
                attempt=store.reserve(identifier)
                return dict(attempt=attempt,run=store.public(store.read(identifier)))
            if operation=='reserve_review':
                if value['status']!='needs_attention':raise ValueError('Finish or recover the current job first.')
                attempt=store.attempt_for(value,data['attempt_id'])
                if not attempt.get('image') or attempt.get('review'):raise ValueError('Choose a captured image with an unfinished review.')
                from .foundry_ai import cached_review_response
                if value['usage']['calls']>=value['limits']['calls'] and not cached_review_response(identifier,attempt['id']):raise ValueError('Assistant-call budget reached.')
                value['status']='reviewing';store.write(value)
                return dict(run=store.public(value))
            if operation=='bind_job':
                job=data['job_id']
                if not isinstance(job,str) or not 1<=len(job)<=100:raise ValueError('Invalid queue job ID.')
                value['job_id']=job;store.write(value)
                return dict(run=store.public(value))
            if operation in ('mark_interrupted','failed'):
                # Never recover a record while its native ComfyUI job is still active.
                queue=getattr(PromptServer.instance,'prompt_queue',None)
                if queue is not None:
                    running,pending=queue.get_current_queue()
                    if any(str(item[1])==value.get('job_id') for item in running+pending):
                        raise ValueError('This job is still in the ComfyUI queue. Wait for it to finish or cancel it there.')
                if operation=='failed':
                    store.fail(identifier,str(data.get('error','Queue request failed.')),data.get('attempt_id'))
                    return dict(run=store.public(store.read(identifier)))
            if operation not in ('approve','accept','pause','resume','stop','mark_interrupted','save_template'):
                raise ValueError('Unknown Foundry action.')
            result=store.action(identifier,operation,data)
            if operation=='resume' and result.get('automation_enabled') and result['status']=='needs_attention':
                from .foundry_runner import job_active
                if job_active(PromptServer.instance,result.get('job_id')):result['status']='rendering'
                else:
                    result.pop('job_id',None);result['status']='ready'
                    if result['attempts'] and result['attempts'][-1].get('image') and not result['attempts'][-1].get('review'):result['resume_review']=True
                result['last_error']='';store.write(result)
            return dict(run=store.public(result))

    @PromptServer.instance.routes.post('/prompt_mage/foundry')
    async def control(request):
        if not trusted_request(request):return web.json_response({'error':'Use this ComfyUI page.'},status=403)
        try:
            if request.content_type!='application/json' or not request.content_length or request.content_length>4*1024*1024:raise ValueError('Invalid Foundry request size.')
            data=await request.json()
            if not isinstance(data,dict):raise ValueError('Expected a Foundry action.')
            if request.content_length>262144 and data.get('operation') not in ('approve_start','continue_auto','retry_auto'):raise ValueError('Invalid Foundry request size.')
            if data.get('operation')=='retry_review':
                from .foundry_runner import retry_saved_review
                result=dict(run=await retry_saved_review(PromptServer.instance,data['id'],data.get('client_id',''),data.get('continue_run',True)))
            else:result=await asyncio.to_thread(process,data)
            value=result.get('run')
            if value and value.get('automation_enabled') and data.get('operation') in ('approve_start','accept_continue','continue_auto','retry_auto','bind_job','resume') and value['status'] not in ('paused','stopped','complete','needs_attention'):
                from .foundry_runner import start
                start(PromptServer.instance,value['id'])
                value['controller_running']=True
            return web.json_response(result,headers={'Cache-Control':'no-store'})
        except (ValueError,KeyError,TypeError,OSError) as error:
            return web.json_response({'error':str(error)},status=400)
    return True
