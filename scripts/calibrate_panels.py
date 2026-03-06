#!/usr/bin/env python3
"""Visualise UV panel regions and kid-template layout side by side.

Usage:
    python scripts/calibrate_panels.py

Outputs:
    /tmp/model3_calibration.png
    /tmp/modely_calibration.png
"""

import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

REPO = Path(__file__).parent.parent
UV_DIR = REPO / "backend" / "app" / "templates"

# Panel definitions: uv_quad = [[TL,TR,BR,BL]] in UV 1024x1024 space
# kid_quad = [[TL,TR,BR,BL]] in warped kid-template 1024x1024 space
# Layout concept (1024x1024):
# |  LEFT SIDE  |  ROOF (full width top)  |
# |  (full ht)  |  HOOD  |  RIGHT SIDE    |
# |             |  TRUNK |  (full ht)     |
#
# Left col : x:10-370,  y:10-1014
# Roof     : x:380-1014, y:10-200
# Hood     : x:380-650,  y:210-520
# Trunk    : x:380-650,  y:530-820
# Right col: x:660-1014, y:210-1014

MODEL3_PANELS = [
    {
        "name": "left_side",
        "label": "Left Side",
        "color": (255, 180, 180),
        "uv_quad": [[14, 131], [278, 131], [278, 994], [14, 994]],
        "kid_quad": [[10, 10], [370, 10], [370, 1014], [10, 1014]],
    },
    {
        "name": "roof",
        "label": "Roof",
        "color": (180, 220, 255),
        "uv_quad": [[276, 25], [748, 25], [748, 166], [276, 166]],
        "kid_quad": [[380, 10], [1014, 10], [1014, 200], [380, 200]],
    },
    {
        "name": "hood",
        "label": "Hood",
        "color": (180, 255, 200),
        "uv_quad": [[368, 175], [655, 175], [655, 399], [368, 399]],
        "kid_quad": [[380, 210], [650, 210], [650, 520], [380, 520]],
    },
    {
        "name": "trunk",
        "label": "Trunk",
        "color": (255, 220, 180),
        "uv_quad": [[366, 684], [655, 684], [655, 897], [366, 897]],
        "kid_quad": [[380, 530], [650, 530], [650, 820], [380, 820]],
    },
    {
        "name": "right_side",
        "label": "Right Side",
        "color": (220, 180, 255),
        "uv_quad": [[749, 131], [1014, 131], [1014, 994], [749, 994]],
        "kid_quad": [[660, 210], [1014, 210], [1014, 1014], [660, 1014]],
    },
]

MODELY_PANELS = [
    {
        "name": "left_side",
        "label": "Left Side",
        "color": (255, 180, 180),
        "uv_quad": [[28, 147], [230, 147], [230, 992], [28, 992]],
        "kid_quad": [[10, 10], [370, 10], [370, 1014], [10, 1014]],
    },
    {
        "name": "roof",
        "label": "Roof",
        "color": (180, 220, 255),
        "uv_quad": [[254, 8], [771, 8], [771, 149], [254, 149]],
        "kid_quad": [[380, 10], [1014, 10], [1014, 200], [380, 200]],
    },
    {
        "name": "hood",
        "label": "Hood",
        "color": (180, 255, 200),
        "uv_quad": [[361, 151], [662, 151], [662, 392], [361, 392]],
        "kid_quad": [[380, 210], [650, 210], [650, 520], [380, 520]],
    },
    {
        "name": "trunk",
        "label": "Trunk",
        "color": (255, 220, 180),
        "uv_quad": [[302, 633], [721, 633], [721, 941], [302, 941]],
        "kid_quad": [[380, 530], [650, 530], [650, 820], [380, 820]],
    },
    {
        "name": "right_side",
        "label": "Right Side",
        "color": (220, 180, 255),
        "uv_quad": [[797, 147], [999, 147], [999, 992], [797, 992]],
        "kid_quad": [[660, 210], [1014, 210], [1014, 1014], [660, 1014]],
    },
]


def draw_panels_on_uv(uv_path: Path, panels: list[dict]) -> Image.Image:
    uv = Image.open(uv_path).convert("RGBA")
    overlay = Image.new("RGBA", uv.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for panel in panels:
        pts = [tuple(p) for p in panel["uv_quad"]]
        r, g, b = panel["color"]
        draw.polygon(pts, fill=(r, g, b, 100), outline=(r // 2, g // 2, b // 2, 255))
        cx = int(sum(p[0] for p in pts) / 4)
        cy = int(sum(p[1] for p in pts) / 4)
        draw.text((cx, cy), panel["label"], fill=(40, 40, 40, 255), anchor="mm")

    result = Image.alpha_composite(uv, overlay)
    return result.convert("RGB")


def draw_kid_layout(panels: list[dict]) -> Image.Image:
    img = Image.new("RGB", (1024, 1024), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Grid
    for x in range(0, 1024, 100):
        draw.line([(x, 0), (x, 1024)], fill=(220, 220, 220))
    for y in range(0, 1024, 100):
        draw.line([(0, y), (1024, y)], fill=(220, 220, 220))

    for panel in panels:
        pts = [tuple(p) for p in panel["kid_quad"]]
        r, g, b = panel["color"]
        draw.polygon(pts, fill=(r, g, b), outline=(r // 2, g // 2, b // 2))
        cx = int(sum(p[0] for p in pts) / 4)
        cy = int(sum(p[1] for p in pts) / 4)
        draw.text((cx, cy), panel["label"], fill=(40, 40, 40), anchor="mm")

    return img


def side_by_side(uv_vis: Image.Image, kid_vis: Image.Image, title: str) -> Image.Image:
    h = max(uv_vis.height, kid_vis.height) + 40
    w = uv_vis.width + kid_vis.width + 20
    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    canvas.paste(uv_vis, (0, 40))
    canvas.paste(kid_vis, (uv_vis.width + 20, 40))
    draw = ImageDraw.Draw(canvas)
    draw.text((uv_vis.width // 2, 20), f"{title} — UV Template", fill=(50, 50, 50), anchor="mm")
    draw.text((uv_vis.width + 20 + kid_vis.width // 2, 20), f"{title} — Kid Layout (1024x1024)", fill=(50, 50, 50), anchor="mm")
    return canvas


for model, panels in [("model3", MODEL3_PANELS), ("modely", MODELY_PANELS)]:
    uv_path = UV_DIR / f"{model}.png"
    if not uv_path.exists():
        print(f"UV template not found: {uv_path}")
        continue

    uv_vis = draw_panels_on_uv(uv_path, panels)
    kid_vis = draw_kid_layout(panels)
    out = side_by_side(uv_vis, kid_vis, model.upper())
    out_path = f"/tmp/{model}_calibration.png"
    out.save(out_path)
    print(f"Saved: {out_path}")

print("Open /tmp/model3_calibration.png and /tmp/modely_calibration.png to review.")
