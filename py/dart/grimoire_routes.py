from .openai_routes import trusted_request
from .grimoire import LOCK, memory_path, read_memory


def register_grimoire_routes():
    try:
        from server import PromptServer
        from aiohttp import web
    except ImportError:
        return False
    if getattr(PromptServer, 'instance', None) is None:
        return False

    @PromptServer.instance.routes.get('/prompt_mage/grimoire/history')
    async def history(request):
        if request.headers.get('Sec-Fetch-Site') != 'same-origin' and not trusted_request(request):
            return web.json_response({'error':'Use this ComfyUI page.'}, status=403)
        try:
            with LOCK:
                value = read_memory(memory_path(request.query.get('id','')))
        except (ValueError, OSError):
            return web.json_response({'error':'Could not load conversation.'}, status=400)
        return web.json_response(value, headers={'Cache-Control':'no-store'})
    return True
