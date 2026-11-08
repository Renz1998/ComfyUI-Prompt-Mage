# OpenAI in Archmage

1. In **MODEL & PERFORMANCE**, change **Assistant → OpenAI API**.
2. Paste your key into the **masked key panel**, then click **Add key**. The field clears and collapses to a configured indicator. Open **Add / replace key** to change it; **Remove saved key** deletes that provider’s saved credential and clears its runtime copy.
3. Choose **GPT-6.1 Terra** for lower-cost visual/writing work, or **GPT-6.1 Sol** for more demanding composition. Run as usual: concepts, reference images, appearance settings, styles and MOSS JSON still work.

Local Qwen remains the default. Updating an existing workflow never switches it to a paid backend automatically. The local CLIP and VRAM/unload controls are ignored in API mode; the image-generation workflow can still use its usual local MOSS text encoder downstream.

<img src="../assets/screenshots/openai-key-panel.jpg" alt="Archmage OpenAI controls with an empty masked key field and Add key button" width="500">

The screenshot shows an empty entry field; the configured indicator never reveals the stored key.

## Models and prices

The dropdown labels show standard USD per **one million input / output tokens**, checked November 7, 2026:

| Model | Input / output | Suggested use |
| --- | --- | --- |
| [GPT-6.1 Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra) | $1 / $5 | Recommended lower-cost starting point |
| [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) | $2 / $10 | Recommended for harder composition |
| [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) | $0.10 / $0.50 | Budget option; compare prompt quality |
| [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) | $10 / $50 | **HIGH COST**; not selected automatically |

This is a pricing snapshot, not a per-image quote or an invoice estimate. Access and prices can change. Image inputs, reasoning, caching, context length and service pricing affect the final bill. No priority, ultrafast, pro, browsing or other paid tools are enabled by this integration. API charges and ChatGPT subscription allowances are separate considerations; check your API project's billing settings.

Text → prose normally makes one request. Text → MOSS normally makes two: scene writing, then layout conversion. A malformed layout may trigger one additional correction request. Image captions and appearance corrections can also require a second request. Each mapped batch image incurs its own requests. The node does not automatically retry network errors, rate limits or refusals.

## Key handling

The panel sends the key to **your ComfyUI server**, which saves it in its provider-specific credential file and keeps a runtime copy. It is shared by this server's OpenAI nodes, does not go into workflow JSON, browser storage, repository files or node reports, and survives restarts when the user directory is retained. Use a trusted/private ComfyUI connection; remote servers should use HTTPS and appropriate access protection. Anyone allowed to queue workflows on that server may consume the configured key's API budget.

The configured indicator means a credential was added, not that billing/access was verified. The first generation reports invalid/expired keys, unavailable models or quota errors. A key stored in the server's `OPENAI_API_KEY` environment variable is also supported; removing the saved key does not delete that environment variable. Advanced API workflows may override `openai_key_env` with another variable name. Never put the actual key in that field or any prompt.

The provided temporary test credential was used only for bounded live checks; no credential is bundled with the package. Add your own key when using the node, and revoke keys that have been shared in chat.

## Thinking, cancellation and image privacy

Thinking on requests **medium** reasoning. Off requests **none** for Terra/Luna and the supported minimum **low** for Sol/Astra. The token ceiling includes reasoning and final output per request. Reports show usage and reasoning-token counts; private reasoning traces are not exposed. The seed varies scene suggestions; it does not make API sampling deterministic.

Requests use the [Responses API](https://developers.openai.com/api/docs/guides/responses) with `store: false`. Connected images are encoded and sent directly to OpenAI with the scene/appearance instructions. They are not uploaded to a separate image host. `store: false` does not mean that all provider-side logging or retention is disabled; the provider's data policies still apply.

An in-flight synchronous request may finish and be billed even if you cancel ComfyUI or the request times out. Cancellation checks prevent subsequent generation stages after control returns. No automatic retry occurs after an uncertain network result. OpenAI applies its own content policies; Direct / explicit language and appearance instructions do not override them. Refusals stop the request rather than being rewritten into a claimed success.

Saved credentials use provider-specific plaintext files under `ComfyUI user directory/prompt_mage/credentials/`, with restricted permissions. Use persistent RunPod storage and protect server access. Replace overwrites only the selected provider; Remove deletes its saved file. Environment variables remain externally managed. See [storage details](GRIMOIRE.md).
