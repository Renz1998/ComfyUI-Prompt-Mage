"""Extract one JSON artifact without treating chat prose as model input."""
import json
import re


def json_values(text):
    if not isinstance(text, str) or len(text) > 262144:
        raise ValueError('Reply is too large to extract safely.')
    try:
        whole = json.loads(text.strip())
    except ValueError:
        pass
    else:
        yield whole
        return
    decoder = json.JSONDecoder()
    offset = 0
    attempts = 0
    while attempts < 64:
        start = re.search(r'[\{\[]', text[offset:])
        if not start:
            return
        position = offset + start.start()
        attempts += 1
        try:
            value, end = decoder.raw_decode(text, position)
        except ValueError:
            offset = position + 1
            continue
        yield value
        offset = end


def select_json(text, predicate=None):
    matches = {}
    for value in json_values(text):
        if predicate is None or predicate(value):
            matches[json.dumps(value, sort_keys=True, ensure_ascii=False)] = value
    if not matches:
        raise ValueError('No complete matching JSON object found. The reply may be truncated or use the wrong schema.')
    if len(matches) != 1:
        raise ValueError('This reply contains multiple different JSON prompts. Keep one prompt before applying it.')
    return next(iter(matches.values()))


def is_moss(value):
    return isinstance(value, dict) and 'summary' in value and 'items' in value
