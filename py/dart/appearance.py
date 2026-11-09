"""Reusable, optional visual-edit instructions shared by both assistants."""
import json
import re
from copy import deepcopy

KEEP = "Keep unchanged"
MISMATCH_POLICIES = ["Warn and continue", "Block downstream"]


class AppearanceMismatch(ValueError):
    """Valid generated content whose requested appearance wording is unconfirmed."""
    def __init__(self, issues):
        self.issues = issues
        super().__init__("\n".join(issue["message"] for issue in issues))


def appearance_report(settings, issues, policy, attempts=0, corrected=False, output="", edits=None, model_output=None):
    if policy not in MISMATCH_POLICIES:
        raise ValueError("Choose Warn and continue or Block downstream for override mismatches.")
    unique = {json.dumps(issue, sort_keys=True): issue for issue in issues}
    issues = list(unique.values())
    checked = bool(required_trait_phrases(settings))
    status = ("blocked" if policy == "Block downstream" else "warning") if issues else (
        "edited" if edits else "corrected" if checked and corrected else "ok" if checked else "unchecked")
    message = {
        "blocked": "Overrides not confirmed. Downstream processing is blocked; model output is available below.",
        "warning": "Overrides not confirmed. Continuing with the model output; selected traits may be missing or changed.",
        "corrected": "Appearance wording confirmed after an automatic correction.",
        "edited": "Prompt Mage applied the selected size phrase to the caption. This is a text edit, not model compliance or an image change.",
        "ok": "Selected appearance wording confirmed.",
        "unchecked": "Appearance wording checks are off or no traits were selected.",
    }[status]
    return {"status": status, "message": message, "issues": issues, "policy": policy,
            "attempts": attempts, "checked": checked, "has_appearance": bool(settings and settings.get("enabled")),
            "output": output,
            "post_edits": edits or [], "model_output": output if model_output is None else model_output,
            "next_step": ("Review the output below. Adjust the selected wording or try another instruction-capable model. "
                          "On override mismatch is on this assistant; Strict trait wording is on Appearance Overrides.") if issues else ""}


def reported_result(values, report):
    """Keep existing output indices, append status/report, optionally block only data outputs."""
    if report["status"] == "blocked":
        from comfy_execution.graph import ExecutionBlocker
        values = tuple(ExecutionBlocker(None) for _ in values)
    return tuple(values) + (report["status"], json.dumps(report, ensure_ascii=False, indent=2))
TRAITS = {
    "hair_color": ["Black", "Brown", "Blonde", "Red", "Auburn", "White", "Silver", "Grey", "Blue", "Pink", "Purple", "Green"],
    "hair_style": ["Straight", "Wavy", "Curly", "Bob", "Pixie cut", "Ponytail", "Twin tails", "Braid", "Bun", "Loose hair"],
    "eye_color": ["Brown", "Blue", "Green", "Hazel", "Grey", "Amber", "Violet", "Red"],
    "breast_size": ["Flat chest", "Small breasts", "Medium breasts", "Large breasts", "Very large breasts", "Massive breasts", "Gigantic breasts"],
    "hair_length": ["Bald", "Very short", "Short", "Shoulder length", "Long", "Very long"],
    "body_type": ["Slim", "Athletic", "Muscular", "Curvy", "Full figured"],
    "skin_tone": ["Fair", "Light", "Medium", "Tan", "Brown", "Dark"],
    "clothing": ["Casual clothes", "Dress", "Suit", "Shirt and jeans", "Swimwear", "Lingerie"],
    "expression": ["Neutral", "Smiling", "Serious", "Laughing", "Surprised", "Confident"],
    "butt_size": ["Small butt", "Medium butt", "Large butt", "Very large butt", "Massive butt", "Gigantic butt"],
}


def _words(text):
    return " ".join(re.findall(r"\w+", text.casefold().replace("_", " ")))


def required_trait_phrases(settings):
    if not settings or not settings.get("enabled") or not settings.get("strict_wording", True):
        return {}
    phrases = {}
    for key, value in settings.get("traits", {}).items():
        if key == "hair_color": value += " hair"
        elif key == "eye_color": value += " eyes"
        elif key == "skin_tone": value += " skin"
        elif key == "hair_length" and value != "Bald": value += " hair"
        elif key == "hair_style" and value in ("Straight", "Wavy", "Curly"): value += " hair"
        phrases[key] = value
    return phrases


def check_appearance_wording(text, settings, location="description"):
    """Check requested wording without inserting traits into unrelated objects."""
    phrases = required_trait_phrases(settings)
    if not phrases:
        return
    normalized = _words(text)
    # Equivalent skin nouns are fine; selected breast-size wording stays literal.
    comparable = normalized.replace("skin tone", "skin").replace("complexion", "skin")
    for original, equivalent in (("haired", "hair"), ("eyed", "eyes"), ("skinned", "skin"), ("tanned", "tan")):
        comparable = re.sub(r"\b" + original + r"\b", equivalent, comparable)
    missing = []
    for key, value in phrases.items():
        words = _words(value)
        pattern = re.escape(words)
        if key in ("hair_color", "hair_length", "eye_color") and " " in words:
            attribute, noun = words.rsplit(" ", 1)
            pattern = re.escape(attribute) + r"(?:\s+\w+){0,3}\s+" + re.escape(noun)
        if not re.search(r"\b" + pattern + r"\b", comparable): missing.append(value)
    size = phrases.get("breast_size")
    conflicts = []
    if re.match(r"\s*(?:I (?:cannot|can't|won't)|I'm sorry|I am sorry)", text, re.I):
        conflicts.append("model refusal instead of a caption")
    if size:
        size_words = _words(size)
        pattern = r"\b(?:(?:very|extremely|exceptionally|moderately)\s+)?(?:small|medium|large|huge|massive|gigantic|enormous|ample|full|flat)\s+(?:breasts?|bust|chest)\b"
        conflicts.extend(m.group() for m in re.finditer(pattern, normalized) if _words(m.group()) != size_words)
        if re.search(r"\b(?:no|not|without)\s+(?:\w+\s+){0,2}" + re.escape(size_words) + r"\b", normalized):
            conflicts.append("negated " + size)
    if missing or conflicts:
        details = []
        if missing: details.append("missing exact selected wording: " + ", ".join(missing))
        if conflicts: details.append("conflicting/weakened size wording: " + ", ".join(conflicts))
        message = ("Appearance override not followed in " + location + ": " + "; ".join(details) +
                   ". Keep the exact selected phrases; do not soften, negate or replace them with synonyms.")
        raise AppearanceMismatch([{"location": location, "missing": missing, "conflicts": conflicts, "message": message}])


def person_items(layout, settings):
    trigger = (settings or {}).get("trigger", "")
    return [(index, item) for index, item in enumerate(layout["items"]) if item.get("label") == "object" and (
        (trigger and trigger in item["caption"]) or re.search(
        r"\b(?:woman|man|person|girl|boy|character|traveler|female|male|individual)\b", " ".join(item["caption"].split()[:8]), re.I))]


def target_person_items(layout, settings):
    people = person_items(layout, settings)
    trigger = (settings or {}).get("trigger", "")
    return [(index, item) for index, item in people if (settings or {}).get("subject") == "All people" or
            len(people) == 1 or (trigger and trigger in item["caption"])]


def check_layout_appearance(layout, settings):
    issues = []
    try:
        check_appearance_wording(layout["summary"]["caption"], settings, "MOSS summary.caption")
    except AppearanceMismatch as error:
        issues.extend(error.issues)
    if not required_trait_phrases(settings): return
    for index, item in target_person_items(layout, settings):
        try:
            check_appearance_wording(item["caption"], settings, f"MOSS subject caption (items[{index}].caption)")
        except AppearanceMismatch as error:
            issues.extend(error.issues)
    if issues: raise AppearanceMismatch(issues)


def check_scene_appearance(scene, settings, target):
    issues = []
    fields = [(scene["description"], "description")]
    if target in ("DART tags", "Anima hybrid"): fields.append((", ".join(scene["tags"]), "tags"))
    for text, location in fields:
        try: check_appearance_wording(text, settings, location)
        except AppearanceMismatch as error: issues.extend(error.issues)
    if issues: raise AppearanceMismatch(issues)


def apply_trigger(scene, trigger):
    if not trigger:
        return scene
    scene = deepcopy(scene)
    scene["character"] = trigger
    if trigger not in scene["description"]:
        scene["description"] = trigger + ", " + scene["description"]
    draft = scene.get("layout_draft")
    if isinstance(draft, dict) and isinstance(draft.get("summary"), dict):
        caption = draft["summary"].get("caption")
        if isinstance(caption, str) and trigger not in caption:
            draft["summary"]["caption"] = trigger + ", " + caption
    return scene


def override_instructions(settings):
    if settings is None:
        return "", ""
    if not isinstance(settings, dict) or settings.get("version") != 1 or not isinstance(settings.get("enabled"), bool):
        raise ValueError("Connect appearance from Prompt Mage · Appearance Overrides.")
    if not settings["enabled"]:
        return "", ""
    traits = settings.get("traits")
    if not isinstance(traits, dict) or any((key not in TRAITS and key != 'gender') or not isinstance(value, str) for key, value in traits.items()):
        raise ValueError("Appearance overrides contain unsupported traits.")
    for field in ("subject", "trigger", "identity_mode", "custom"):
        if not isinstance(settings.get(field), str):
            raise ValueError("Appearance override fields must be text.")
    if not traits and not settings["trigger"] and not settings["custom"]:
        return "", ""
    wording = ("Use the exact selected trait wording, preserving its strength. In particular, 'Gigantic breasts' "
               "must remain 'gigantic breasts', not 'large bust', 'large breasts' or another weaker phrase. "
               "Include selected traits in the overall description and every caption describing the target person, "
               "not in captions for unrelated objects. Do not describe an original conflicting size as well. "
               if settings.get("strict_wording", True) else
               "Paraphrasing is allowed, but preserve the meaning and strength of the selected traits. ")
    if settings.get("strict_wording", True) and "breast_size" not in traits:
        wording = ("Use the exact selected trait wording, preserving its strength. Include selected traits in the "
                   "overall description and target-person captions, not unrelated objects. Do not introduce "
                   "unselected anatomy or identity changes. ")
    instructions = (
        "\nApply these requested appearance replacements to the selected subject, even in Preserve mode. "
        "Describe the changed version directly; omit conflicting original attributes instead of explaining the edits. "
        "Apply changes consistently to tags, prose, every JSON field and every layout caption. "
        "Keep pose, framing, background, lighting and unselected attributes unless another instruction changes them. "
        "For multiple people, change only the specified subject; do not transfer traits to other people. "
        "Use a nonempty trigger as the exact literal character reference, not a guessed name. "
        "If identity_mode is 'Trigger replaces identity details', omit unselected identity traits such as original "
        "hair, eyes and body attributes, retaining the trigger and explicitly selected replacements. "
        "Selected replacements take priority over conflicting input descriptions and writing instructions. "
        + wording +
        "Do not render these settings as visible writing in the image. Do not change the required output schema. "
        "These instructions modify generated text, not image pixels. Settings:\n"
        + json.dumps({**{key: settings[key] for key in ("subject", "trigger", "identity_mode", "traits", "custom")},
                      "required_phrases": required_trait_phrases(settings)}, ensure_ascii=False)
    )
    return instructions, settings["trigger"].strip()
