"""Write-only, same-origin session-key settings. Never returns a key or writes it to disk."""
from urllib.parse import urlsplit
from .deepseek_assistant import key_status, set_persistent_key


def trusted_request(request):
    if request.headers.get('Sec-Fetch-Site') == 'cross-site':
        return False
    origin = request.headers.get('Origin')
    if origin:
        parsed = urlsplit(origin)
        return parsed.scheme in ('http', 'https') and parsed.netloc.lower() == request.host.lower()
    return request.remote in ('127.0.0.1', '::1')


def register_deepseek_routes():
    try:
        from server import PromptServer
        from aiohttp import web
    except ImportError:
        return False
    if getattr(PromptServer, 'instance', None) is None:
        return False
    routes = PromptServer.instance.routes

    @routes.get('/prompt_mage/deepseek/key')
    async def status(request):
        return web.json_response(key_status(), headers={'Cache-Control':'no-store'})

    @routes.post('/prompt_mage/deepseek/key')
    async def update(request):
        if not trusted_request(request):
            return web.json_response({'error':'Use the key panel from this ComfyUI page.'}, status=403)
        if request.content_type != 'application/json' or (request.content_length or 0) > 4096:
            return web.json_response({'error':'Expected a small JSON settings request.'}, status=400)
        try:
            raw = bytearray()
            async for chunk in request.content.iter_chunked(1024):
                raw.extend(chunk)
                if len(raw) > 4096:
                    raise ValueError()
            import json
            data = json.loads(raw)
            key = data.get('key')
            if not isinstance(key, str):
                raise ValueError()
            set_persistent_key(key.strip())
        except (ValueError, TypeError, AttributeError):
            return web.json_response({'error':'Check key format and ComfyUI user-directory write permissions.'},status=400)
        return web.json_response(key_status(), headers={'Cache-Control':'no-store'})
    return True
