from .credentials import stored_key, store_key
"""Official DeepSeek Chat Completions adapter; independent session credentials."""
import json
import os
from types import SimpleNamespace
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError
from .openai_assistant import OpenAIEncoder, OpenAIRequestError, NoRedirect, image_data_url

# Official API documentation checked 2026-11-09. Aliases may change backing releases.
MODELS = {'DeepSeek V4.1 Flash · Recommended · Text + images': 'deepseek-flash',
          'DeepSeek V4 Pro · Text only · Check pricing': 'deepseek-v4-pro'}
DEFAULT_MODEL = next(iter(MODELS))
_session_key = ''


def key_status():
    environment = bool(os.environ.get('DEEPSEEK_API_KEY', '').strip())
    return dict(configured=bool(_session_key) or bool(stored_key('deepseek')) or environment, saved_configured=bool(stored_key('deepseek')), session_configured=bool(_session_key), environment_configured=environment)


def set_session_key(key):
    global _session_key
    if not isinstance(key, str) or key and (not key.startswith('sk-') or not 20 <= len(key) <= 512 or any(c.isspace() for c in key)):
        raise ValueError('Enter a valid DeepSeek API key beginning with sk-.')
    _session_key = key


def resolve_key(name):
    return (_session_key if name == 'DEEPSEEK_API_KEY' and _session_key else stored_key('deepseek') if name == 'DEEPSEEK_API_KEY' and stored_key('deepseek') else os.environ.get(name, '')).strip()


class DeepSeekEncoder(OpenAIEncoder):
    def __init__(self, model=DEFAULT_MODEL, key_env='DEEPSEEK_API_KEY', timeout=180):
        if model not in MODELS:
            raise ValueError('Choose a DeepSeek model from the dropdown.')
        if not key_env or not key_env.replace('_', '').isalnum():
            raise ValueError('Enter an API key environment variable NAME, not the secret.')
        if not resolve_key(key_env):
            raise ValueError('Add a key in the DeepSeek key panel or set ' + key_env + ' on the ComfyUI server.')
        if not 10 <= timeout <= 600:
            raise ValueError('DeepSeek timeout must be 10–600 seconds.')
        self.model, self.key_env, self.timeout = MODELS[model], key_env, timeout
        self.calls = []

    def execute(self, prompt, system_prompt='', max_length=4096, thinking=False, image=None, **unused):
        if not 128 <= max_length <= 16384:
            raise ValueError('API token limit must be 128–16384 per request, including thinking.')
        if image is not None and self.model != 'deepseek-flash':
            raise ValueError('DeepSeek Pro is text-only here. Select DeepSeek Flash for reference images.')
        content = prompt
        if image is not None:
            content = [{'type': 'text', 'text': prompt}]
            for reference in image if isinstance(image, (list, tuple)) else [image]:
                content.append({'type': 'image_url', 'image_url': {'url': image_data_url(reference)}})
        payload = dict(model=self.model, messages=[{'role':'system','content':system_prompt}, {'role':'user','content':content}],
                       stream=False, max_tokens=max_length, thinking={'type':'enabled' if thinking else 'disabled'})
        if thinking:
            payload['reasoning_effort'] = 'high'
        key = resolve_key(self.key_env)
        if not key:
            raise OpenAIRequestError('DeepSeek session key was removed. Add it again.')
        request = Request('https://api.deepseek.com/chat/completions', data=json.dumps(payload).encode(),
                          headers={'Authorization':'Bearer ' + key, 'Content-Type':'application/json'})
        try:
            with build_opener(NoRedirect()).open(request, timeout=self.timeout) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError()
            value = json.loads(raw)
            choice = value['choices'][0]
            message = choice['message']
            if not isinstance(message, dict):
                raise ValueError()
        except HTTPError as error:
            hints = {401:'Invalid or expired API key.', 402:'Insufficient balance.', 429:'Rate limit exceeded.', 400:'Unsupported request or model parameters.'}
            raise OpenAIRequestError(f'DeepSeek HTTP {error.code}: ' + hints.get(error.code, 'Service request failed.') + ' No automatic retry was made.') from None
        except (URLError, TimeoutError):
            raise OpenAIRequestError('DeepSeek connection failed or timed out. The request may still be billed. No automatic retry was made.') from None
        except (ValueError, KeyError, IndexError, TypeError):
            raise OpenAIRequestError('DeepSeek returned an invalid response. No automatic retry was made.') from None
        usage = value.get('usage') or {}
        details = usage.get('completion_tokens_details') or {}
        call = dict(model=self.model, reasoning_effort='high' if thinking else 'none',
                    input_tokens=usage.get('prompt_tokens',0), output_tokens=usage.get('completion_tokens',0),
                    reasoning_tokens=details.get('reasoning_tokens',0), status=choice.get('finish_reason'))
        self.calls.append(call)
        if message.get('refusal') or choice.get('finish_reason') == 'content_filter':
            raise OpenAIRequestError('DeepSeek declined this request. No retry or refusal rewriting was performed.')
        if choice.get('finish_reason') != 'stop':
            raise OpenAIRequestError('DeepSeek did not finish the answer. Check the token ceiling/thinking setting. No automatic retry was made.')
        text = message.get('content')
        if not isinstance(text, str) or not text.strip():
            raise OpenAIRequestError('DeepSeek returned no final text. Increase the token ceiling or disable Thinking. No automatic retry was made.')
        # Private reasoning_content is deliberately neither returned nor persisted.
        return SimpleNamespace(args=[text.strip()], api_usage=call)


def set_persistent_key(key):
    global _session_key
    previous = _session_key
    set_session_key(key)
    try:
        store_key('deepseek', key)
    except (OSError, ValueError):
        _session_key = previous
        raise ValueError('Could not save API key. Check ComfyUI user-directory permissions.') from None
