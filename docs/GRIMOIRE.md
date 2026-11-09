# Grimoire (Beta)

**1.18 redesign:** Grimoire handles conversation only. Explicitly apply a selected reply to Spell Scroll; normal image workflow runs read that separate snapshot. [Setup and migration](SPELL_SCROLL.md).

**Interface (1.17):** Chat shows messenger-style bubbles and a fixed composer. **Instructions** holds System prompt, Task instructions and Pinned facts. **Settings → Assistant provider** selects Local Qwen, OpenAI or DeepSeek; selecting an API provider reveals its key input directly below. If a key is already saved, click Add / replace key. The header provider button is a shortcut to Settings. Secondary tools are in More actions, and compacted memory is tucked into Conversation memory only when present. Native widget fields remain serialized for workflow compatibility but are hidden from the interface.

**RunPod/HTTP fix (1.15.1):** chapter creation now works without HTTPS-only `crypto.randomUUID`. History is shown in the conversation panel; **Refresh history** reloads the selected chapter. Update the server, restart ComfyUI when idle, and hard-refresh the browser to load the new UI.

**Saved API keys:** keys added through either API panel now persist in `ComfyUI user directory/prompt_mage/credentials/openai.json` or `deepseek.json`. These are plaintext secrets with restricted file permissions; protect server/volume access. Keep the user directory on persistent RunPod storage to retain keys and conversation history between pod launches. Replacing a key overwrites only its provider's file; Remove saved key deletes only that file and clears its runtime credential. Environment keys are externally managed and can still apply after removing a saved key. No key values are returned to the UI or included in workflows/history.

Grimoire is a separate conversation node, not an Archmage replacement. [Complete Grimoire → MOSS workflow](../workflows/start-here/08-grimoire-to-moss.json) retains the main example's sampling, SLG, accelerator, appearance recipe and shared local Qwen. DART and Archmage are removed. The on-canvas guide includes setup and download links.

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

## Models and images

Local Qwen is the default. Connect a full generation-capable CLIP or choose an installed model. Without a compatible model, Automatic can download the pinned small assistant fallback. OpenAI and DeepSeek use the same separate masked provider-key panels as Archmage. Provider charges/policies apply. Summary and image-caption stages add calls; cancellation cannot undo billing.

Connect image for outfit, prop or composition references. Only the first image in a batch is used in this beta. Images are resized to a 0.8 MP budget and captioned; that caption is stored as text context. For API vision, the current image is also supplied directly to the answer stage. Pixel data is not persisted, so reattach it for exact later inspection. DeepSeek Pro is text-only; use Flash for images.

## Practical limits

This is a first beta: there is no vector search, automatic cross-chat memory, per-user authentication or guaranteed sequence counter. Conversation exports do not travel with workflow JSON. Each editable field is bounded at 32,768 characters and each history file at 2 MB. Large pinned/task fields can still exhaust a small model's context. Use a trusted server and inspect outputs before downstream use.

Validation includes a live neutral two-turn DeepSeek Flash conversation with saved-context recall, mocked compaction/regeneration/error recovery tests, image-caption persistence and MOSS boundary validation. A complete diffusion render is not a prompt-quality benchmark and has not been run for this sample.
