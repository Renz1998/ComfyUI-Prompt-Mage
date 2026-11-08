# Changelog

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
