from .credentials import stored_key, store_key
"""Server-side OpenAI Responses adapter. Credentials never enter workflow inputs."""
import base64
import io
import json
import os
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

# Standard short-context USD / 1M tokens, verified against official model pages 2026-11-07.
# Labels are a pricing snapshot, not a billing quote. No priority/pro mode is enabled.
MODELS = {
    'GPT-6.1 Terra · Recommended · $1 input / $5 output': 'gpt-6.1-terra',
    'GPT-6.1 Sol · Recommended · $2 input / $10 output': 'gpt-6.1-sol',
    'GPT-6 Luna · Budget · $0.10 input / $0.50 output': 'gpt-6-luna',
    'GPT-6 Astra · WARNING: HIGH COST · $10 input / $50 output': 'gpt-6-astra',
}
DEFAULT_MODEL = next(iter(MODELS))
_session_key = ''


def key_status():
    environment = bool(os.environ.get('OPENAI_API_KEY', '').strip())
    return dict(configured=bool(_session_key) or bool(stored_key('openai')) or environment, saved_configured=bool(stored_key('openai')),
                session_configured=bool(_session_key), environment_configured=environment)


def set_session_key(key):
    global _session_key
    if key and (not isinstance(key, str) or not key.startswith('sk-') or not 20 <= len(key) <= 512 or any(ch.isspace() for ch in key)):
        raise ValueError('Enter a valid OpenAI API key beginning with sk-.')
    _session_key = key


def resolve_key(name):
    return (_session_key if name == 'OPENAI_API_KEY' and _session_key else stored_key('openai') if name == 'OPENAI_API_KEY' and stored_key('openai') else os.environ.get(name, '')).strip()


class OpenAIRequestError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward a bearer credential to another destination.


def image_data_url(image):
    from PIL import Image
    array = (image[0, :, :, :3].detach().cpu().clamp(0, 1).numpy() * 255).round().astype('uint8')
    stream = io.BytesIO()
    Image.fromarray(array).save(stream, format='PNG')
    if stream.tell() > 20 * 1024 * 1024:
        raise ValueError('API reference image exceeds 20 MB. Lower Image megapixel budget.')
    return 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode('ascii')


class OpenAIEncoder:
    is_remote = True

    def __init__(self, model=DEFAULT_MODEL, key_env='OPENAI_API_KEY', timeout=180):
        if model not in MODELS:
            raise ValueError('Choose an OpenAI model from the dropdown.')
        if not key_env or not key_env.replace('_', '').isalnum():
            raise ValueError('Enter the environment variable NAME for the API key, not the key itself.')
        if not resolve_key(key_env):
            raise ValueError('Add an API key in Archmage’s OpenAI key panel, or set ' + key_env + ' on the ComfyUI server. Never paste keys into workflow text widgets.')
        if not 10 <= timeout <= 600:
            raise ValueError('OpenAI timeout must be 10–600 seconds.')
        self.model, self.key_env, self.timeout = MODELS[model], key_env, timeout
        self.calls = []

    def execute(self, prompt, system_prompt='', max_length=4096, thinking=False, image=None, **unused):
        if not 128 <= max_length <= 16384:
            raise ValueError('API token limit must be 128–16384 per request, including reasoning.')
        content = [{'type': 'input_text', 'text': prompt}]
        if image is not None:
            content.append({'type': 'input_image', 'image_url': image_data_url(image), 'detail': 'auto'})
        effort = 'medium' if thinking else ('low' if self.model in ('gpt-6.1-sol', 'gpt-6-astra') else 'none')
        payload = dict(model=self.model, instructions=system_prompt,
                       input=[{'role': 'user', 'content': content}], store=False,
                       max_output_tokens=max_length, reasoning={'effort': effort})
        key = resolve_key(self.key_env)
        if not key:
            raise OpenAIRequestError('The API key was removed. Add it again in the OpenAI key panel.')
        request = Request('https://api.openai.com/v1/responses',
                          data=json.dumps(payload).encode('utf-8'),
                          headers={'Authorization': 'Bearer ' + key,
                                   'Content-Type': 'application/json'})
        try:
            with build_opener(NoRedirect()).open(request, timeout=self.timeout) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise OpenAIRequestError('OpenAI response exceeded the supported size.')
            value = json.loads(raw)
        except HTTPError as error:
            hints = {400: 'Unsupported request or model parameters.', 401: 'API key is invalid or expired.',
                     403: 'This project cannot use the selected model.', 404: 'Model unavailable for this project.',
                     429: 'Rate limit or billing quota exceeded; check your OpenAI dashboard.'}
            raise OpenAIRequestError(f'OpenAI HTTP {error.code}: ' + hints.get(error.code, 'Service request failed.') +
                                     ' No automatic retry was made.') from None
        except (URLError, TimeoutError):
            raise OpenAIRequestError('OpenAI request timed out or could not connect. It may still have been processed and billed. No automatic retry was made.') from None
        except (ValueError, KeyError):
            raise OpenAIRequestError('OpenAI returned an invalid response. No automatic retry was made.') from None
        usage = value.get('usage') or {}
        details = usage.get('output_tokens_details') or {}
        call = dict(model=self.model, reasoning_effort=effort,
                    input_tokens=usage.get('input_tokens', 0), output_tokens=usage.get('output_tokens', 0),
                    reasoning_tokens=details.get('reasoning_tokens', 0), status=value.get('status'))
        self.calls.append(call)
        parts = [part for item in value.get('output', []) if item.get('type') == 'message'
                 for part in item.get('content', [])]
        if any(part.get('type') == 'refusal' for part in parts):
            raise OpenAIRequestError('OpenAI declined this request. The provider applies its own content policies. No retry or output rewriting was performed.')
        if value.get('status') != 'completed':
            raise OpenAIRequestError('OpenAI did not return a complete answer. Check the token ceiling, reasoning setting or service status. No automatic retry was made.')
        text = '\n'.join(part['text'] for part in parts if part.get('type') == 'output_text' and isinstance(part.get('text'), str)).strip()
        if not text:
            raise OpenAIRequestError('OpenAI returned no usable text. No automatic retry was made.')
        return SimpleNamespace(args=[text], api_usage=call)


def execute_generation(clip, **kwargs):
    if isinstance(clip, OpenAIEncoder):
        # Native interruption checks prevent subsequent paid stages after cancellation.
        try:
            from comfy.model_management import throw_exception_if_processing_interrupted as check
        except ImportError:
            check = lambda: None
        check()
        result = clip.execute(**kwargs)
        check()
        return result
    from comfy_extras.nodes_textgen import TextGenerate
    return TextGenerate.execute(clip=clip, **kwargs)


def set_persistent_key(key):
    global _session_key
    previous = _session_key
    set_session_key(key)
    try:
        store_key('openai', key)
    except (OSError, ValueError):
        _session_key = previous
        raise ValueError('Could not save API key. Check ComfyUI user-directory permissions.') from None
