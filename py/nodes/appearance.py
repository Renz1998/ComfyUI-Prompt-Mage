from .base import BaseNode
from ..dart.appearance import TRAITS, KEEP, override_instructions


class DanbooruTagsTransformerAppearanceOverrides(BaseNode):
    CATEGORY = "Prompt Mage/Assistants"

    @classmethod
    def INPUT_TYPES(cls):
        fields = {
            "enabled": ("BOOLEAN", {"default": True, "tooltip": "Turn all appearance replacements on/off without removing connections."}),
            "subject": (["Main subject", "All people", "Custom subject"], {"default": "Main subject", "tooltip": "Choose who receives the replacements. Custom subject can identify the person on the left or another subject without naming a real person."}),
            "subject_custom": ("STRING", {"default": "", "tooltip": "Custom subject selector, for example: the adult person on the left. Used only with Custom subject."}),
            "trigger": ("STRING", {"default": "", "tooltip": "Optional exact training/character trigger. Overrides the Image to Text character trigger when provided. Does not load a LoRA."}),
            "identity_mode": (["Keep other appearance details", "Trigger replaces identity details"], {"tooltip": "Keep unselected traits, or use the trigger instead of describing unselected identity traits. The second option needs a trigger; selected replacements still appear."}),
        }
        for name, choices in TRAITS.items():
            if name == "butt_size": continue  # Appended below for saved-widget compatibility.
            fields[name] = ([KEEP] + choices + ["Custom"], {"default": KEEP, "tooltip": f"Replace {name.replace('_', ' ')} for the selected subject. Keep unchanged makes no request. Custom reveals a free-text value."})
            fields[name + "_custom"] = ("STRING", {"default": "", "tooltip": f"Your own {name.replace('_', ' ')} value. Used only when its dropdown is Custom."})
        fields["custom_overrides"] = ("STRING", {"default": "", "multiline": True, "tooltip": "Extra appearance replacements, accessories, makeup, clothing or other directions. Selected dropdown traits win if they conflict. Existing assistant writing instructions remain available."})
        fields["strict_wording"] = ("BOOLEAN", {"default": True, "tooltip": "Check selected trait phrases and request a correction when missing or weakened. The assistant's On override mismatch setting controls whether a persistent mismatch warns or blocks downstream. Disable to allow paraphrasing. Wording checks do not verify visual/semantic accuracy or free-form extra instructions."})
        fields["apply_size_wording"] = ("BOOLEAN", {"default": True, "tooltip": "Explicit caption edit: apply your selected breast-size phrase after generation for an identifiable target, replacing weaker size phrases or adding the selected attribute. Reported as an Atelier text edit, not model compliance. Does not alter source images, model policies or unrelated object captions. Ambiguous subjects remain unconfirmed."})
        # Append to preserve positional settings in existing saved workflows.
        fields["gender"] = (["Female", "Male", "Nonbinary", KEEP, "Custom"], {"default": "Female", "tooltip": "Requested gender of the selected adult subject. Keep unchanged preserves the reference. Does not imply clothing, anatomy or pose."})
        fields["gender_custom"] = ("STRING", {"default": "", "tooltip": "Your gender wording when Gender is Custom."})
        fields["butt_size"] = ([KEEP] + TRAITS["butt_size"] + ["Custom"], {"default": KEEP, "tooltip": "Requested butt size for the selected adult subject. Keep unchanged preserves existing appearance; Custom accepts your wording."})
        fields["butt_size_custom"] = ("STRING", {"default": "", "tooltip": "Your own butt-size wording when Custom is selected."})
        return {"required": fields}

    RETURN_TYPES = ("ATELIER_APPEARANCE", "STRING")
    RETURN_NAMES = ("appearance", "instructions")
    FUNCTION = "build"
    OUTPUT_NODE = True

    def build(self, enabled=True, subject="Main subject", subject_custom="", trigger="",
              identity_mode="Keep other appearance details", custom_overrides="", strict_wording=True, apply_size_wording=True, **values):
        if subject not in ("Main subject", "All people", "Custom subject"):
            raise ValueError("Choose a supported subject selector.")
        if identity_mode not in ("Keep other appearance details", "Trigger replaces identity details"):
            raise ValueError("Choose a supported identity mode.")
        if enabled and subject == "Custom subject" and not subject_custom.strip():
            raise ValueError("Enter a custom subject, or choose Main subject.")
        if enabled and identity_mode == "Trigger replaces identity details" and not trigger.strip():
            raise ValueError("Enter a trigger for Trigger replaces identity details.")
        traits = {}
        gender = values.get('gender', KEEP)
        if gender not in ('Female', 'Male', 'Nonbinary', KEEP, 'Custom'):
            raise ValueError('Choose a supported gender.')
        if gender == 'Custom':
            gender = values.get('gender_custom', '').strip()
            if enabled and not gender:
                raise ValueError('Enter a custom gender value.')
        if gender != KEEP and gender:
            traits['gender'] = {'Female': 'woman', 'Male': 'man', 'Nonbinary': 'nonbinary adult'}.get(gender, gender)
        for name, choices in TRAITS.items():
            choice = values.get(name, KEEP)
            if choice not in [KEEP] + choices + ["Custom"]:
                raise ValueError(f"Choose a supported {name.replace('_', ' ')} option.")
            value = values.get(name + "_custom", "").strip() if choice == "Custom" else choice
            if enabled and choice == "Custom" and not value:
                raise ValueError(f"Enter a custom {name.replace('_', ' ')} value.")
            if choice != KEEP and value:
                traits[name] = value
        settings = {"version": 1, "enabled": enabled, "subject": subject_custom.strip() if subject == "Custom subject" else subject,
                    "trigger": trigger.strip(), "identity_mode": identity_mode, "traits": traits, "custom": custom_overrides.strip(), "strict_wording": strict_wording, "apply_size_wording": apply_size_wording}
        instructions, _ = override_instructions(settings)
        return {"ui": {"text": [instructions or "No appearance replacements requested."]}, "result": (settings, instructions)}
