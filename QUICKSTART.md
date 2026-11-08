# Prompt Mage — Quickstart

## 1. Install once

Follow [README installation](README.md#install), restart ComfyUI and refresh your browser. Search **Prompt Mage · Archmage (Beta)**. Disable the original ComfyUI-Dart or legacy prompt-atelier distribution if also installed; these packs share node IDs. Read the [Registry migration guide](docs/REGISTRY_MIGRATION.md) before switching an existing installation.

## 2. Pick a model

**Full image workflow:** [download the main Archmage workflow](workflows/start-here/03-moss-full-workflow.json) and follow the [model downloads guide](docs/MODEL_DOWNLOADS.md). This is the supplied Zine DART Ideas graph with only its character LoRA removed; accelerator/custom sampling settings remain.

**Prefer the OpenAI API?** Select Assistant → OpenAI API in Archmage, paste a key into its masked panel and click Add key. It clears/collapses after adding and is saved in the ComfyUI user directory for reuse after restart. Terra and Sol are recommended; the model dropdown shows cost labels. [API guide](docs/OPENAI_API.md).

Connect CLIP from the same compatible Qwen loader used by MOSS, or leave Local model on Automatic. In the browser it reuses an unambiguous compatible downstream encoder; otherwise it chooses the smallest installed Qwen. With none installed, Archmage downloads a pinned official Qwen3.5 2B once. Reference images require vision weights. [Details](docs/ARCHMAGE_USABILITY.md#automatic-encoder-and-memory).

## 3. Write or connect your idea

- **Scene idea / WHAT:** enter `an adult explorer reading a map in a small workshop`, or leave blank for a seeded scene. **Writing rules / HOW:** add constraints such as `sharp focus throughout; no extra people`.
- Connect an image to prioritize a reference. Instructions and Appearance Overrides request changes to its generated description.
- Style is first. The default **Photo · Bright lifestyle** favors crisp detail and clean light. Choose another preset or add style notes. With a reference, Image treatment must be Apply selected style to restyle its caption.
- Add **Prompt Mage · Resolution** and connect its width/height to both Archmage and your latent. Without an image, Archmage uses connected/manual dimensions. With an image, choose processed-image size or Manual.

## 4. Choose and connect the output

Use **prompt** for your positive text encoder. Prose produces plain text; MOSS JSON layout produces validated native JSON. **description** stays prose for a separate tagger. **moss_json** is inactive in Prose mode. **width/height** can drive your latent. Without a reference the image output is inactive rather than a fake blank image.

New nodes default to Detailed, MOSS JSON layout, 4096 tokens and Thinking on, matching the working setup. For a faster first try choose Prose and turn Thinking off. If thinking runs out of tokens, try 8192. The token ceiling includes reasoning and the final answer per stage. Read the visible status if a final answer or layout is blocked.

## 5. Add a reusable character or image list

Connect **Appearance Overrides → appearance**. Gender defaults to Female on new nodes; choose Keep unchanged when describing an existing subject faithfully. Choose a trigger and only the traits you want replaced. Custom reveals a free-text option. These instructions edit text, not pixels.

For local/RunPod uploads, connect **Upload Images.image → Archmage.image** and **filename → source_name**. Wait for uploads, then use **Run all images from first** on the node. With Batch mode off, five images queue five complete workflow runs. With it on, one workflow processes the native list. No manual indexing is required. [Batch guide](docs/BATCH_RUNNER.md).

## Examples and deeper help

[Three starter workflows](workflows/start-here/README.md) · [Archmage controls](docs/ARCHMAGE_USABILITY.md) · [Model choices](docs/MODEL_CHOICES.md) · [Older examples](workflows/next/README.md)

Scene Composer, Text Assistant and Image to Text are deprecated but remain under Prompt Mage/Deprecated. Their IDs and sockets are retained. General Structured JSON captions and external chat-server features remain available in the legacy nodes; Archmage currently focuses on prose and native MOSS layouts.
