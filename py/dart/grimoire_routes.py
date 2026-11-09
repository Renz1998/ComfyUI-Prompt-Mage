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
    return True
