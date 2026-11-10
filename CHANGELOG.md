# Changelog

## 1.27.0 — Grimoire production briefs

- Adds a production_brief connection and explicit Send brief → Foundry action. A queued compiler extracts the latest agreed direction into an immutable snapshot without adding a chat turn or rendering images.
- Imports creative direction, style, frame count, references and canvas choices into a new Foundry draft. Appearance transfers as a fallback; connected overrides take precedence. Models, keys, scoring and spending caps remain under Foundry control.
- Protects active runs and stale conversations, retains earlier snapshots, and removes live chat dependencies from generation jobs. Includes a separate MOSS example and setup guide.

## 1.26.1 — Plan revisions and visible review progress

- Keeps Preview plan in both the header and persistent bottom toolbar. Both are disabled once a plan is ready and throughout execution. Explicit Edit brief enables a new preview; Regenerate plan creates a new saved version before approval.
- Keeps approval, regeneration and brief editing beside each other at the bottom. Adds a captured planning-settings overview with model, style, canvas, score, limits, mode and reference count.
- Broadcasts the saved-image review stage before calling the API, so waiting on a vision review no longer looks like a stuck renderer.

## 1.26.0 — Passing scores, uninterrupted sequences and provider choice

- Adds an adjustable overall passing score (recommended 80): 40% prompt match, 25% usability, 35% physical inspection. The first passing try advances immediately; major visible defects and must-have checks remain hard stops for that image.
- Automatic mode can flag an exhausted frame and continue through the shot list, without approving each image. Missing frames are clearly listed; rejected attempts never enter the accepted collection. Pause for review remains optional.
- Disables Preview plan and New plan during Manual or Automatic processing, preventing overlapping planning and render sequences.
- Adds OpenAI Terra/Sol/Luna/Astra and Gemini Flash/Flash-Lite/Argon choices to Foundry, with isolated masked server-saved API key panels. No keys in workflows.

## 1.25.1 — Safe idle execution

- Normal ComfyUI Run with no Foundry plan, unavailable run or stale attempt now blocks downstream execution cleanly and shows guidance in the panel. It does not create a plan, render attempt or assistant request.
- Moves Preview plan into the persistent header so starting a sequence is easy to find.

## 1.25.0 — Physical inspection and named collections

- Adds separate anatomy, scene geometry, garment/material and lighting inspections before prompt match. Vision APIs receive full context and two crops in one bounded review call. Major physical defects cannot be offset by good prompt scores.
- Names new output folders from the editable AI project title or a custom name, with collision protection. Separates all attempts from a clean accepted collection and manifest; existing folders remain unchanged.
- Renames Holiday carousel to IG carousel and preserves custom briefs when switching templates. Adds coherent pose/support instructions to planning and MOSS composition.
- Brings Foundry and its Inspector into the Ember theme, with a PM forge seal, running glow and separate physical-inspection evidence cards.

## 1.24.1 — Recover reviewer formatting without losing an image

- Normalizes review status casing, common aliases, partial matches and numeric score strings. Partial matches follow tolerance; they never satisfy must-have checks. Unknown states cannot silently become passes.
- Saves original reviewer responses alongside an image hash before parsing. Saved-image recovery can reparse a compatible reply without another API call, or request one fresh review without rendering the image again.
- Broadcasts review failures to the panel so automatic runs visibly leave their running state. The recovery button now queues only the saved-image review on the server and resumes the sequence when requested.

## 1.24.0 — Automatic Foundry sequences and reference gallery

- Approve once to start a bounded server-side render/review/retry/advance loop. It continues independently of the browser and stops at errors or configured limits; pause/resume and manual override remain available.
- Restores the full Archmage style selector. Assistant choice is explicit; saved Grimoire chats are optional context under an expandable section.
- Adds Relaxed/Balanced/Strict review tolerance, match/usability scores, must-have checks and an attempt picker. Acceptance is immediate without confirmation dialogs; Manual mode labels the next-frame action clearly.
- Adds a numbered drag-and-drop image gallery with upload/folder selection, remove/clear/reorder and per-image outfit/pose/prop roles. Planning uses the actual reference images; no extra image sockets are created.
- Suggests budgets for the entire script rather than retaining a three-render cap for longer templates. Includes controller, review and gallery regression tests and updated workflow notes.
- Accepts structured optional reference notes from planners and reports the specific node/input when native workflow validation fails. A live two-frame DeepSeek/MOSS test completed automatic review and advancement on an RTX 3090.

## 1.23.0 — Foundry experimental production bench

- Adds a separate Foundry panel with script templates, saved run history, editable shot lists, explicit plan approval and bounded attempts/calls.
- Adds an explicit recommended DeepSeek V4.1 Flash preset and persistent-key panel for planning and vision review. Local Qwen remains the default; text-only DeepSeek Pro is rejected before planning.
- Reuses a selected Grimoire chat’s saved assistant/model/style settings and recent context without modifying its conversation or Spell Scroll.
- Compiles native MOSS prompts, archives actual output images and reviews their pixels against approved per-frame checks. Human acceptance is required; retries use a fresh seed and the same prompt.
- Adds saved-image review recovery, pause/stop controls, persistent run records and a separate single-frame MOSS testing workflow. No unattended loop or automatic prompt rewriting.
- Includes architecture/testing notes. Provider and queue tests use mocks; live GPU, paid API and RunPod validation remain outstanding.

## 1.22.1 — Thinking beside Send

- Adds a compact Thinking toggle beside Send, synchronized with the existing Settings control and saved workflow value. Toggling makes no model request; the next reply uses the selected setting.
- Shows a clear pressed/on state with spellbook styling and a tooltip covering model support, latency and token usage. The toggle is disabled while a request is running.


## 1.22.0 — Bound-prompt glow and fantasy spellbook theme

- Marks the reply applied to the selected Spell Scroll with an amethyst/gold glow, an Applied badge and a pressed Applied button. Matching includes conversation, stable response identity and snapshot text (legacy records fall back to index/content), so edits/regeneration do not falsely inherit selection.
- Restores highlighting from saved server state when chats load; changing destinations updates the highlight. Applying does not generate text or images.
- Adds a local spellbook theme with brass borders, dark plum panels, warm typography and faint arcane ornamentation. No external fonts or textures are loaded; the compact layout stays intact.
- Uses a slow glow animation and a static highlight when reduced motion is requested.


## 1.21.0 — Clear MOSS prompt cards and Grimoire voice

- Extracts one unambiguous JSON artifact from fenced, bare or mixed chat replies, fixing Extra data errors from trailing prose. Multiple different layouts stay blocked; invalid geometry is not silently repaired.
- Uses official-style top-left Pixel Layout drafts and compiles coordinates in code, including fractional edge enclosure. Accepts existing native centered MOSS layouts too.
- Displays a readable MOSS prompt card; Copy prompt and Spell Scroll use only compiled JSON. Discussion is not offered as a MOSS prompt. Existing recoverable replies can be applied after refreshing history, without another model call.
- Preserves actual image socket names when intermediate sockets are empty, puts current attachments before reused images, and supplies an explicit current reference map.
- Adds a warm, curious and lightly fantasy-themed default voice while preserving custom system prompts. Image captions stay precise; formatting-only requests should preserve scene content.


## 1.20.0 — Grimoire attachments and multiple image inputs

- Adds Attach, drag-and-drop and clipboard image paste, with thumbnail/file chips, removal, saved previews and Attach again. Uploading makes no model call; failed execution restores the queued draft.
- Supports images, text/code, Markdown, JSON, CSV, DOCX text and text-based PDFs. Bounded excerpts are labelled; server-owned attachment IDs never accept arbitrary paths or execute files. Adds pypdf for PDF text extraction.
- Connecting image reveals another image socket below it, through image_6, while preserving graph links. Supports six current images across sockets and attachments.
- Sends multiple API images in one answer request, without separate per-image caption calls; includes up to two recent saved image references on follow-ups. Local Qwen captions current images separately.
- Stores normalized images/extracted document text in the ComfyUI user directory, outside workflow JSON. Attachment history needs the same persistent server storage as chats.


## 1.19.2 — More room for Grimoire conversations

- Combines the chat picker, New chat and Settings into one header row.
- Keeps the style selector compact, with hover help instead of a permanent explanatory paragraph.
- Moves Spell Scroll destination and active prompt into a collapsed Applied prompt section beside Style.
- Hides idle message counts, retains status/error feedback, and reduces composer/footer padding without changing chat behavior or saved node dimensions.


## 1.19.1 — Conversational Grimoire with live style

- Replaces the visible mode selector with Style / theme above the chat. Style changes apply with the next message; changing the dropdown alone makes no model request.
- Keeps ordinary replies conversational. Prompt-format instructions apply when creating, continuing or revising a prompt; whole JSON replies still receive format validation.
- Explicitly reports changed style settings to the model on the next turn. Existing chat history and applied Spell Scroll snapshots stay intact.


## 1.19.0 — Grimoire conversation and prompt workshop

- Adds Conversation / Prompt workshop modes, shared Archmage styles, and a native MOSS JSON response contract tied to the canvas. Invalid layouts stay inspectable and cannot be applied; no automatic repair call is charged.
- Keeps the full workflow cache during chat with native partial execution; remote chats skip the local CLIP dependency. Unsupported servers fail before submission. Explicit unloading remains optional; native memory pressure can still evict models.
- Adds per-message Copy, Edit, Resend and Retry. User edits branch transactionally; manual response edits validate and save without a model call. Applied Spell Scroll snapshots remain independent.
- Renders bare JSON as copyable code and expands safe Markdown with real lists, blockquotes and tables.
- Persists resized Grimoire dimensions and named settings; embedded API-key panels no longer collapse the node.
- Adds butt-size presets and Custom to Appearance Overrides, preserving existing widget positions.


## 1.18.1 — Restore Grimoire canvas sockets

- Always expose width and height sockets on new and saved Grimoire nodes, independently of hidden settings widgets. Existing connections are preserved.
- History failures now show the actual HTTP error to help identify outdated server routes or connection problems.

## 1.18.0 — Separate conversation from applied prompts

- Grimoire is chat-only; explicit chat requests use an internal executor. Normal workflow runs exclude the conversation node.
- Adds Spell Scroll, a model-free reader of an explicitly applied response snapshot. Use this prompt is available per assistant reply; active source/text stay visible across chat changes.
- Updates the MOSS sample so only Spell Scroll feeds the encoder. Existing direct Grimoire connections require rewiring; no automatic latest-response selection is performed.

## 1.17.2 — Reuse approved replies by default

- Global Run/Queue defaults to Use latest; existing nodes migrate their hidden action to reuse. Send overrides only the isolated chat job.
- Labels continuation/rewrite/compaction as new requests to distinguish them from image generation using the saved reply.

## 1.17.1 — Resizable Grimoire chat and canvas sockets

- Exposes permanent width/height input sockets, migrates existing nodes without shifting links, and suggests Resolution when dragging backward.
- Removes the fixed 700-pixel chat widget cap, allowing the message area to fill resized nodes.
- Preserves manually chosen node dimensions through new replies, history loads and provider changes. Composer and navigation keep their own space while history scrolls.

## 1.17.0 — Grimoire messenger layout

- Replaces the button wall and native settings stack with Chat, Instructions and Settings tabs, left/right message bubbles and a fixed composer.
- Keeps Send and Generate image primary; moves secondary tools into More actions and hides empty compacted memory.
- Embeds provider-specific API-key controls directly below the Assistant provider selector, with explicit setup guidance. Saved chats, Markdown and queue isolation are retained.

## 1.16.0 — Chat composer and saved-chat picker

- Grimoire now has a message composer, Enter/Shift+Enter, New chat and a persistent saved-chat picker with restored task/system/pinned settings.
- Send queues only Grimoire and upstream inputs; generated-image dependencies are rejected. Generate image separately reuses the saved response without another assistant call.
- Adds safe Markdown headings, lists, bold/italic, links and fenced code with Copy code. Raw HTML and remote image embeds are not rendered.

## 1.15.1 — RunPod UI and saved provider keys

- Fixes Grimoire creation on HTTP origins without crypto.randomUUID. Uses random bytes for chapter IDs instead.
- Restores history on HTTP via an origin-checked POST and adds Refresh history.
- UI-added OpenAI and DeepSeek keys now persist separately in the ComfyUI user directory with atomic replacement and restricted file permissions. Remove deletes only that provider's saved key; environment credentials remain externally managed.

## 1.15.0 — Grimoire Beta

- Separate persistent conversation node with system/task/pinned instructions, appearance and image references, local/OpenAI/DeepSeek backends and server-side atomic history files.
- Adds conversational next-step/regenerate, manual/automatic summary compaction, new chapters, clear history, copy and selectable JSON/MOSS output extraction.
- Adds a complete main-pipeline-derived Grimoire → MOSS example, without DART or Archmage. Maintenance actions block primary downstream output. Memory remains server-wide plaintext, not per-user authenticated storage.

## 1.14.0 — DeepSeek API

- Adds official DeepSeek Flash and V4 Pro options to Archmage, separate masked session credentials, thinking controls, usage reporting and provider-specific errors.
- Flash supports reference images; Pro rejects images before a request. Local Qwen remains the default. No automatic network retries or private reasoning output.
- Official documentation checked 2026-11-09; mocked request/response tests only, no live paid test or comparative refusal benchmark.

## 1.13.0 — Reusable tag filter presets

- Adds Tag Filters with curated vocabulary/alias groups, independent generation bans and final cleanup, custom fields and explicit protected-tag conflict errors.
- DART Generate accepts a filter recipe. Archmage accepts the same recipe, cleans incoming tags and receives prose/JSON exclusions as model-guided instructions.
- Adds recipe socket suggestions and documentation. Existing socket order and unconnected behavior are preserved.

## 1.12.1 — Portrait and landscape ratios

- Adds 4:5 and 5:4 to Resolution and Archmage's standalone canvas presets. Existing choices and defaults remain unchanged.

## 1.12.0 — Main workflow and DART v3 selection

- Main Archmage workflow: public default Zine circuit with DART v3 ideas, Appearance Overrides, shared Qwen and MOSS base generation. No LoRAs or extra node packs.
- V3-only loader for new graphs. Deprecates the legacy multi-version loader, v1/v2 composers and v2 aspect helper while retaining saved graph execution. Drag suggestions offer v3.
- Model downloads/folders guide, community issue forms and contribution invitation, plus optional Ko-fi, PayPal and TRON support links.

## 1.11.0 — DART tags as character-safe scene ideas

- Adds Archmage's optional source_tags input, separate from explicit Scene idea and Writing rules. Default filtering protects character identity and selected visual style while retaining candidate scene/action/prop/composition tags.
- Reuses the bundled vocabulary and lexical rules for known conflicts, with removed-tag reasons and character replacements in report.source_tags. Contextual relevance and unknown tags remain model-guided; no extra LLM filtering call is added.
- Adds a Keep unselected appearance policy and reference-first guidance. Existing appearance wording checks and MOSS validation remain active with local Qwen or OpenAI.
- DART drag suggestions prioritize Archmage.source_tags; old Archmage nodes gain the new socket without moving existing input indices.
- Adds a generic DART-to-Archmage example. The supplied local MOSS Zine workflow is retained, with a separate copy moving its DART link from Concepts to source_tags.

## 1.10.0 — OpenAI assistant and masked session-key panel

- Archmage adds OpenAI Responses API support for text scenes, reference-image captions and MOSS layouts. Local Qwen remains the default.
- Adds Terra/Sol recommendations, budget Luna and a high-cost Astra warning with dated per-million-token price labels.
- A masked, non-serialized key panel clears and collapses after saving. Credentials stay in server memory for the current process and can be replaced/removed without opening files; environment keys remain supported.
- Keeps local CLIP/model-management behavior separate from cloud requests. Reports include API token usage and actual reasoning-token counts. Network errors, incomplete responses and refusals are actionable and never silently retried.
- Limits mirror-selfie geometry guidance to explicitly requested mirror scenes, avoiding unrequested content in reference captions.

## 1.9.1 — Section overlap hotfix

- Replaces floating section-header DOM overlays with fixed-height native canvas widgets so headings and controls occupy separate rows at every zoom.
- Restores defaults for newly added controls when loading named settings from older graphs, fixing the blank Memory mode selector without overwriting saved choices.
- Cache-busts the updated Archmage UI module. Frontend-only fix; refresh the browser to apply.


## 1.9.0 — Clearer canvas, style and model controls

- Archmage groups style first, then scene, canvas, reference and performance. Clear WHAT/HOW labels distinguish scene ideas from writing rules. Unused reference controls are hidden.
- New nodes default to Detailed MOSS JSON, thinking enabled, a 4096-token ceiling and 3.7 MP reference processing, matching the supplied working setup. Bright lifestyle becomes the requested photo default; saved workflows retain their choices.
- Adds Prompt Mage · Resolution: aspect ratio, total megapixels, aligned dimensions and custom sizing, with drag suggestions for Archmage and latent inputs.
- Appearance Overrides adds gender, default Female for new nodes. Older saved recipes keep unselected gender unchanged.
- Connected dimensions override aspect presets. JSON conversion retains the full completed scene, adds stronger single-photograph/mirror geometry guidance and reports actual canvas/box coverage.
- Browser Automatic shares an unambiguous compatible downstream CLIPTextEncode encoder; explicit CLIP/model choices win. Otherwise the smallest installed Qwen is used. With none installed, Archmage downloads a pinned official Qwen3.5 2B checkpoint from Hugging Face once.
- Automatic memory preparation requests native offloading of competing weights and 2 GB generation headroom. Cancellation/error cleanup releases the assistant even with normal post-run unloading disabled. This mitigates VRAM pressure; it does not promise a particular speed.
- Simplifies the workflow gallery into a few starters, with archived examples retained for compatibility. Adds full MOSS generation and same-scene prose/JSON comparison examples.

## 1.8.1 — Registry ID migration

- Moves the distribution from prompt-atelier to prompt-mage with unchanged runtime node IDs and sockets. Existing Registry installations require an explicit package migration; Git installations can update in place.
- Documents legacy package review statuses separately from upload success and Manager discovery. Renaming does not bypass Registry review.
- New uploads use the prompt-mage input subfolder; old uploaded paths remain valid.


## 1.8.0 — Run every uploaded image

- Upload Images adds a Batch mode switch and Run all images from first button. Off appends a complete workflow per uploaded image; on submits one native list run containing the entire collection.
- Automatic runs ignore manual indices, limits and global Batch Count; related captioners start at image index 0. The editor stays unchanged and settings/seeds are captured once.
- Fresh request IDs rerun downstream nodes on repeat. Sequential queue submissions, stop-adding control and no automatic retries protect against accidental duplicate jobs.
- Advanced manual controls remain available from the node menu, with unchanged global Run behavior. Versioned frontend imports avoid stale upload controls after updating.


## 1.7.0 — Archmage beta and Prompt Mage repository

- Renamed the GitHub repository to ComfyUI-Prompt-Mage and refreshed setup, navigation, screenshots and guides. Registry display name is Prompt Mage; permanent package ID stays prompt-atelier.
- Added Archmage Beta: text/reference priority, prose/native MOSS outputs, canvas and aspect presets, appearance recipes, image resizing, status/report and targeted offloading.
- Added optional native thinking with budget-exhaustion feedback and warnings when thinking is unconfirmed.
- Added 30 style/theme templates, custom notes, seeded random presets and explicit reference restyling.
- Scene Composer, Text Assistant and Image to Text are deprecated; IDs and behavior remain available for older workflows and specialized legacy features.
- Added separate experimental vocabulary-backed Tag Composer; semantic tag coverage remains model-guided.


## 1.6.0 — Prompt Mage and simpler remote uploads

- Rebranded visible node names, categories, guides, documentation and Registry display name to Prompt Mage. Existing class IDs, repository URL and Registry package ID stay compatible.
- Upload Images now has a large click-to-browse drop area, whole-node image drops and a local Choose folder action, preserving nested folder paths during upload.
- Renamed the path-based selector to Server Folder (Advanced) to distinguish server paths from uploads on RunPod.
- Removed the dependency on secure-context crypto.randomUUID so uploads do not hang on HTTP hosts where it is unavailable.


## 1.5.5 — Direct multi-image uploads

- Added Image Batch Upload: multi-file picker, drag-and-drop, thumbnail previews, reorder/remove/clear controls and upload progress/errors. Uses native ComfyUI input uploads, including on remote servers.
- Supports one image per queued run or a sequential native image list, preserving independent dimensions and filename labels. Dragging from image also wires the filename to Image to Text.
- Saved collections use input-relative paths; invalid, escaping or missing files report actionable errors. Removing from the list leaves server files intact.
- Added Ember/Studio themes, animated flames and rising embers during execution, a stronger RUNNING badge and a canvas outline. Animation respects reduced motion and stops with execution.
- Added an upload workflow example and upload endpoint/backend regression coverage.

## 1.5.4 — Visible override feedback and graceful handling

- Added Image Batch Selector: folder choice, natural filename order, one image per queued run or a native list mapped sequentially through Image to Text. Images retain independent dimensions and filenames label reports.
- Added explicit Apply exact breast-size wording. Identifiable target captions can be post-edited to use the selected phrase, with original output and edit details retained. This is labeled as an Prompt Mage caption edit, not a model unlock/compliance guarantee; ambiguous targets are not blindly rewritten.
- Both assistants now default to Warn and continue when valid model output still misses selected wording after correction. A visible amber report names missing/conflicting phrases and their output locations.
- Added On override mismatch directly to each assistant. Block downstream preserves the raw preview/report while blocking dependent data outputs, without an appearance-validation traceback.
- Appended status/report outputs; existing output positions remain unchanged. Reports include attempts, issues, policy and the actual generated text. Prompt wires remain clean prose/JSON.
- Feedback remains visible when node branding is disabled. Invalid JSON, model failures and invalid inputs still stop normally.

## 1.5.3 — Preserve selected appearance wording

- Appearance Overrides now defaults to Strict trait wording: missing selected phrases or weakened/conflicting size wording trigger a bounded correction instead of being returned silently.
- Checks prose, structured descriptions/subjects, DART tags and MOSS summaries/target-person captions. Unrelated object captions are not modified. Remaining failures report the missing/conflicting phrases.
- Disable Strict trait wording to allow model paraphrasing. Wording checks do not prove visual accuracy, multi-person identity assignment or free-form instruction compliance.

## 1.5.2 — Appearance recipes, targeted offloading and MOSS parsing

- Added optional Appearance Overrides with trait dropdowns, custom values, subject selection, literal character trigger and identity wording controls, shared by both assistants.
- Dragging from either appearance input suggests and connects the recipe node; the recipe output suggests either assistant.
- Added opt-in targeted assistant model offloading after successful generation or errors; unrelated diffusion models stay loaded. Shared encoders can reload when needed.
- Vision MOSS parsing accepts direct native summary/items layouts and supported wrappers instead of requiring layout_draft. Missing layout errors now identify returned keys; native coordinates are validated without double conversion.

## 1.5.1 — Vision JSON and searchable node names

- Image to Text now supports Plain text, Structured JSON and native MOSS JSON layout, with character instructions and formatted previews.
- MOSS vision layouts expose canvas dimensions, validate boxes and convert to native centered yxyx coordinates. Box placement is model-estimated.
- All DART display names now start with Prompt Mage for node search. Persisted class IDs and output socket positions are unchanged.
- Added an image megapixel budget, downscale-only or upscale-to-budget mode, five interpolation methods, automatic MOSS canvas sizing and width/height/processed-image outputs. Existing description connections keep output index 0.

## 1.5.0 — Prompt Mage branding and workflow gallery

- Renamed the pack and assistant display names to Prompt Mage; preserved legacy class IDs, sockets and the upstream license/history.
- Added source/model credits, Registry-shaped metadata, icon/banner, manual publication preparation and contributor guidance.
- Added combined workflows for descriptions/photos → DART v3, photos → MOSS JSON, shared vision-to-prose, and keywords → MOSS JSON.
- Grouped tools into Assistants, Vision and DART categories.
- Added four prompt lengths, a configurable generation budget, and direct-language wording options for both assistants.
- Formatted MOSS JSON output and Markdown preview; inactive layout sockets no longer draw or accept drops outside JSON mode.
- Improved MOSS caption detail, removed a misleading example text box, and added one bounded revision for very short Detailed/Extensive creative responses.

## 1.4.0

- Added local Image to Text with free instructions, exact character trigger, detail/token limits and batch selection.

## 1.3.0

- Added source tags, custom instructions, Concept/Natural language modes, validated MOSS JSON layouts and named settings persistence.

## 1.2.0

- Added complete hover help, role palettes, expandable guides, execution animations and reduced-motion support.

## 1.1.x

- Added DART v3 Preview E support, native local Qwen assistance, direct previews, compatible socket menus and reliability fixes.

Earlier DART node foundation: [nkchocoai/ComfyUI-Dart](https://github.com/nkchocoai/ComfyUI-Dart).
