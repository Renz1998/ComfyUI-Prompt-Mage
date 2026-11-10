from .openai_routes import trusted_request
from .grimoire import LOCK, memory_path, read_memory
from pathlib import Path


def register_grimoire_routes():
    try:
        from server import PromptServer
        from aiohttp import web
    except ImportError:
        return False
    if getattr(PromptServer, 'instance', None) is None:
        return False

    @PromptServer.instance.routes.post('/prompt_mage/grimoire/attachment')
    async def upload_attachment(request):
        if not trusted_request(request):
            return web.json_response({'error':'Use this ComfyUI page.'},status=403)
        from .grimoire_attachments import MAX_BYTES, save_attachment
        import asyncio
        try:
            if request.content_type != 'multipart/form-data':
                raise ValueError('Choose a file with the attachment button.')
            reader = await request.multipart()
            part = await reader.next()
            if part is None or part.name != 'file' or not part.filename:
                raise ValueError('No file selected.')
            raw = bytearray()
            while chunk := await part.read_chunk(65536):
                raw.extend(chunk)
                if len(raw) > MAX_BYTES:
                    raise ValueError('Each attachment must be under 16 MB.')
            value = await asyncio.to_thread(save_attachment,part.filename,bytes(raw))
            return web.json_response(value,headers={'Cache-Control':'no-store'})
        except ValueError as error:
            return web.json_response({'error':str(error)},status=400)
        except Exception:
            return web.json_response({'error':'Could not read this file. Check its format and server storage permissions.'},status=400)

    @PromptServer.instance.routes.post('/prompt_mage/grimoire/attachment/read')
    async def read_attachment(request):
        if not trusted_request(request):
            return web.json_response({'error':'Use this ComfyUI page.'},status=403)
        from .grimoire_attachments import load_attachment, public_attachment
        import asyncio
        try:
            if request.content_type != 'application/json' or not request.content_length or request.content_length > 4096:
                raise ValueError('Invalid attachment request.')
            data = await request.json()
            value = await asyncio.to_thread(load_attachment,data['id'])
            return web.json_response(public_attachment(value),headers={'Cache-Control':'no-store'})
        except (ValueError,KeyError,TypeError,OSError):
            return web.json_response({'error':'Attachment unavailable. Attach the file again.'},status=400)

    @PromptServer.instance.routes.get('/prompt_mage/grimoire/capabilities')
    async def capabilities(request):
        import inspect
        import execution
        supported = 'partial_execution_list' in inspect.signature(execution.validate_prompt).parameters
        return web.json_response({'partial_execution': supported}, headers={'Cache-Control':'no-store'})

    @PromptServer.instance.routes.post('/prompt_mage/grimoire/message')
    async def edit_message(request):
        if not trusted_request(request):
            return web.json_response({'error':'Use this ComfyUI page.'},status=403)
        from .grimoire import edit_assistant
        try:
            if request.content_type != 'application/json' or not request.content_length or request.content_length > 262144:
                raise ValueError('Invalid edit request size.')
            data = await request.json()
            value = edit_assistant(data['id'], data['index'], data['original'], data['text'])
            return web.json_response(value, headers={'Cache-Control':'no-store'})
        except (ValueError,KeyError,TypeError,OSError) as error:
            return web.json_response({'error':str(error)},status=400)

    @PromptServer.instance.routes.get('/prompt_mage/grimoire/history')
    @PromptServer.instance.routes.post('/prompt_mage/grimoire/history')
    async def history(request):
        if request.headers.get('Sec-Fetch-Site') != 'same-origin' and not trusted_request(request):
            return web.json_response({'error':'Use this ComfyUI page.'}, status=403)
        try:
            if request.method == 'POST':
                if request.content_type != 'application/json' or not request.content_length or request.content_length > 4096:
                    raise ValueError('Expected a small settings request.')
                data = await request.json()
                chapter = data.get('id','')
            else:
                chapter = request.query.get('id','')
            with LOCK:
                value = read_memory(memory_path(chapter))
                from .grimoire_prompt import prepare_turn
                value['turns'] = [prepare_turn(t,value.get('settings')) for t in value['turns']]
        except (ValueError, OSError, TypeError, AttributeError):
            return web.json_response({'error':'Could not load conversation.'}, status=400)
        return web.json_response(value, headers={'Cache-Control':'no-store'})
    @PromptServer.instance.routes.post('/prompt_mage/grimoire/chats')
    async def chats(request):
        if not trusted_request(request):
            return web.json_response({'error':'Use this ComfyUI page.'},status=403)
        import asyncio
        def collect():
            root = memory_path('list-root').parent
            result=[]
            with LOCK:
                paths=sorted(root.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:500]
                for path in paths:
                    try:
                        value=read_memory(path)
                        first=next((t['content'] for t in value['turns'] if t['role']=='user'),'Empty conversation')
                        result.append(dict(id=path.stem,title=first[:90].replace('\n',' '),updated=path.stat().st_mtime,turns=len(value['turns'])))
                    except (OSError,ValueError,TypeError,AttributeError):
                        continue
            return result
        return web.json_response({'chats':await asyncio.to_thread(collect)},headers={'Cache-Control':'no-store'})
    @PromptServer.instance.routes.post('/prompt_mage/grimoire/scroll')
    async def scroll(request):
        if not trusted_request(request):return web.json_response({'error':'Use this ComfyUI page.'},status=403)
        from .spell_scroll import active_scroll, approve
        try:
            if request.content_type!='application/json' or not request.content_length or request.content_length>262144:raise ValueError('Invalid request size.')
            data=await request.json()
            if data.get('apply'):
                value=approve(data['scroll_id'],data['conversation_id'],data['index'],data['text'],data.get('mode','Latest response'),data.get('field',''))
            else:
                with LOCK:value=active_scroll(data['scroll_id'])
            return web.json_response({'active':value},headers={'Cache-Control':'no-store'})
        except (ValueError,KeyError,TypeError,OSError) as error:
            return web.json_response({'error':str(error)},status=400)
    return True
