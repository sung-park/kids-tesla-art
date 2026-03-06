#!/usr/bin/env python3
"""Test: color each panel with a distinct solid color + arrow/text to check
mirroring and clipping issues.

Usage:
    cd backend && python ../scripts/test_colored_rect.py
"""

import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "backend"))

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.services.warping import warp_image, generate_uv_mask, _warp_cache
from app.services.compositing import _load_template_np, _apply_glass_tint

OUTPUT_DIR = REPO / "scripts" / "test_output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_SIZE = 1024

# Panel colors (R, G, B, A) - distinct per panel
PANEL_COLORS = {
    "left_front_fender":  (255, 80, 80, 255),    # red
    "left_front_door":    (80, 200, 80, 255),     # green
    "left_rear_door":     (80, 80, 255, 255),     # blue
    "left_rear_quarter":  (255, 200, 0, 255),     # yellow
    "hood":               (255, 128, 0, 255),     # orange
    "roof":               (128, 0, 255, 255),     # purple
    "trunk":              (0, 200, 200, 255),      # cyan
    "right_front_fender": (255, 80, 80, 255),     # red (same as left)
    "right_front_door":   (80, 200, 80, 255),     # green
    "right_rear_door":    (80, 80, 255, 255),     # blue
    "right_rear_quarter": (255, 200, 0, 255),     # yellow
}


def load_font(size):
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            pass
    return ImageFont.load_default()


def generate_colored_kid_template(model: str) -> np.ndarray:
    """Create a 1024x1024 kid template with each panel filled with a solid color
    and an arrow pointing RIGHT + panel label text."""
    import json

    panels_path = REPO / "backend" / "app" / "templates" / f"{model}_panels.json"
    config = json.loads(panels_path.read_text())

    img = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(28)
    small_font = load_font(18)

    for panel in config["panels"]:
        name = panel["name"]
        kq = panel["kid_quad"]
        color = PANEL_COLORS.get(name, (200, 200, 200, 255))

        x0 = min(pt[0] for pt in kq)
        y0 = min(pt[1] for pt in kq)
        x1 = max(pt[0] for pt in kq)
        y1 = max(pt[1] for pt in kq)

        # Fill rectangle
        draw.rectangle([x0, y0, x1, y1], fill=color)

        # Draw arrow pointing RIGHT (→) to detect mirroring
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        arrow_len = min(x1 - x0, y1 - y0) * 0.3
        # Arrow shaft
        draw.line([(cx - arrow_len, cy), (cx + arrow_len, cy)],
                  fill=(0, 0, 0, 255), width=3)
        # Arrow head
        draw.polygon([
            (cx + arrow_len, cy),
            (cx + arrow_len - 10, cy - 8),
            (cx + arrow_len - 10, cy + 8),
        ], fill=(0, 0, 0, 255))

        # Panel name label
        short = name.replace("left_", "L_").replace("right_", "R_")
        draw.text((cx, cy - 15), short, fill=(0, 0, 0, 255),
                  anchor="mm", font=small_font)

        # Draw "ABC" text to detect text mirroring
        draw.text((x0 + 10, y0 + 5), "ABC", fill=(0, 0, 0, 255), font=small_font)

    return np.array(img)


def run_test(model: str):
    print(f"\n=== Colored Rect Test: {model} ===")
    _warp_cache.clear()

    # Step 1: Generate colored kid template
    kid_img = generate_colored_kid_template(model)
    Image.fromarray(kid_img).save(OUTPUT_DIR / f"{model}_colored_kid.png")
    print(f"  Saved: {model}_colored_kid.png")

    # Step 2: Warp
    warped = warp_image(kid_img, model)
    Image.fromarray(warped).save(OUTPUT_DIR / f"{model}_colored_warped.png")
    print(f"  Saved: {model}_colored_warped.png")

    # Step 3: UV template + mask
    uv_template = _load_template_np(model)
    mask = generate_uv_mask(uv_template, model)
    Image.fromarray(mask).save(OUTPUT_DIR / f"{model}_colored_mask.png")
    print(f"  Saved: {model}_colored_mask.png")

    # Step 4: Composite
    composited = uv_template.copy()
    warped_visible = warped[:, :, 3] > 0
    paint_mask = (mask > 0) & warped_visible
    paint_mask_4d = np.stack([paint_mask] * 4, axis=-1)
    composited[paint_mask_4d] = warped[paint_mask_4d]
    composited = _apply_glass_tint(composited, model)

    # Step 5: Final with white bg
    rgba_img = Image.fromarray(composited)
    white_bg = Image.new("RGBA", rgba_img.size, (255, 255, 255, 255))
    final = Image.alpha_composite(white_bg, rgba_img).convert("RGB")
    final.save(OUTPUT_DIR / f"{model}_colored_final.png")
    print(f"  Saved: {model}_colored_final.png")

    # Step 6: Also save warped-only on white bg (no mask) to see raw warping
    warped_rgba = Image.fromarray(warped)
    white_bg2 = Image.new("RGBA", warped_rgba.size, (255, 255, 255, 255))
    raw = Image.alpha_composite(white_bg2, warped_rgba).convert("RGB")
    raw.save(OUTPUT_DIR / f"{model}_colored_warped_raw.png")
    print(f"  Saved: {model}_colored_warped_raw.png")


if __name__ == "__main__":
    models = sys.argv[1:] if len(sys.argv) > 1 else ["model3", "modely"]
    for m in models:
        run_test(m)
    print(f"\nAll outputs in: {OUTPUT_DIR}")
