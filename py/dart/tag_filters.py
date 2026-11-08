"""Curated exact tag groups, expanded through the bundled vocabulary's aliases."""
import re
from .tags import split_tags
from .vocabulary import vocabulary, normalized

GROUPS = {
    'Full color': ('monochrome, greyscale, grayscale, black and white, partially colored, limited palette',
                   'Use full color throughout; do not introduce monochrome or greyscale treatment.'),
    'No text / watermarks': ('text, watermark, signature, artist name, username, dated, copyright name, speech bubble, translation request',
                            'Do not add visible writing, signatures, watermarks or speech bubbles.'),
    'Photography': ('anime, manga, comic, illustration, drawing, sketch, lineart, pixel art, painting',
                    'Describe a photographic scene rather than an illustration, comic or painting.'),
}
PRESETS = ['Custom only', *GROUPS, 'Full color + clean photo']


def expand(text):
    """Canonical names and verified alias spellings; never substring-match colors."""
    vocab = vocabulary()
    found = {}
    for tag in split_tags(text):
        clean = re.sub(r'^\((.*):[0-9.]+\)$', r'\1', tag.strip()).replace('_', ' ').casefold()
        if clean:
            found[normalized(clean)] = clean
        for key in vocab.lookup(clean):
            for spelling, ids in vocab.exact.items():
                if key in ids:
                    found[spelling] = spelling
    return sorted(found.values())


def build_filter(preset, prevent=True, clean=True, extra_banned='', remove='', protected=''):
    if preset not in PRESETS:
        raise ValueError('Choose a supported tag filter preset.')
    if any(len(t) > 8192 for t in (extra_banned, remove, protected)):
        raise ValueError('Each custom tag field must be at most 8192 characters.')
    groups = list(GROUPS) if preset == 'Full color + clean photo' else ([preset] if preset in GROUPS else [])
    base = ', '.join(GROUPS[g][0] for g in groups)
    bans = expand(', '.join([base if prevent else '', extra_banned]))
    removals = expand(', '.join([base if clean else '', remove]))
    protected_tags = expand(protected)
    conflicts = sorted(set(map(normalized, protected_tags)) & set(map(normalized, bans + removals)))
    if conflicts:
        raise ValueError('Protected tags conflict with exclusions: ' + ', '.join(conflicts) + '. Change the preset or custom lists.')
    return dict(version=1, preset=preset, banned=bans, removed=removals,
                protected=split_tags(protected), guidance=[GROUPS[g][1] for g in groups] if prevent or clean else [],
                note='Exact vocabulary/alias matching only. Broader meaning and assistant wording remain model-guided. Protected tags are not an allow-only whitelist.')


def check_recipe(recipe):
    if not recipe:
        return dict(banned=[], removed=[], protected=[], guidance=[])
    if not isinstance(recipe, dict) or recipe.get('version') != 1:
        raise ValueError('Connect a Prompt Mage Tag Filters recipe.')
    for name in ('banned', 'removed', 'protected', 'guidance'):
        values = recipe.get(name)
        if not isinstance(values, list) or len(values) > 2048 or any(not isinstance(x, str) or len(x) > 8192 for x in values):
            raise ValueError('Invalid tag filter recipe field: ' + name)
    return recipe


def clean_text(text, recipe):
    recipe = check_recipe(recipe)
    excluded = set(map(normalized, recipe['removed']))
    protected = set(map(normalized, expand(', '.join(recipe['protected'])))) if recipe['protected'] else set()
    return ', '.join(t for t in split_tags(text) if normalized(re.sub(r'^\((.*):[0-9.]+\)$', r'\1', t)) not in excluded or normalized(t) in protected)


def dart_lists(recipe, banned, removed, kept):
    recipe = check_recipe(recipe)
    keep = ', '.join([kept, *recipe['protected']]).strip(', ')
    ban = ', '.join([banned, *recipe['banned']]).strip(', ')
    remove = ', '.join([removed, *recipe['removed']]).strip(', ')
    conflicts = set(map(normalized, expand(keep))) & set(map(normalized, expand(ban + ', ' + remove))) if keep else set()
    if conflicts:
        raise ValueError('Keep/protected tags conflict with tag filters: ' + ', '.join(sorted(conflicts)))
    return ban, remove, keep
