# Grimoire → Foundry

Discuss a project in Grimoire, then send a saved production brief to Foundry. Later chat does not change that snapshot or an approved run.

[Example MOSS workflow](../workflows/experimental/02-grimoire-to-foundry-moss.json) · [Foundry guide](FOUNDRY_EXPERIMENT.md)

1. Connect Grimoire's **production_brief** output to Foundry's **production_brief** input. Dragging either socket suggests the matching node.
2. Discuss the concept, style, references, frame count and aspect ratio. Use the same Appearance Overrides node for both if desired.
3. Click **Send brief → Foundry** when agreed. One assistant request compiles a structured brief. It does not add a chat turn, approve a plan or render images.
4. An idle, new Foundry draft fills with the brief, consistency rules, reviewer guidance, style, frame count and references. Ready or approved plans remain unchanged; choose New plan/Edit brief, then **Check sent brief → Use this brief for a new plan** when appropriate.
5. Review fields and spending limits. Import keeps Foundry's model, keys, passing score, retry policy, tries, render cap and assistant-call cap. If the frame count exceeds those caps, Foundry warns and opens spending limits. Using suggested limits is an explicit choice.
6. Preview the plan, edit it if needed, then approve production as usual.

## What transfers

- The latest agreed direction, consistency rules and observable review guidance from recent conversation, pinned facts and compacted memory.
- A selected style and optional custom notes. Unspecified choices retain current settings.
- An explicitly agreed frame count, aspect ratio or dimensions. A connected Prompt Mage Resolution changes to the agreed ratio while keeping its megapixel budget. Explicit dimensions select Custom. Other connected canvas nodes are kept, with a message to adjust them manually. Without canvas links, the agreed dimensions or ratio resolve at the existing default pixel area.
- Selected image attachments and current connected references, with roles. Connected images become server-owned attachments visible in Foundry's gallery.
- The captured appearance recipe as a fallback. A separately connected Foundry Appearance Overrides input takes priority.

The compiler does not guess when you have agreed: Send brief is the explicit handoff. Review its interpretation before planning. Long conversations may need compaction; summaries are lossy. Unknown choices remain unset.

## Persistence and execution

Briefs live under **ComfyUI user/prompt_mage/production_briefs** as immutable versioned JSON, with a latest pointer per conversation. Keep this directory and the attachment store on persistent RunPod storage. Imported IDs need the same server data to reopen.

Only Send compiles a brief, using Grimoire's selected model and key. Local compilation runs through ComfyUI's queue; API compilation may incur charges. Reading, importing and reusing a snapshot require no assistant request. Foundry generation jobs remove the live Grimoire dependency, so diffusion does not chat, recompile or follow later conversation. Existing output positions are preserved; the new socket is appended.

If the conversation changes during compilation, publication is rejected as stale. Failures keep the previously sent brief intact. Only known creative fields and available reference IDs are accepted; provider settings, keys and spending caps cannot be imported from the model's JSON.

## Validation

An isolated local OpenAI Terra test compiled an agreed three-frame, 4:5 brief without changing the chat, then produced a matching Foundry plan with zero rendered images and preserved caps. Automated tests cover immutable snapshots, stale conversations, forbidden fields, unchanged provider/caps, canvas import, source sockets and removal of chat dependencies from generation jobs. Browser component checks verify visible field and reference transfer. This validates local setup; RunPod deployment was not tested.
