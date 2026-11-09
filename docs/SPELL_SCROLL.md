# Chat → Apply → Generate

**Grimoire is chat only. Spell Scroll is the workflow prompt reader.** They share an explicitly chosen prompt slot, not a graph connection. [Updated MOSS sample](../workflows/start-here/08-grimoire-to-moss.json).

1. Add Grimoire and Spell Scroll. Connect **Spell Scroll.prompt → positive text encoder**, and Resolution width/height to Spell Scroll and the latent. Grimoire can share the same Resolution and appearance recipe for conversation context.
2. Send messages in Grimoire. Chat uses its own internal execution target and does not run downstream image generation.
3. Select the destination Spell Scroll ID in Grimoire, then click **Use this prompt** on the particular assistant response you want. The server verifies that response still exists in the saved chat, validates extraction and saves a separate snapshot.
4. **Run ComfyUI** to generate images from the applied snapshot. Spell Scroll has no assistant model, key input or API calls. Repeated runs, further chat and chat switching do not replace the snapshot.

**Active prompt** shows its source and lets you inspect its full contents. Selecting a different chat does not select a different prompt. To change the workflow prompt, apply another response explicitly. Clearing conversation history does not clear an already applied snapshot. A response removed by regeneration/compaction cannot be applied from a stale view; refresh first.

The snapshot includes the selected output mode/JSON field. MOSS schemas/boxes are validated by Spell Scroll against its connected canvas when read. Invalid or missing snapshots stop the workflow rather than calling a model or selecting a newer reply automatically. Review content and coordinate compatibility when changing resolution.

Each Spell Scroll has a `scroll_id` (default `main-scroll`). Use distinct IDs for independent projects. The selected destination is independent of chat IDs. Snapshots are plaintext files under `ComfyUI user directory/prompt_mage/spell_scroll/`; keep this directory on persistent storage. They are server-wide, not private per browser login, and do not travel with workflow JSON. No API key is included.

## Existing workflows

Replace the old **Grimoire.output → encoder** connection with **Spell Scroll.prompt → encoder**. Remove diagnostic connections from Grimoire if you want it completely absent from normal workflow execution. Grimoire no longer runs automatically as an output node; its chat UI queues a hidden internal turn executor. Its legacy data outputs are for explicit chat jobs, not automatic prompt selection.

Restart ComfyUI after installing this update, then hard-refresh the browser. The new Spell Scroll and internal chat executor require backend registration. Start with the updated sample if you prefer to avoid manual rewiring.
