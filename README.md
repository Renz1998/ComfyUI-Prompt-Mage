![Prompt Mage — words, tags and images into your next scene](assets/banner.svg)

# Prompt Mage for ComfyUI

Turn a rough idea or reference image into a usable image prompt. **Archmage** combines scene writing, image descriptions, character appearance settings, 31 visual styles and native MOSS JSON layouts. Use local Qwen or the OpenAI API, with one shared canvas size for your prompt and image workflow.

[Quickstart](QUICKSTART.md) · [Workflows](workflows/start-here/README.md) · [Model downloads](docs/MODEL_DOWNLOADS.md) · [Archmage guide](docs/ARCHMAGE_USABILITY.md) · [Registry](https://registry.comfy.org/nodes/prompt-mage) · [Node screenshots](docs/NODE_GALLERY.md) · [Community](CONTRIBUTING.md) · [Support](SUPPORT.md) · [Credits](CREDITS.md)

## Start with Archmage

- **Write an idea**, or leave Concepts blank for a seeded scene.
- **Connect an image** to make it the primary reference. Add instructions for requested changes.
- **Connect DART tags** to `source_tags` for random scene inspiration. Character replacements and the selected style take priority; known conflicting traits are filtered before composition. [DART scene ideas →](docs/DART_SCENE_IDEAS.md)
- Choose **Prose** or **MOSS JSON layout**, with canvas/aspect-ratio context in either mode.
- Pick from **31 style templates**: amateur Instagram, phone snapshots, studio photography, sci-fi anime, manga, watercolor and more. Random and Custom are available too.
- Connect **Appearance Overrides** for a character trigger and selected traits. This edits the description, not the source image.
- Optionally enable **Thinking mode** with a compatible model. It can take longer; it does not guarantee better results.

**Archmage is beta.** Reports distinguish valid output, appearance warnings, unsupported/unconfirmed thinking and blocked layouts. Inspect important results before using them downstream.

![Archmage with a shared Appearance Overrides recipe](assets/screenshots/archmage-appearance.jpg)

*Current Archmage layout with a reusable appearance recipe and the collapsed OpenAI key panel. Neutral demo settings; [see individual node screenshots](docs/NODE_GALLERY.md).*

## Install

Use one installation of this pack. It replaces the original ComfyUI-Dart and retains legacy node IDs; do not install both together.

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Renz1998/ComfyUI-Prompt-Mage.git prompt-mage
# Use the Python environment that runs ComfyUI:
python -m pip install -r prompt-mage/requirements.txt
```

Restart ComfyUI, refresh the browser, then search **Prompt Mage** or **Archmage**.

**Comfy Registry:** the new package ID and display name are **prompt-mage / Prompt Mage**. After Registry approval, the install command is `comfy node install prompt-mage`. This replaces the legacy `prompt-atelier` distribution; **do not install both** because they register the same node IDs. Existing users should follow the [migration guide](docs/REGISTRY_MIGRATION.md). A successful upload is not the same as Registry review approval or Manager discovery; see [current publishing status](PUBLISHING.md).

## Pick the right tool

**[Chat → Apply → Generate](docs/SPELL_SCROLL.md):** Grimoire handles conversation. Click **Use this prompt** on a chosen reply; **Spell Scroll** reads that approved snapshot for image generation. Further chat never silently changes it, and normal workflow runs never call the assistant.

**[Grimoire (Beta)](docs/GRIMOIRE.md)** is a separate persistent conversation node with conversational chat, a live style dropdown, system/task instructions, pinned facts, Appearance Overrides, drag-and-drop file attachments, multiple image inputs, Markdown, message editing, Archmage styles, a warmer default voice and validated MOSS prompt cards. [Grimoire → MOSS sample](workflows/start-here/08-grimoire-to-moss.json).

**[Tag Filters](docs/TAG_FILTERS.md):** reusable Full color, No text/watermarks and Photography presets, custom bans/removals and protected tags. Share one recipe between DART Generate and Archmage.

| Node | Use it for |
| --- | --- |
| **Archmage (Beta)** | Text/reference → prose or native MOSS layout JSON; the recommended starting point |
| **Resolution** | Select aspect ratio and total megapixels once; send matching width/height to Archmage and your latent |
| **Upload Images** | Local file picker, folder picker and drag-and-drop, including when ComfyUI runs on RunPod |
| **Appearance Overrides** | Reusable gender, character trigger, appearance dropdowns and custom replacements |
| **Tag Composer (Experimental)** | Separate vocabulary-backed Danbooru conversion; review coverage and semantic warnings |
| **DART v3 tools** | DART v3 tag expansion, shared generation/config/decode utilities and creative ideas for Archmage |
| **Server Folder (Advanced)** | Read image folders on the computer running ComfyUI |

**Deprecated:** Scene Composer, Text Assistant and Image to Text remain executable for older workflows. Use Archmage for new scene/prose/MOSS workflows. External chat servers, DART/Anima formatting and general Structured JSON captions remain documented in [legacy controls](docs/LEGACY_ASSISTANTS.md). Deprecated does not mean removed, and there is no automatic graph conversion.

## Start with the main Archmage workflow

**[Download the main workflow JSON](https://raw.githubusercontent.com/Renz1998/ComfyUI-Prompt-Mage/main/workflows/start-here/03-moss-full-workflow.json)** · [Model downloads and folders](docs/MODEL_DOWNLOADS.md)

The supplied **Moss_Image_Zine_2 - DART Ideas** workflow, with **only the Zine character LoRA removed**. Its accelerator LoRA, custom sampling, SLG, 3.7 MP resolution, appearance recipe and Archmage settings are retained. The saved assistant uses **Local Qwen**, sharing MOSS's encoder. No API key is needed. On-canvas notes explain setup, models and controls. Install the required nodes/models and select your installed filenames. [Workflow requirements](docs/MODEL_DOWNLOADS.md).

| Goal | Open |
| --- | --- |
| Write a character scene | [01 · Write a scene](workflows/start-here/01-write-a-scene.json) |
| Describe uploaded photos | [02 · Describe uploaded images](workflows/start-here/02-describe-uploaded-images.json) |
| **Main: DART ideas → Archmage → MOSS** | [03 · Main Archmage workflow](workflows/start-here/03-moss-full-workflow.json) |

[Simple setup and prose/JSON comparison →](workflows/start-here/README.md) · [Older / specialized workflows](workflows/next/README.md)

Already using DART? Try [DART Generate → Appearance Overrides → Archmage](workflows/start-here/06-dart-ideas-to-archmage.json) to turn random tags into a coherent scene for your character.

**DART v3 is the only new-workflow entry point.** The multi-version loader, v1/v2 composers and v2 aspect helper are deprecated; saved workflows retain their original behavior. Shared DART generation and tag tools stay available. [Models and compatibility →](docs/MODEL_DOWNLOADS.md)

## Upload from your computer, even on RunPod

Click the drop area, drop files onto the node, or choose a local folder. Files upload to the ComfyUI server. Connect **image → Archmage.image** and **filename → source_name**; the drag-create shortcut wires both. Wait for uploads, then click **Run all images from first** on Upload Images.

**Batch mode off:** five images queue five complete workflow runs, starting from the first. **Batch mode on:** one workflow receives all five through native list handling. Manual indices and limits do not affect this button. The global Run button retains its manual behavior. [Batch runner guide →](docs/BATCH_RUNNER.md)

<img src="assets/screenshots/upload-images.jpg" alt="Prompt Mage Upload Images node with local file and folder buttons" width="510">

Workflow files store server-relative image paths. Upload again when moving to another server. Removing a file from the list does not delete it from the server.

## Models and practical limits

**DeepSeek API:** select it in Archmage's Assistant dropdown and add a key through its masked session panel. **Flash** is the current recommended text/image option; **V4 Pro** is text-only here. Thinking, appearance recipes, DART filters and MOSS JSON remain available. [Setup, models, billing and limitations](docs/DEEPSEEK_API.md).

**OpenAI API:** switch Archmage's Assistant dropdown, paste a key into the masked panel and click **Add key**. The field clears and hides after adding; the key is saved separately in the ComfyUI user directory, outside workflows. **GPT-6.1 Terra** and **GPT-6.1 Sol** are recommended options, Luna is the budget choice, and Astra carries a **HIGH COST** label. The dropdown shows per-million-token pricing. [API setup, billing and privacy →](docs/OPENAI_API.md)

- Install a **full generation-capable Qwen encoder** in `models/text_encoders`, or connect a compatible CLIP loader. Image inputs require vision weights. Archmage Automatic reuses a compatible downstream encoder when unambiguous, otherwise chooses a small installed Qwen. With none installed, it downloads a pinned official Qwen3.5 2B fallback once; other nodes do not auto-download.
- Local checks used Qwen3-VL 4B and Qwen3.5 9B. Native thinking was detected with Qwen3.5 9B; the tested Qwen3-VL 4B did not return a separate thinking segment. Try 8192 tokens for thinking, up to 16384 for complex requests.
- Templates are text instructions, not LoRAs. Use **Reference style → Apply selected style** to restyle a reference caption; the default preserves its style.
- MOSS JSON is validated and converted to native centered-pixel coordinates. Connect width/height to your latent to match the actual image size. Valid boxes do not guarantee precise diffusion placement.
- These nodes produce **text and conditioning inputs**, not finished images. Appearance instructions do not edit pixels or load character LoRAs. Vocabulary membership does not prove a tag accurately describes the scene.

[Model choices](docs/MODEL_CHOICES.md) · [Archmage controls](docs/ARCHMAGE_BETA.md) · [DART and legacy setup](docs/DART_AND_LEGACY_SETUP.md)

Hover controls and sockets for help. Ember adds animated flames while running; Studio offers a quieter theme. Both respect reduced-motion settings. Right-click for theme/design options.

## Help build Prompt Mage

Got a workflow that works well? Found a confusing control? **[Share it with the community](https://github.com/Renz1998/ComfyUI-Prompt-Mage/issues/new/choose)**. Testers, workflow creators, developers and documentation improvements are welcome. Include models and settings so others can reproduce your results. [Ways to contribute](CONTRIBUTING.md).

If the pack is useful, consider starring the repo or supporting development:

**[☕ Ko-fi](https://ko-fi.com/renzuwu)** · **[PayPal](https://paypal.me/luckyrenz1998)** · [Support details](SUPPORT.md)

**USDT · TRON / TRC20** — use the code block's copy button:

```text
TUggk9S4aDDyT7HxrEjqCDxFPXgEr4okW8
```

Support is optional and goes to the Prompt Mage maintainer. Check the TRON network before sending.

## Built on the original creators’ work

Original node foundation: **[nkchocoai and contributors](https://github.com/nkchocoai/ComfyUI-Dart)**. DART models: **[p1atdev](https://huggingface.co/p1atdev)**. Language/vision models: **Qwen team and checkpoint authors**. MOSS format/model: **OpenMOSS**. Runtime/frontend: **ComfyUI contributors**.

[Full credits and model links](CREDITS.md) · [GPL-3.0 license](LICENSE) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)
