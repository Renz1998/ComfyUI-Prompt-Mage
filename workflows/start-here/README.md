# Start here

Testing the new script-to-image bench? Use the separate [Foundry experimental workflow](../experimental/README.md). It waits for your approval after each actual-image review.

Drag one JSON file into ComfyUI. **Start with 03 for the full DART v3 → Archmage → MOSS workflow.** 01 and 02 make prompts. [Download model files first](../../docs/MODEL_DOWNLOADS.md).

| I want to… | Open | What to connect / change |
| --- | --- | --- |
| Conversation → image sequence | [08 · Grimoire → MOSS](08-grimoire-to-moss.json) | Main sampling pipeline with Grimoire instead of DART/Archmage. Local Qwen, appearance recipe, persistent conversation and 4:5 canvas. See the on-canvas setup note. |
| Write a scene for a character | [01 · Write a scene](01-write-a-scene.json) | Optional appearance settings → Archmage. Send **prompt** to your positive text encoder. |
| Describe my photos | [02 · Describe uploaded images](02-describe-uploaded-images.json) | Drop photos on Upload Images. Use **Run all images from first**; batch off runs the whole connected workflow per image. |
| **Main Archmage workflow** | [03 · DART v3 → Archmage → MOSS](03-moss-full-workflow.json) | Exact supplied Zine DART Ideas graph, minus the character LoRA. Accelerator LoRA and custom sampling/SLG remain. See the model guide for requirements. |
| Use random DART ideas with my character | [06 · DART ideas → Archmage](06-dart-ideas-to-archmage.json) | DART tags feed source_tags; Appearance Overrides and the selected style define the character/treatment. This example makes prompts, not images. |

In Archmage, **Scene idea = WHAT** (a mage in a red cloak taking a hotel mirror selfie). **Writing rules = HOW** (fully clothed, sharp focus throughout, no extra people). Either field can be empty. Style supplies the visual treatment; Bright lifestyle is the new default.

**Resolution** sends the same width/height to Archmage and the empty latent. Change its megapixels or aspect ratio once. It creates no latent itself, so you can use it with other generation models.

The main workflow retains the supplied Zine settings, including its accelerator LoRA, manual sigma schedule, SLG, 3.7 MP resolution. Archmage defaults to Local Qwen with the shared MOSS encoder; on-canvas notes include setup, downloads and controls. Only the character LoRA is removed. No API key is required. Download the linked models and select their filenames; update ComfyUI if native sampling/SLG nodes are missing. It is not the 50-step base-model starter. [Requirements](../../docs/MODEL_DOWNLOADS.md).

## Compare prose and JSON fairly

Use [04 · Prose](04-compare-prose.json), then [05 · JSON](05-compare-json.json), with the **same model files**. Both use fixed scene/image seeds and identical generation settings. Only the Archmage output format changes. Its **description** output is the prose used to construct JSON; **moss_json** adds spatial boxes while retaining the full description in `summary.caption`.

JSON layout is experimental and can render worse than prose. Longer JSON does not imply sharper images. Keep whichever format works best with your checkpoint. A beach photo and an indoor mirror selfie also differ in light, framing and material detail, so that comparison alone cannot isolate format quality.

[Older / specialized examples](../next/README.md) · [Archmage controls](../../docs/ARCHMAGE_BETA.md)
