#!/usr/bin/env python3
"""Generate printable PDF templates for Kids Tesla Art.

Each template is an A4 page with:
  - Kid-friendly car panel layout (Left Side, Roof, Hood, Trunk, Right Side)
    arranged so kids can intuitively color each part of the car.
  - Panel regions match the kid_quad coordinates in *_panels.json exactly,
    so the kid's coloring maps directly onto the Tesla UV wrap via per-panel
    perspective warping in the backend.
  - 4 ArUco markers (DICT_4X4_50, IDs 0-3) at the page corners.

Usage:
    python scripts/generate_templates.py

Outputs:
    frontend/public/templates/model3-template.pdf
    frontend/public/templates/modely-template.pdf
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas
except ImportError as exc:
    print(f"Missing dependency: {exc}")
    print("Install with: pip install opencv-contrib-python Pillow reportlab")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PDF_OUTPUT_DIR = REPO_ROOT / "frontend" / "public" / "templates"
UV_DIR = REPO_ROOT / "backend" / "app" / "templates"

PAGE_W_PX, PAGE_H_PX = 2480, 3508
PAGE_W_PT, PAGE_H_PT = A4

ARUCO_DICT_ID = cv2.aruco.DICT_4X4_50
MARKER_PX = 160
MARGIN_PX = 120

DRAW_X0 = MARGIN_PX + MARKER_PX
DRAW_Y0 = MARGIN_PX + MARKER_PX
DRAW_X1 = PAGE_W_PX - MARGIN_PX - MARKER_PX
DRAW_Y1 = PAGE_H_PX - MARGIN_PX - MARKER_PX
DRAW_W = DRAW_X1 - DRAW_X0
DRAW_H = DRAW_Y1 - DRAW_Y0

PANEL_COLORS = {
    "left_side":  (255, 230, 230),
    "roof":       (230, 240, 255),
    "hood":       (230, 255, 235),
    "trunk":      (255, 245, 225),
    "right_side": (240, 230, 255),
}
PANEL_BORDER = (160, 160, 160)
LABEL_COLOR = (80, 80, 80)


def _page_pt(x, y):
    fx, fy = x / 1024.0, y / 1024.0
    return DRAW_X0 + fx * DRAW_W, DRAW_Y0 + fy * DRAW_H


def _generate_aruco(marker_id, size_px):
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT_ID)
    marker_bgr = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size_px)
    return Image.fromarray(cv2.cvtColor(marker_bgr, cv2.COLOR_BGR2RGB))


def generate_template_png(model):
    panels_path = UV_DIR / f"{model}_panels.json"
    panels = json.loads(panels_path.read_text())["panels"] if panels_path.exists() else []

    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    for panel in panels:
        pts = [_page_pt(x, y) for x, y in panel["kid_quad"]]
        color = PANEL_COLORS.get(panel["name"], (240, 240, 240))
        draw.polygon(pts, fill=color, outline=PANEL_BORDER)
        cx = sum(p[0] for p in pts) / 4
        cy = sum(p[1] for p in pts) / 4
        draw.text((cx, cy), panel.get("label", panel["name"]), fill=LABEL_COLOR, anchor="mm")

    # Divider lines
    vx0 = _page_pt(380, 0)[0]
    vx1 = _page_pt(660, 0)[0]
    hy0 = _page_pt(0, 205)[1]
    hy1 = _page_pt(0, 525)[1]
    draw.line([(vx0, DRAW_Y0), (vx0, DRAW_Y1)], fill=(200, 200, 200), width=3)
    draw.line([(vx1, hy0), (vx1, DRAW_Y1)], fill=(200, 200, 200), width=3)
    draw.line([(vx0, hy0), (DRAW_X1, hy0)], fill=(200, 200, 200), width=3)
    draw.line([(vx0, hy1), (vx1, hy1)], fill=(200, 200, 200), width=3)

    for marker_id, (mx, my) in enumerate([
        (MARGIN_PX, MARGIN_PX),
        (PAGE_W_PX - MARGIN_PX - MARKER_PX, MARGIN_PX),
        (PAGE_W_PX - MARGIN_PX - MARKER_PX, PAGE_H_PX - MARGIN_PX - MARKER_PX),
        (MARGIN_PX, PAGE_H_PX - MARGIN_PX - MARKER_PX),
    ]):
        img.paste(_generate_aruco(marker_id, MARKER_PX), (mx, my))

    model_label = "Model 3" if model == "model3" else "Model Y"
    lines = [
        f"Kids Tesla Art — {model_label}",
        "Color each section with crayons or markers.",
        "Keep all 4 corner squares visible when you take a photo!",
        "Upload at tesla.sunggeun.com",
    ]
    base_y = PAGE_H_PX - MARGIN_PX - MARKER_PX // 2
    for i, line in enumerate(lines):
        draw.text(
            (PAGE_W_PX // 2, base_y - (len(lines) - 1 - i) * 70),
            line, fill=(80, 80, 80), anchor="mm",
        )

    return img


def create_pdf(template_png, output_path):
    import io
    output_path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    template_png.save(buf, format="PNG")
    buf.seek(0)
    c = rl_canvas.Canvas(str(output_path), pagesize=A4)
    c.drawImage(ImageReader(buf), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT)
    c.save()
    print(f"  PDF saved: {output_path}")


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["model3", "modely"])
    opts = parser.parse_args(args)
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for model in opts.models:
        print(f"\nGenerating: {model}")
        create_pdf(generate_template_png(model), PDF_OUTPUT_DIR / f"{model}-template.pdf")
    print("\nDone.")


if __name__ == "__main__":
    main()
