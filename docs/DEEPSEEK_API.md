# DeepSeek API in Archmage

Select **Assistant → DeepSeek API**. Paste a DeepSeek key into the masked **DeepSeek key panel**, then click **Add key**. The field clears and collapses. Keys stay in ComfyUI server memory for this session, are never read back, and are not saved in workflows or browser storage. Re-add after restart. An existing `DEEPSEEK_API_KEY` server environment variable is supported too. OpenAI and DeepSeek credentials are separate.

## Models checked November 9, 2026

- **DeepSeek V4.1 Flash · Recommended · Text + images** uses `deepseek-flash`, currently served by **DeepSeek-V4.1-Flash-1017**. It supports image references, scene composition and MOSS layout generation.
- **DeepSeek V4 Pro · Text only · Check pricing** uses `deepseek-v4-pro`. Reference images are rejected before an API request; select Flash for vision.

These are official service aliases, not pinned model snapshots; backing releases may change. Retired Flash/experimental vision names are intentionally omitted. Sources: [official model overview](https://api-docs.deepseek.com/), [vision guide](https://api-docs.deepseek.com/guides/vision/), [API reference](https://api-docs.deepseek.com/api/create-chat-completion/). Check [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing) and your provider dashboard before use. Numerical pricing is not hardcoded here because the pricing page did not expose a verifiable current table during integration.

## Thinking, costs and privacy

Thinking on sends DeepSeek's enabled/high setting; off explicitly disables thinking. The generation token ceiling applies per call, including thinking. Private reasoning content is not returned or persisted by Prompt Mage. Provider usage counts are included in Archmage's report.

Scene text, appearance recipes, instructions and supported reference images are sent to **DeepSeek's hosted API** when you run the node. Use a trusted/private connection to ComfyUI; a session key is shared by that server's users. The masked panel protects workflow files, not a publicly exposed server. We make no claim about provider-side retention; review DeepSeek's current service terms/privacy information.

MOSS composition can use multiple billable calls, including a format correction. No automatic network retries are made. Cancellation/timeouts cannot undo a request the provider already processed. Refusal, incomplete output, missing final text and billing/rate errors are surfaced rather than rewritten into claimed success.

DeepSeek support is not an “uncensored” guarantee. No comparative refusal benchmark was performed. Existing language/appearance controls remain writing instructions, not overrides of provider behavior.

Validation uses mocked API responses and request inspection; a live DeepSeek key has not been used for an end-to-end generation test in this release. Local Qwen remains the default; existing workflows are not switched to a paid backend.
