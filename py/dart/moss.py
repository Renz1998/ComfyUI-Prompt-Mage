"""Compile layout drafts to OpenMOSS USERGUIDE's centered-pixel yxyx format.

Reference: https://github.com/OpenMOSS/MOSS-Image/blob/main/USERGUIDE.md
Draft boxes use ordinary top-left pixel xyxy coordinates for easier planning.
"""

import json
import math


def canvas_size(width, height):
    if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 or v % 16 for v in (width, height)):
        raise ValueError("MOSS canvas width and height must be positive multiples of 16. Match the image generation size.")


def compile_layout(layout, width, height, draft=False):
    canvas_size(width, height)
    if not isinstance(layout, dict):
        raise ValueError("MOSS layout must be a JSON object with summary and items.")
    summary = layout.get("summary")
    if not isinstance(summary, dict) or not isinstance(summary.get("caption"), str) or not summary["caption"].strip():
        raise ValueError("MOSS summary.caption must describe the overall scene.")
    meta = summary.get("meta", [])
    if not isinstance(meta, list) or not all(isinstance(v, str) for v in meta):
        raise ValueError("MOSS summary.meta must be a list of strings.")
    if summary.get("canvas", "single") != "single":
        raise ValueError("This MOSS layout supports a single canvas.")
    if not draft and (layout.get("bbox_coord_space") != "abs_centralized" or layout.get("bbox_format") != "yxyx"):
        raise ValueError("MOSS JSON needs bbox_coord_space abs_centralized and bbox_format yxyx.")
    items = layout.get("items")
    if not isinstance(items, list) or not items or len(items) > 32:
        raise ValueError("MOSS layout needs between 1 and 32 text/object items.")
    compiled = []
    for index, item in enumerate(items):
        prefix = f"MOSS item {index + 1}"
        if not isinstance(item, dict) or item.get("label") not in ("text", "object"):
            raise ValueError(prefix + " label must be text or object.")
        if not isinstance(item.get("caption"), str) or not item["caption"].strip():
            raise ValueError(prefix + " needs a caption.")
        box = item.get("bbox")
        if not isinstance(box, list) or len(box) != 4 or any(
            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in box
        ):
            raise ValueError(prefix + " bbox needs four finite numbers.")
        if draft:
            x1, y1, x2, y2 = box
            if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                raise ValueError(prefix + ' draft bbox is inverted, empty, or outside the selected canvas.')
            box = [math.floor(y1) - height / 2, math.floor(x1) - width / 2, math.ceil(y2) - height / 2, math.ceil(x2) - width / 2]
        y1, x1, y2, x2 = box
        if not (-height / 2 <= y1 < y2 <= height / 2 and -width / 2 <= x1 < x2 <= width / 2):
            raise ValueError(prefix + " bbox is inverted, empty, or outside the selected canvas. Check dimensions or regenerate.")
        box = [round(v) for v in box]
        if box[0] >= box[2] or box[1] >= box[3]:
            raise ValueError(prefix + " bbox is smaller than one pixel.")
        result = {"label": item["label"], "caption": item["caption"].strip()}
        if item["label"] == "text":
            if not isinstance(item.get("text"), str) or not item["text"].strip():
                raise ValueError(prefix + " needs the exact visible text.")
            result["text"] = item["text"]
        result["bbox"] = box
        compiled.append(result)
    return {"summary": {"meta": meta, "canvas": "single", "caption": summary["caption"].strip()},
            "items": compiled, "bbox_coord_space": "abs_centralized", "bbox_format": "yxyx"}


def read_layout(text, width, height):
    try:
        layout = json.loads(text)
    except (TypeError, ValueError):
        raise ValueError("MOSS layout override must be valid JSON, without Markdown fences.") from None
    return compile_layout(layout, width, height)


def layout_diagnostics(layout, width, height):
    """Report actual box coverage, not an invented requirement to fill every pixel."""
    boxes = [item['bbox'] for item in layout['items']]
    xs = sorted({x for y1, x1, y2, x2 in boxes for x in (x1, x2)})
    area = 0
    for left, right in zip(xs, xs[1:]):
        intervals = sorted((y1, y2) for y1, x1, y2, x2 in boxes if x1 <= left and x2 >= right)
        end = -height / 2
        for start, stop in intervals:
            area += (right - left) * max(0, stop - max(start, end))
            end = max(end, stop)
    return {'canvas': [width, height], 'native_x_range': [-width / 2, width / 2],
            'native_y_range': [-height / 2, height / 2], 'item_count': len(boxes),
            'box_union_fraction': round(area / (width * height), 4),
            'note': 'Summary describes the whole canvas. Boxes locate subjects, not a crop or pixel mask. Unboxed background is valid. Match these dimensions to the latent; diffusion placement is approximate.'}


def layout_instruction(width, height):
    canvas_size(width, height)
    return f"""
Also return layout_draft, an object with summary and items for a {width}x{height} canvas.
summary has meta (a short list of style/media tags), canvas (\"single\"), and caption (the overall scene).
Write a substantive summary caption and specific item captions at the requested prompt length.
Describe appearance, pose, clothing or surface textures, light, color, spatial relationships and framing
where supported. Item captions should add local detail instead of repeating the summary.
Each item has label (\"object\" or \"text\"), caption, and bbox [x_min,y_min,x_max,y_max].
These draft boxes are TOP-LEFT pixel xyxy coordinates: x from 0 to {width}, y from 0 to {height}.
Use at most 8 major items. All boxes must have positive area inside the canvas. Plan natural composition;
intentional overlaps are allowed. Do not draw boxes around every small attribute.
For text items include text with the EXACT requested wording and line breaks. Do not invent visible text.
Only create text items when the user explicitly requests visible words in the image.
Never turn the scene description, source tags or writing instructions into a text item.
When no visible wording is requested, use object items only. This need not be a poster.
Object items do not need text. Avoid prohibited concepts. Keep required concepts in summary.caption.
For a continuous photograph, describe the complete scene in summary.caption, including camera viewpoint,
focus, light direction, materials and background. Do not turn it into a collage, poster or panel layout.
Use one box per major subject, not separate boxes for their face, hair, breasts, hands or clothing.
Place the subject box around their actual visible silhouette including raised arms; do not stretch them
across the entire canvas unless the framing truly fills it. The background may extend across the full canvas.
Preserve requested sharp focus/no-blur instructions. A phone photo need not be blurry or low resolution.
Do not output centered coordinates: the application converts the draft into MOSS coordinates.
The exact layout_draft structure is:
{{"summary":{{"meta":["requested medium/style"],"canvas":"single","caption":"Write the full overall scene here"}},"items":[
{{"label":"object","caption":"Write this subject's specific appearance, pose, materials and light here","bbox":[0,{height // 4},{width},{height}]}}
]}}
This is a schema example, not the requested scene. Replace every placeholder.
If visible words ARE requested, add a text item with label text, caption describing its lettering/placement,
text containing ONLY those exact visible words, and its own bbox. Every text item MUST have a text key.
"""
