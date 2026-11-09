"""Transactional conversation storage; summaries never replace pinned instructions."""
import json
import os
import re
import threading
from pathlib import Path

LOCK = threading.RLock()


def memory_path(conversation_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,80}', conversation_id):
        raise ValueError('Use a conversation ID of 8–80 letters, digits, hyphens or underscores. New chapter creates one.')
    import folder_paths
    root = Path(folder_paths.get_user_directory()) / 'prompt_mage' / 'grimoire'
    root.mkdir(parents=True, exist_ok=True)
    return root / (conversation_id + '.json')


def read_memory(path):
    if not path.exists():
        return dict(version=1, summary='', turns=[])
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('Conversation file exceeds 2 MB. Start a new chapter.')
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('version') != 1 or not isinstance(value.get('turns'), list) or not isinstance(value.get('summary'), str):
        raise ValueError('Conversation memory is invalid. Start a new chapter or restore its file.')
    for turn in value['turns']:
        if turn.get('role') not in ('user','assistant') or not isinstance(turn.get('content'), str):
            raise ValueError('Invalid conversation turn.')
    return value


def save_memory(path, value):
    raw = json.dumps(value, ensure_ascii=False, indent=2)
    if len(raw.encode()) > 2 * 1024 * 1024:
        raise ValueError('Conversation reached 2 MB. Compact it or start a new chapter.')
    temp = path.with_suffix('.tmp')
    temp.write_text(raw, encoding='utf-8')
    os.replace(temp, path)


def transcript(value):
    return '\n\n'.join(t['role'].upper() + ': ' + t['content'] for t in value['turns'])


def edit_assistant(conversation_id, index, original, text):
    """Manual response edits cost no model call; discard later turns explicitly in the UI."""
    if not isinstance(text, str) or not text.strip() or len(text) > 65536:
        raise ValueError('Enter a nonempty response under 65,536 characters.')
    with LOCK:
        path = memory_path(conversation_id)
        state = read_memory(path)
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(state['turns']):
            raise ValueError('Message changed. Refresh history.')
        turn = state['turns'][index]
        if turn['role'] != 'assistant' or turn['content'] != original:
            raise ValueError('Message changed. Refresh history before editing.')
        from .grimoire_prompt import extract_response
        mode = turn.get('mode', 'Latest response')
        extract_response(text, 'Prompt workshop', mode, turn.get('field',state.get('settings',{}).get('json_field','prompt')), turn.get('width',1024), turn.get('height',1024))
        state['turns'] = state['turns'][:index+1]
        turn.update(content=text, valid=True)
        save_memory(path,state)
        return state


def select_output(text, mode, section):
    if mode == 'Latest response':
        return text
    value = text.strip()
    if value.startswith('```'):
        lines = value.splitlines()
        if lines[-1].strip() == '```':
            value = '\n'.join(lines[1:-1])
    parsed = json.loads(value)
    if mode == 'JSON field':
        for key in section.split('.'):
            if not isinstance(parsed, dict) or key not in parsed:
                raise ValueError('JSON field not found: ' + section)
            parsed = parsed[key]
        return parsed if isinstance(parsed, str) else json.dumps(parsed, ensure_ascii=False, indent=2)
    if mode != 'JSON only':
        raise ValueError('Choose a supported output selection.')
    return json.dumps(parsed, ensure_ascii=False, indent=2)
