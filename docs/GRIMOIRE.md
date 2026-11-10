# Grimoire (Beta)

**1.18 redesign:** Grimoire handles conversation only. Explicitly apply a selected reply to Spell Scroll; normal image workflow runs read that separate snapshot. [Setup and migration](SPELL_SCROLL.md).

**Interface (1.17):** Chat shows messenger-style bubbles and a fixed composer. **Instructions** holds System prompt, Task instructions and Pinned facts. **Settings → Assistant provider** selects Local Qwen, OpenAI or DeepSeek; selecting an API provider reveals its key input directly below. If a key is already saved, click Add / replace key. The compact header combines the chat picker, New chat and Settings; hover Settings to see the provider. Secondary tools are in More actions, and compacted memory is tucked into Conversation memory only when present. Native widget fields remain serialized for workflow compatibility but are hidden from the interface.

**RunPod/HTTP fix (1.15.1):** chapter creation now works without HTTPS-only `crypto.randomUUID`. History is shown in the conversation panel; **Refresh history** reloads the selected chapter. Update the server, restart ComfyUI when idle, and hard-refresh the browser to load the new UI.

**Saved API keys:** keys added through either API panel now persist in `ComfyUI user directory/prompt_mage/credentials/openai.json` or `deepseek.json`. These are plaintext secrets with restricted file permissions; protect server/volume access. Keep the user directory on persistent RunPod storage to retain keys and conversation history between pod launches. Replacing a key overwrites only its provider's file; Remove saved key deletes only that file and clears its runtime credential. Environment keys are externally managed and can still apply after removing a saved key. No key values are returned to the UI or included in workflows/history.

Grimoire is a separate conversation node, not an Archmage replacement. [Complete Grimoire → MOSS workflow](../workflows/start-here/08-grimoire-to-moss.json) retains the main example's sampling, SLG, accelerator, appearance recipe and shared local Qwen. DART and Archmage are removed. The on-canvas guide includes setup and download links.

## Conversational chat with live style (1.19.1)

Grimoire stays conversational. The **Style / theme** dropdown sits in a compact toolbar above the messages; changing it makes no request and spends no API credits. The next message includes that selection and any custom style notes. A changed selection is explicitly identified in the next model request, so old conversation styles do not silently take precedence.

Ask questions, discuss ideas, then say “write the prompt,” “revise it in this style,” or “next scene” when ready. Grimoire is instructed to use the selected style for prompt creation/revision while keeping ordinary discussion in Markdown. Changing the dropdown alone does not rewrite a reply or the applied Spell Scroll snapshot.

**Settings → Prompt format** controls the format when a prompt is requested. Choose **MOSS JSON layout** for native MOSS, **Natural language / Markdown** for prose, or generic JSON with your own task schema. Custom style notes remain in Settings. The old mode widget is retained internally for workflow compatibility; the chat UI uses Conversation.

MOSS mode follows the official **editable draft → compile → model prompt** process. The assistant plans ordinary top-left `xyxy` pixel boxes using the connected width/height; Prompt Mage validates and converts these to native centered `yxyx` coordinates. The final image prompt contains only `summary`, `items`, `bbox_coord_space: "abs_centralized"` and `bbox_format: "yxyx"`, with no draft dimensions, code fences or assistant commentary. Existing native MOSS replies are accepted too. See the [official MOSS guide](https://github.com/OpenMOSS/MOSS-Image/blob/main/USERGUIDE.md#layout-prompts-experimental) and [Pixel Layout reference](https://github.com/OpenMOSS/MOSS-Image/blob/main/skills/moss-image-prompt-enhancer/references/layout.md). This pack supports a single continuous canvas with object/text items.

**MOSS prompt cards (1.21):** one structurally valid JSON prompt in a reply becomes a readable, wrapped code block. **Copy prompt** copies the compiled JSON only; **Use this prompt** explicitly applies it to Spell Scroll. Formatting is handled by the application, so the assistant need not argue about raw JSON versus code fences. Ordinary chat does not get an Apply button while MOSS is selected. Two distinct layouts in one reply are blocked instead of guessing; edit to keep one. Invalid/truncated/out-of-bounds layouts stay visible with an explanation. No extra model call is made to extract or compile a reply. Legacy mixed JSON/prose replies are rechecked when history loads and when applied, so a recoverable formatting error does not require regeneration.

**Reference roles:** image context uses actual socket names (including gaps), current attachment names, and a fresh payload-order map. Current attachments precede older reused images; the assistant is told to follow the roles you specify instead of merging identities or copying every reference attribute.

**Personality:** the default Grimoire voice is warm, curious, candid and lightly playful, with restrained fantasy flavor. Personality belongs in conversation; image captions stay concrete and free of assistant chatter. Empty/old factory system prompts upgrade automatically on the next turn; custom system prompts are preserved. Formatting-only requests are instructed to preserve the scene and geometry. Structural validation does not prove image quality or semantic correctness.

**Message actions:** Copy and Edit appear below both kinds of messages, Resend below yours, and Retry below assistant replies. Sending an edited user message or retrying requests a new reply; later messages are replaced only after success. Editing an assistant reply saves your text without calling the model, validates its selected format, and removes later messages. Earlier-message edits warn first. These actions do not modify the applied Spell Scroll snapshot.

Bare JSON is displayed as a formatted code block with Copy code. Safe Markdown includes headings, emphasis, lists, blockquotes, tables, links and fenced code. Raw HTML and remote images remain disabled. Resized dimensions and named settings are saved in workflow JSON; embedded key panels no longer reset the node height.

**Model retention:** chat retains the full workflow cache and uses ComfyUI partial execution to run only Grimoire’s chat target and required inputs. API chats skip the optional local CLIP dependency. Both updated Prompt Mage backend and ComfyUI partial-execution support are required; unsupported servers fail before queuing. Keep Unload local assistant after generation off to retain that encoder. Native memory pressure, cache eviction, explicit server unload options, or another workflow can still offload models. This does not guarantee residency when a local LLM shares VRAM with diffusion models.

**Compact interface (1.19.2):** open **Applied prompt** beside Style to inspect the Spell Scroll destination and saved prompt. It starts collapsed. Style help and keyboard shortcuts are hover tips; idle message counts are hidden, while working/error feedback remains visible. The shorter composer and combined header leave more room for messages at the same node size.

**Applied-prompt glow (1.22):** the response currently applied to the selected Spell Scroll has a gold border, amethyst glow, **Applied** badge and pressed Applied button. It follows the saved snapshot rather than the newest message. Stable message identities keep the marker on its source when conversation compaction shifts message positions. Editing/regenerating that reply does not mark a different version as applied; a snapshot from another chat is shown only in Applied prompt until its source chat is open. The glow restores when history loads. A failed state lookup clears the visual marker rather than guessing. Changes made elsewhere become visible on the next history/chat refresh.

The fantasy spellbook theme uses only local CSS and system fonts. Text and JSON remain readable, ornamentation does not intercept clicks, and the compact controls preserve chat space. Reduced-motion preferences disable the slow glow animation while retaining the border and label.

## Instructions and memory

- **System prompt:** role and general rules; sent verbatim every turn.
- **Task instructions:** current project, sequence, output schema and constraints; also never compacted.
- **Pinned facts:** manually chosen durable facts. No silent automatic fact collection.
- **Appearance Overrides:** optional input, included every turn separately from summaries. Changes descriptions, not image pixels. Grimoire does not claim Archmage's exact trait enforcement.
- **Conversation history:** persists as plaintext JSON in `ComfyUI user directory/prompt_mage/grimoire/<conversation_id>.json`. This is outside workflow files. Protect server access and backups. It is server-wide, not isolated per browser user.
- **Automatic compaction:** above 24,000 characters or 12 messages, summarizes older turns and retains the last six messages verbatim. The visible summary is lossy. System/task/pinned fields and current appearance remain separate.
- **Edit summary:** copies the summary into Summary override; edit it there and run. Clear the override afterward so it does not keep replacing newer summaries.

## Conversation controls

**Send** uses the chat composer (Enter sends; Shift+Enter inserts a newline). Only the isolated chat executor and its required inputs run. Image samplers are excluded. Click **Use this prompt** on a chosen assistant reply to save a separate Spell Scroll snapshot. **Run ComfyUI** uses Spell Scroll, not the latest chat message. Opening chats or discussing more ideas never replaces the applied prompt.

**New chat** starts a separate history. **Saved chats** reopens up to 500 most recently updated server conversations, restoring messages, summary and saved system/task/pinned/model settings. Empty new chats appear in the picker after their first successful turn. Cloning/importing the same chapter ID shares its conversation. Appearance and image graph connections remain live and are not rewired by chat switching.

Messages support safe Markdown: headings, lists, bold/italic, HTTPS/HTTP links and fenced code blocks with Copy code. Raw HTML and remote image embeds are not executed or loaded. Use the Instructions and Settings tabs for separate prompts and provider choices.

**Next step** requests a continuation; it is model-guided, not a guaranteed script index. **Regenerate** replaces the most recent answer without adding another user message. Failed calls leave the saved conversation unchanged. Successful history writes are atomic.

**Compact now** and **Clear conversation** block the primary output to avoid generating an image during maintenance. Clear removes stored turns and summary; configured instructions/pinned facts remain. **New chapter** changes the ID and starts a separate history. Old chapters remain on disk. This interface does not permanently delete chapter files. Copying a workflow with the same ID shares its history; choose New chapter to separate them.

**Copy latest** copies the answer. `latest_response` always retains the complete answer; `output` can select the response, valid JSON, a dot-separated JSON field, or validated MOSS JSON. Use **Spell Scroll.prompt** for downstream generation; legacy Grimoire data outputs are only for explicit chat jobs. Width/height should share the latent's Resolution source. MOSS validation checks schema/boxes, not scene quality.

**Thinking shortcut (1.22.1):** the Thinking toggle beside Send controls the same setting as Settings → Thinking. Its On/pressed state is visible, it is saved with workflow settings, and changing it does not send a request. It applies to the next reply. Model support varies; thinking can take longer and consumes the generation token budget. If a model exhausts that budget without a final answer, raise the token limit or turn Thinking off.

## Models and images

Local Qwen is the default. Connect a full generation-capable CLIP or choose an installed model. Without a compatible model, Automatic can download the pinned small assistant fallback. OpenAI and DeepSeek use the same separate masked provider-key panels as Archmage. Provider charges/policies apply. Summary and image-caption stages add calls; cancellation cannot undo billing.

### Attachments and multiple image inputs (1.20)

Click **Attach**, drop files onto the chat, or paste an image from the clipboard. Pending files appear above the message box with image thumbnails and Remove buttons. Uploading does not call the model. **Send** includes those references with your message; an attachment-only Send asks the assistant to review the files. Saved messages show their attachment names; expand one to preview it or choose **Attach again**. Failed chat executions restore the queued draft and attachments for retry.

Supported files: PNG/JPEG/WebP/GIF/BMP/TIFF (first frame), UTF-8/UTF-16 text/code, Markdown, JSON, CSV/TSV, YAML/TOML/XML, DOCX text and text-based PDF. Each message accepts up to **six files**, **16 MB each**. Document references use at most **24,000 characters per file**, **16 PDF pages**, and **64,000 characters total**; limited files are visibly marked **excerpt**. PDF diagrams, scanned pages, DOCX formatting and embedded pictures are not extracted as images: attach screenshots/page images for those. Files are treated as reference data, not executable instructions.

The native **image** socket also supports multiple connections through separate inputs: connecting it reveals **image_2** directly below it, continuing up to **image_6**. Connected sockets and existing appearance/resolution links are preserved. Each input uses the first image of its batch. There is a combined limit of **six current images** across sockets and attachments; this is separate from the file-count limit. Dropping attachments needs no extra Load Image node.

**Vision APIs:** current images go directly into one answer request, without an additional caption call per attachment. Up to two recent saved image attachments from the last six retained conversation turns can be included again on follow-up messages, within the six-image budget. Repeated images use provider input tokens. OpenAI multi-image payloads follow the [official image-input documentation](https://developers.openai.com/api/docs/guides/images-vision?api-mode=responses). DeepSeek Pro remains text-only in this integration; use Flash for images. Local Qwen captions each current image separately, then uses those descriptions for the answer.

**Storage:** image references are normalized to server-side PNGs (maximum 1536 pixels per edge), then prepared at a 0.8 MP vision budget. Documents are saved as extracted text; their original binary files are not retained. References live under `ComfyUI user directory/prompt_mage/grimoire_attachments/`; conversation files hold IDs and readable context. Draft attachments are excluded from workflow JSON. Remove clears a draft selection; it does not delete saved server files. Keep the user directory on persistent RunPod storage to retain attachment history. When using an API, sending a message shares its reference text/images with that provider, including recent images described above.

## Practical limits

This is a first beta: there is no vector search, automatic cross-chat memory, per-user authentication or guaranteed sequence counter. Conversation exports do not travel with workflow JSON. Each editable field is bounded at 32,768 characters and each history file at 2 MB. Large pinned/task fields can still exhaust a small model's context. Use a trusted server and inspect outputs before downstream use.

Validation includes a live neutral two-turn DeepSeek Flash conversation with saved-context recall, mocked compaction/regeneration/error recovery tests, image-caption persistence and MOSS boundary validation. A complete diffusion render is not a prompt-quality benchmark and has not been run for this sample.
