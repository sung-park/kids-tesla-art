#!/usr/bin/env python3
"""Generate printable PDF templates with ArUco markers for Kids Tesla Art.

Each template is an A4 page containing:
  - A simplified Tesla silhouette outline (coloring-book style) in the center
  - 4 ArUco markers (DICT_4X4_50, IDs 0-3) at the corners

Marker placement convention:
  - ID 0 → top-left
  - ID 1 → top-right
  - ID 2 → bottom-right
  - ID 3 → bottom-left

The inner corner of each marker defines the bounding rectangle of the drawing area.

Usage:
    pip install opencv-contrib-python Pillow reportlab
    python scripts/generate_templates.py

Outputs:
    frontend/public/templates/model3-template.pdf
    frontend/public/templates/modely-template.pdf
    backend/app/templates/model3.png    (UV template placeholders)
    backend/app/templates/modely.png
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


def _draw_tesla_silhouette(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    """Draw a simplified Tesla car silhouette outline inside the given bounding box."""
    # Scale factors
    sx = w / 200.0
    sy = h / 100.0

    def s(px, py):
        return (int(x + px * sx), int(y + py * sy))

    # Car body outline (simplified coupe shape)
    body = [
        s(10, 80), s(10, 60), s(30, 35), s(70, 20), s(130, 20),
        s(170, 35), s(190, 60), s(190, 80),
    ]
    draw.polygon(body, outline=(50, 50, 50), fill=(240, 240, 240))

    # Roof
    roof = [s(40, 60), s(55, 30), s(145, 30), s(160, 60)]
    draw.polygon(roof, outline=(50, 50, 50), fill=(220, 220, 220))

    # Wheels
    wheel_color = (80, 80, 80)
    draw.ellipse([s(30, 72), s(65, 95)], outline=wheel_color, fill=(150, 150, 150), width=2)
    draw.ellipse([s(135, 72), s(170, 95)], outline=wheel_color, fill=(150, 150, 150), width=2)

    # Window divider line
    draw.line([s(100, 30), s(100, 60)], fill=(100, 100, 100), width=2)


def generate_template_png(
    model: str,
    page_w_px: int = 2480,
    page_h_px: int = 3508,
) -> Image.Image:
    """Generate a full-page template image with ArUco markers and car silhouette.

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

    # Dashed border around drawing area
    draw.rectangle([draw_x, draw_y, draw_x + draw_w, draw_y + draw_h],
                   outline=(180, 180, 180), width=3)

    # Car silhouette
    car_margin = 60
    _draw_tesla_silhouette(
        draw,
        draw_x + car_margin,
        draw_y + car_margin,
        draw_w - 2 * car_margin,
        draw_h - 2 * car_margin,
    )

    # Labels
    model_label = "Model 3" if model == "model3" else "Model Y"
    instructions = [
        f"Kids Tesla Art — {model_label} Template",
        "Color inside the outline. Use crayons, markers, or watercolors.",
        "Then take a photo and upload at kids-tesla-art.example.com",
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

        print("  Generating printable template PNG...")
        template_png = generate_template_png(model)

        pdf_path = PDF_OUTPUT_DIR / f"{model}-template.pdf"
        create_pdf(template_png, pdf_path)

        print("  Generating UV template placeholder...")
        uv_img = generate_uv_template_placeholder(model)
        uv_path = UV_OUTPUT_DIR / f"{model}.png"
        uv_img.save(uv_path)
        print(f"  UV template saved: {uv_path}")
        print(f"  NOTE: Replace {uv_path} with the official Tesla UV template from")
        print(f"        https://github.com/teslamotors/custom-wraps")

    print("\nDone! All templates generated.")
    print("\nIMPORTANT: The UV templates in backend/app/templates/ are placeholders.")
    print("Download the official templates from https://github.com/teslamotors/custom-wraps")
    print("and replace the files in backend/app/templates/")


if __name__ == "__main__":
    main()
