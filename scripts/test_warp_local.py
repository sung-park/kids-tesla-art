#!/usr/bin/env python3
"""Local test: generate kid template image → warp → composite → save output PNG.

Usage:
    cd backend && python ../scripts/test_warp_local.py
"""

import sys
from pathlib import Path

# Add backend to path
REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "backend"))

import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.services.warping import warp_image, generate_uv_mask, build_warp_maps, _warp_cache
from app.services.compositing import _load_template_np, _apply_glass_tint

OUTPUT_DIR = REPO / "scripts" / "test_output"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_SIZE = 1024


def generate_kid_template_image(model: str) -> np.ndarray:
    """Generate the kid template as a 1024x1024 RGBA image (what a kid's photo would capture)."""
    # Import the generate_templates module
    sys.path.insert(0, str(REPO / "scripts"))
    from generate_templates import generate_template_png, KID_SCALE_X, KID_SCALE_Y, DRAW_X0, DRAW_Y0

    # Generate the full-page template
    full_img = generate_template_png(model)

    # Crop to the drawable area (inside ArUco markers) and resize to 1024x1024
    # This simulates what the detection pipeline would extract
    from generate_templates import DRAW_X0, DRAW_Y0, DRAW_W, DRAW_H
    cropped = full_img.crop((DRAW_X0, DRAW_Y0, DRAW_X0 + DRAW_W, DRAW_Y0 + DRAW_H))
    resized = cropped.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)

    # Convert to RGBA
    rgba = resized.convert("RGBA")
    return np.array(rgba)


def run_test(model: str):
    print(f"\n=== Testing {model} ===")

    # Clear warp cache to pick up any changes
    _warp_cache.clear()

    # Step 1: Generate kid template image
    kid_img = generate_kid_template_image(model)
    kid_pil = Image.fromarray(kid_img)
    kid_pil.save(OUTPUT_DIR / f"{model}_kid_input.png")
    print(f"  Saved kid input: {OUTPUT_DIR / f'{model}_kid_input.png'}")

    # Step 2: Warp
    warped = warp_image(kid_img, model)
    warped_pil = Image.fromarray(warped)
    warped_pil.save(OUTPUT_DIR / f"{model}_warped.png")
    print(f"  Saved warped: {OUTPUT_DIR / f'{model}_warped.png'}")

    # Step 3: Load UV template
    uv_template = _load_template_np(model)

    # Step 4: Generate mask
    mask = generate_uv_mask(uv_template, model)
    mask_pil = Image.fromarray(mask)
    mask_pil.save(OUTPUT_DIR / f"{model}_mask.png")
    print(f"  Saved mask: {OUTPUT_DIR / f'{model}_mask.png'}")

    # Step 5: Composite
    composited = uv_template.copy()
    warped_visible = warped[:, :, 3] > 0
    paint_mask = (mask > 0) & warped_visible
    paint_mask_4d = np.stack([paint_mask] * 4, axis=-1)
    composited[paint_mask_4d] = warped[paint_mask_4d]

    # Step 6: Glass tint
    composited = _apply_glass_tint(composited, model)

    # Step 7: Save final
    rgba_img = Image.fromarray(composited)
    white_bg = Image.new("RGBA", rgba_img.size, (255, 255, 255, 255))
    final = Image.alpha_composite(white_bg, rgba_img).convert("RGB")
    final.save(OUTPUT_DIR / f"{model}_final.png")
    print(f"  Saved final: {OUTPUT_DIR / f'{model}_final.png'}")

    # Also save a debug overlay showing warp control points on UV
    save_debug_overlay(model, uv_template)


def save_debug_overlay(model: str, uv_template: np.ndarray):
    """Save debug image showing warp dst points on UV template."""
    import json
    warp_path = REPO / "backend" / "app" / "templates" / f"{model}_warp.json"
    config = json.loads(warp_path.read_text())

    debug = uv_template.copy()
    for region in config["regions"]:
        pts = region["dst_points"]
        for x, y in pts:
            x, y = int(x), int(y)
            cv2.circle(debug, (x, y), 5, (255, 0, 0, 255), -1)

    # Also draw glass regions
    panels_path = REPO / "backend" / "app" / "templates" / f"{model}_panels.json"
    panels_config = json.loads(panels_path.read_text())
    for glass in panels_config.get("glass_regions", []):
        pts = np.array(glass["polygon"], dtype=np.int32)
        cv2.polylines(debug, [pts], True, (0, 0, 255, 255), 2)

    debug_pil = Image.fromarray(debug)
    debug_pil.save(OUTPUT_DIR / f"{model}_debug_overlay.png")
    print(f"  Saved debug overlay: {OUTPUT_DIR / f'{model}_debug_overlay.png'}")


if __name__ == "__main__":
    models = sys.argv[1:] if len(sys.argv) > 1 else ["model3", "modely"]
    for m in models:
        run_test(m)
    print(f"\nAll outputs in: {OUTPUT_DIR}")
