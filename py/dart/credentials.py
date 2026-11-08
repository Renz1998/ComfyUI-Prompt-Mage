"""Provider-specific server credentials. Never expose contents to browser responses."""
import json
import os
import tempfile
from pathlib import Path


def credential_path(provider):
    if provider not in ('openai','deepseek'):
        raise ValueError('Unknown API provider.')
    import folder_paths
    return Path(folder_paths.get_user_directory()) / 'prompt_mage' / 'credentials' / (provider + '.json')


def stored_key(provider):
    try:
        path = credential_path(provider)
        if not path.exists():
            return ''
        if path.stat().st_size > 4096:
            raise ValueError('Credential file is invalid; replace it through the key panel.')
        value = json.loads(path.read_text(encoding='utf-8')).get('key','')
        if not isinstance(value,str):
            raise ValueError('Invalid saved API credential.')
        return value
    except ImportError:
        return ''  # Unit-test / non-ComfyUI environments have no user directory.


def store_key(provider, key):
    path = credential_path(provider)
    if not key:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=provider+'-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(handle,'w',encoding='utf-8') as stream:
            json.dump({'key':key},stream)
        os.chmod(temporary,0o600)
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
