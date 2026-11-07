# Archmage: clearer controls and practical MOSS setup

## New-node defaults

New nodes use **Photo · Bright lifestyle**, **Detailed**, **MOSS JSON layout**, thinking **on**, **4096 tokens**, **3.7 MP** reference processing, and normal post-run unload **off**. These retain the supplied working setup except for the requested brighter photo preset. Saved graphs keep their previous choices. A 4096-token ceiling can run out during thinking; increase it to 8192 if the status says no final answer was produced.

Bright lifestyle favors sharply resolved subjects, fabric and skin texture, rich natural color, clean directional light and readable surroundings. It does not insert beaches, swimwear, exposed anatomy or daylight into an indoor scene. No text template can guarantee the beach example's rendering quality.

## Read the node from top to bottom

1. **Style:** choose a visual treatment; optional notes refine it.
2. **Scene:** **Scene idea / WHAT** supplies subjects, place and action. **Writing rules / HOW** supplies constraints such as “keep all clothing; no blur.” Both can be empty for seeded invention.
3. **Canvas:** use Resolution → width/height for one shared source of truth. Connected dimensions beat Archmage's aspect preset. Without a reference image, dimensions are always manual/connected; the unused image-source selector is hidden. With a reference, choose processed-image dimensions or Manual explicitly.
4. **Reference image:** appears only when an image is connected. “Preserve” keeps the image's medium, ignoring your style preset; “Apply selected style” restyles the generated caption. It never changes the input pixels. Megapixel budget here processes the reference and is separate from output resolution.
5. **Model & performance:** choose encoder, thinking, token ceiling, language and memory behavior.

Appearance Overrides adds **Gender**, default **Female** on new nodes, with Male, Nonbinary, Keep unchanged and Custom options. It is a subject instruction, not an anatomy or clothing preset. Older saved recipes without gender keep it unchanged.

## Automatic encoder and memory

A wired **clip** socket always wins. Otherwise, with **Local model = Automatic**, the browser checks CLIPTextEncode nodes consuming Archmage output. If exactly one compatible Qwen CLIP branch is found, the queued prompt shares that encoder object. LoRA CLIP branches are followed, dependency cycles are rejected, and multiple conflicting encoders are left unbound. This changes the submitted prompt, not the visible graph. Connect clip explicitly for ambiguous graphs, API clients and headless use.

If there is no reusable connection, Automatic chooses the smallest named compatible Qwen in `text_encoders`. If none is installed, Archmage downloads the official [Qwen3.5 2B](https://huggingface.co/Comfy-Org/Qwen3.5) once, pinned to revision `5d50a2252bf1bcd49e5fee9b5f296986d442682b`. The first run needs internet, disk space and several GB of download. Native Hugging Face caching supports interrupted transfers. Other nodes retain their previous no-download behavior. Installed candidates are preferred without downloading. Very old ComfyUI builds may need updating to support Qwen3.5.

**Memory mode = Automatic** asks ComfyUI to free competing model memory before text generation, keeping the selected encoder and reserving 2 GB of headroom. **Native ComfyUI** skips this preparation. Errors and cancellation release the assistant even when normal post-run unloading is off; cleanup failures are logged without hiding the original error. The existing unload switch still controls successful runs. Shared encoders may need to reload for later text encoding after an error or explicit unloading.

This targets VRAM pressure after diffusion and interrupted generation. Dynamic loading, context length and model kernels can also affect speed; no particular tokens/second improvement is promised.

## Canvas and JSON quality

Native MOSS boxes use centered absolute pixels, ordered **y1, x1, y2, x2**. A 1568×2368 canvas spans x **−784…784** and y **−1184…1184**. The application's conversion now has rectangular-canvas regression checks; `report.layout` records actual dimensions, coordinate limits and union area of boxes. The subject box need not cover all pixels: `summary.caption` describes the full scene and unboxed background remains valid. Boxes do not crop the image or guarantee diffusion placement.

Text-to-JSON conversion now retains the completed prose verbatim in the summary before appearance edits, rather than allowing a shorter second-pass summary to discard detail. Layout planning receives the original constraints and directions for coherent mirror geometry and one continuous photograph. These are model instructions, not proof of correct anatomy or reflection physics.

For a fair check, keep scene, seed, checkpoint, sampler, size and steps fixed, and compare Archmage's **description** with **moss_json** in the same positive encoder. Use the [paired workflows](../workflows/start-here/README.md). Preserve a prose option when layout hurts image quality.
# Additional aspect ratios

Resolution and Archmage support **4:5** portrait and **5:4** landscape. Resolution uses your megapixel budget and rounds to its selected alignment. Archmage's standalone presets use 1024 × 1280 and 1280 × 1024 respectively; connected width/height still take priority. Choose the ratio in Resolution when using the main workflow so the latent and prompt share one canvas.
