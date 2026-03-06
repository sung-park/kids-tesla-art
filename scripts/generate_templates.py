#!/usr/bin/env python3
"""Generate printable PDF templates with ArUco markers for Kids Tesla Art.

Each template is an A4 page containing:
  - The official Tesla UV template as the coloring area (so coloring maps 1:1 to the wrap)
  - 4 ArUco markers (DICT_4X4_50, IDs 0-3) at the corners

Marker placement convention:
  - ID 0 → top-left
  - ID 1 → top-right
  - ID 2 → bottom-right
  - ID 3 → bottom-left

The inner corner of each marker defines the bounding rectangle of the drawing area.
The UV template is embedded as-is so that pixels colored by the child map directly
onto the corresponding UV panel on the Tesla wrap.

Usage:
    pip install opencv-contrib-python Pillow reportlab
    python scripts/generate_templates.py

Outputs:
    frontend/public/templates/model3-template.pdf
    frontend/public/templates/modely-template.pdf

Note:
    backend/app/templates/*.png are NOT regenerated if they already exist.
    Download official UV templates from https://github.com/teslamotors/custom-wraps
"""

import argparse
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
UV_OUTPUT_DIR = REPO_ROOT / "backend" / "app" / "templates"

# A4 in points (72pt = 1 inch)
PAGE_W, PAGE_H = A4  # 595.28 x 841.89 pt
MARGIN_PT = 36  # 0.5 inch margins
MARKER_SIZE_PT = 40  # ArUco marker size in points
MARKER_SIZE_PX = 80  # Raster size for marker generation

ARUCO_DICT = cv2.aruco.DICT_4X4_50


def _generate_aruco_marker_pil(marker_id: int, size_px: int) -> Image.Image:
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    marker_bgr = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size_px)
    return Image.fromarray(cv2.cvtColor(marker_bgr, cv2.COLOR_BGR2RGB))


def generate_template_png(
    model: str,
    page_w_px: int = 2480,
    page_h_px: int = 3508,
) -> Image.Image:
    """Generate a full-page template image with ArUco markers and UV template as coloring area.

    The official Tesla UV template is embedded as the coloring sheet so that the
    child's coloring maps 1:1 onto the final Tesla wrap.

    Args:
        model: Tesla model identifier for labeling.
        page_w_px: A4 width at 300 DPI.
        page_h_px: A4 height at 300 DPI.

    Returns:
        PIL Image of the template page (RGB).
    """
    img = Image.new("RGB", (page_w_px, page_h_px), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    margin = 120  # pixels
    marker_px = MARKER_SIZE_PX * 2

    # Place ArUco markers at corners (IDs 0=TL, 1=TR, 2=BR, 3=BL)
    positions = [
        (margin, margin),
        (page_w_px - margin - marker_px, margin),
        (page_w_px - margin - marker_px, page_h_px - margin - marker_px),
        (margin, page_h_px - margin - marker_px),
    ]

    for marker_id, (mx, my) in enumerate(positions):
        marker_img = _generate_aruco_marker_pil(marker_id, marker_px)
        img.paste(marker_img, (mx, my))

    # Drawing area (between inner corners of markers)
    draw_x = margin + marker_px + 40
    draw_y = margin + marker_px + 40
    draw_w = page_w_px - 2 * (margin + marker_px + 40)
    draw_h = page_h_px - 2 * (margin + marker_px + 40) - 200

    # Embed UV template as the coloring area (1:1 pixel correspondence with the wrap)
    uv_path = UV_OUTPUT_DIR / f"{model}.png"
    if uv_path.exists():
        uv_rgba = Image.open(uv_path).convert("RGBA")
        # Composite onto white background to preserve transparency as white
        white_bg = Image.new("RGB", uv_rgba.size, (255, 255, 255))
        white_bg.paste(uv_rgba, mask=uv_rgba.split()[3])
        uv_img = white_bg
        # Fit UV template into drawing area while preserving aspect ratio
        uv_size = min(draw_w, draw_h)
        uv_img = uv_img.resize((uv_size, uv_size), Image.LANCZOS)
        uv_x = draw_x + (draw_w - uv_size) // 2
        uv_y = draw_y + (draw_h - uv_size) // 2
        img.paste(uv_img, (uv_x, uv_y))
    else:
        # Fallback: plain border if UV template not yet downloaded
        draw.rectangle([draw_x, draw_y, draw_x + draw_w, draw_y + draw_h],
                       outline=(180, 180, 180), width=3)
        draw.text(
            (page_w_px // 2, draw_y + draw_h // 2),
            "Download UV template from github.com/teslamotors/custom-wraps",
            fill=(200, 50, 50),
            anchor="mm",
        )

    # Labels
    model_label = "Model 3" if model == "model3" else "Model Y"
    instructions = [
        f"Kids Tesla Art — {model_label} Template",
        "Color the panels. Use crayons, markers, or watercolors.",
        "Then take a photo and upload at tesla.sunggeun.com",
        "Keep all 4 corner markers (black squares) fully visible in your photo!",
    ]

    text_y = draw_y + draw_h + 40
    for i, line in enumerate(instructions):
        draw.text((page_w_px // 2, text_y + i * 60), line, fill=(60, 60, 60), anchor="mm")

    return img


def generate_uv_template_placeholder(model: str, size: int = 1024) -> Image.Image:
    """Generate a placeholder UV template image.

    In production, replace this with the official Tesla UV template PNG
    from https://github.com/teslamotors/custom-wraps

    Args:
        model: Tesla model identifier.
        size: Template size in pixels.

    Returns:
        PIL Image (RGBA) representing the UV template.
    """
    img = Image.new("RGBA", (size, size), color=(230, 230, 230, 255))
    draw = ImageDraw.Draw(img)

    # Draw a simple car-shaped UV unwrap guide
    colors = {
        "hood": (200, 220, 255, 255),
        "roof": (220, 200, 255, 255),
        "door": (200, 255, 220, 255),
        "trunk": (255, 220, 200, 255),
    }

    panels = [
        ("hood",  [50, 50, 300, 200]),
        ("roof",  [350, 50, 700, 200]),
        ("door",  [50, 250, 500, 600]),
        ("trunk", [550, 250, 950, 600]),
    ]

    for name, bbox in panels:
        color = colors.get(name, (220, 220, 220, 255))
        draw.rectangle(bbox, fill=color, outline=(150, 150, 150, 255), width=2)
        cx = (bbox[0] + bbox[2]) // 2
        cy = (bbox[1] + bbox[3]) // 2
        draw.text((cx, cy), name.upper(), fill=(100, 100, 100, 255), anchor="mm")

    model_label = "Model 3" if model == "model3" else "Model Y"
    draw.text(
        (size // 2, size - 30),
        f"PLACEHOLDER — Replace with official {model_label} UV template",
        fill=(200, 50, 50, 255),
        anchor="mm",
    )
    return img


def create_pdf(template_png: Image.Image, output_path: Path) -> None:
    """Export a PIL image as a single-page A4 PDF."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import io
    buf = io.BytesIO()
    template_png.save(buf, format="PNG")
    buf.seek(0)

    c = rl_canvas.Canvas(str(output_path), pagesize=A4)
    reader = ImageReader(buf)
    c.drawImage(reader, 0, 0, width=PAGE_W, height=PAGE_H)
    c.save()
    print(f"  PDF saved: {output_path}")


def main(args=None):
    parser = argparse.ArgumentParser(description="Generate Kids Tesla Art templates")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["model3", "modely"],
        help="Model IDs to generate templates for",
    )
    opts = parser.parse_args(args)

    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    UV_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for model in opts.models:
        print(f"\nGenerating templates for: {model}")

        uv_path = UV_OUTPUT_DIR / f"{model}.png"
        if not uv_path.exists():
            print(f"  WARNING: {uv_path} not found.")
            print(f"  Download the official UV template from https://github.com/teslamotors/custom-wraps")
            print(f"  The PDF will be generated with a placeholder.")
        else:
            print(f"  Using UV template: {uv_path}")

        print("  Generating printable template PDF...")
        template_png = generate_template_png(model)

        pdf_path = PDF_OUTPUT_DIR / f"{model}-template.pdf"
        create_pdf(template_png, pdf_path)

    print("\nDone! PDF templates generated.")


if __name__ == "__main__":
    main()
