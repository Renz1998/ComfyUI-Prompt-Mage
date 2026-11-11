# Grimoire configuration map

Grimoire is a ComfyUI chat interface with server-side saved conversations. It is separate from Archmage and from image generation. Sending chat creates a reply; applying a reply to Spell Scroll selects the snapshot used by the connected image workflow.

## Editing the assistant

Open the Grimoire node's **Instructions** tab:

- **System prompt:** general role, tone and behavior.
- **Task instructions:** the current project, output requirements and workflow instructions.
- **Pinned facts:** durable character/project facts that must survive compaction.

The selected chat saves these settings. Opening a different saved chat can restore different values. Editing only the Python default does not replace a custom system prompt. Known earlier built-in prompts are upgraded by `effective_system` on the next turn.

The **Settings** tab selects the provider, model, thinking, token ceiling and output format. The chat style dropdown is supplied on the next message. Changing a setting alone makes no API call. Thinking affects reasoning, not content permissions.

## How a request is assembled

`py/nodes/grimoire.py` combines these parts:

1. Effective system prompt.
2. Task instructions and pinned facts.
3. Connected Appearance Overrides recipe and canvas dimensions.
4. `response_contract` from `py/dart/grimoire_prompt.py`: conversation behavior, current style, reference roles and selected output-format instructions.

The user message contains structured conversation data: compacted summary, recent turns and the current message. Image references are attached when supported by the provider. Previous assistant replies remain in history; changing the system prompt does not erase them. A new chat starts without that history; preserve important project facts in the instruction fields first.

## Important source files

| File | Responsibility |
| --- | --- |
| `py/dart/grimoire_prompt.py` | Built-in prompt, default migration, style/format contract, MOSS extraction |
| `py/nodes/grimoire.py` | Request assembly, actions, provider dispatch, saved settings |
| `py/dart/grimoire.py` | Conversation persistence and message edits |
| `py/dart/deepseek_assistant.py` | Official DeepSeek transport and model dropdown |
| `py/dart/credentials.py` | Separate server-saved provider keys |
| `web/grimoire.mjs` and `web/grimoire_layout.mjs` | Chat UI, settings bindings and serialized fields |

DeepSeek Flash is routed through `https://api.deepseek.com/chat/completions` with model alias `deepseek-flash`. The adapter sends system/user messages, a token ceiling and the thinking setting. It does not retry refusals. The UI label can name the current model release while the request uses the official alias.

MOSS JSON has an additional format contract even with a custom system prompt. Grimoire requests a top-left pixel draft, then the application validates and converts it into native `summary`, `items`, `bbox_coord_space: abs_centralized` and `bbox_format: yxyx`. Preserve that compiler contract when changing assistant tone or instructions.

## Storage and backups

Paths are relative to ComfyUI's configured user directory:

- `prompt_mage/grimoire/<conversation_id>.json`: settings, summary and turns.
- `prompt_mage/credentials/<provider>.json`: secret provider key. Do not share, commit, print or embed it in workflows.
- `default/workflows/`: saved workflows; these can contain system/task instructions and serialized UI settings.

Back up a chat or workflow before editing its JSON. Preserve conversation IDs, turns, selected output IDs, links and unrelated node settings. Prefer the UI for ordinary instruction changes. Python edits require an idle ComfyUI restart; frontend edits also require a browser refresh. Provider behavior remains controlled by the selected model/service.
