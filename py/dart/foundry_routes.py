"""Same-origin, bounded run controls. These routes never call an AI or queue work."""
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
            if operation=='read':return dict(run=store.public(value))
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
                if value['usage']['calls']>=value['limits']['calls']:raise ValueError('Assistant-call budget reached.')
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
            return dict(run=store.public(store.action(identifier,operation,data)))

    @PromptServer.instance.routes.post('/prompt_mage/foundry')
    async def control(request):
        if not trusted_request(request):return web.json_response({'error':'Use this ComfyUI page.'},status=403)
        try:
            if request.content_type!='application/json' or not request.content_length or request.content_length>262144:raise ValueError('Invalid Foundry request size.')
            data=await request.json()
            if not isinstance(data,dict):raise ValueError('Expected a Foundry action.')
            result=await asyncio.to_thread(process,data)
            return web.json_response(result,headers={'Cache-Control':'no-store'})
        except (ValueError,KeyError,TypeError,OSError) as error:
            return web.json_response({'error':str(error)},status=400)
    return True
