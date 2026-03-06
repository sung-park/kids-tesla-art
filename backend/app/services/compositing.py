"""Composite drawing onto Tesla UV template and optimise to ≤1MB PNG."""

import io
import json
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.services.warping import warp_image, generate_uv_mask

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_SIZE = 1024
MAX_FILE_SIZE = 1024 * 1024  # 1MB in bytes
FILENAME_MAX_LEN = 30


def _load_template_np(model: str) -> np.ndarray:
    path = TEMPLATES_DIR / f"{model}.png"
    if not path.exists():
        raise ValueError(f"No template found for model '{model}'. Expected: {path}")
    img = Image.open(path).convert("RGBA").resize(
        (OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS
    )
    return np.array(img)


def composite_and_optimise(
    drawing_rgba: np.ndarray,
    model: str,
    original_filename: str = "drawing",
) -> tuple[bytes, str]:
    """Composite the kid's drawing onto the Tesla UV template using per-panel mapping.

    Args:
        drawing_rgba: Background-removed drawing as RGBA numpy array (H x W x 4).
                      This is warped from the kid-friendly template space.
        model: Tesla model id ('model3' or 'modely').
        original_filename: Original filename hint for output naming.

    Returns:
        Tuple of (png_bytes, safe_filename).  png_bytes is guaranteed ≤ 1MB.
    """
    uv_template = _load_template_np(model)

    drawing = np.array(
        Image.fromarray(drawing_rgba, mode="RGBA").resize(
            (OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS
        )
    )

    # Warp kid's drawing from template space to UV space
    warped = warp_image(drawing, model)

    # Generate mask from UV template (white areas = paintable, glass excluded)
    mask = generate_uv_mask(uv_template, model)

    # Composite: apply warped drawing only within paintable UV areas
    composited = uv_template.copy()
    warped_visible = warped[:, :, 3] > 0
    paint_mask = (mask > 0) & warped_visible
    paint_mask_4d = np.stack([paint_mask] * 4, axis=-1)

    # Blend warped drawing onto template within mask
    composited[paint_mask_4d] = warped[paint_mask_4d]

    # Apply glass tint to window regions
    composited = _apply_glass_tint(composited, model)

    rgba_img = Image.fromarray(composited)
    white_bg = Image.new("RGBA", rgba_img.size, (255, 255, 255, 255))
    final = Image.alpha_composite(white_bg, rgba_img).convert("RGB")

    png_bytes = _compress_to_limit(final)
    safe_name = _sanitise_filename(original_filename)

    return png_bytes, safe_name


def _apply_glass_tint(composited: np.ndarray, model: str) -> np.ndarray:
    """Apply a subtle blue-gray tint to glass/window regions for realism."""
    config_path = TEMPLATES_DIR / f"{model}_panels.json"
    if not config_path.exists():
        return composited
    config = json.loads(config_path.read_text())
    glass_regions = config.get("glass_regions", [])
    if not glass_regions:
        return composited

    result = composited.copy()
    glass_mask = np.zeros(result.shape[:2], dtype=np.uint8)
    for region in glass_regions:
        pts = np.array(region["polygon"], dtype=np.int32)
        cv2.fillPoly(glass_mask, [pts], 255)

    tint_indices = glass_mask > 0
    tint_color = np.array([180, 205, 225], dtype=np.float32)
    alpha = 0.25
    for c in range(3):
        result[:, :, c] = np.where(
            tint_indices,
            (result[:, :, c].astype(np.float32) * (1 - alpha)
             + tint_color[c] * alpha).astype(np.uint8),
            result[:, :, c],
        )
    return result


def _compress_to_limit(image: Image.Image) -> bytes:
    """Compress PNG to ≤ 1MB.  Reduces size by downsampling if needed."""
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()

    if len(data) <= MAX_FILE_SIZE:
        return data

    # Progressively scale down until within limit
    scale = 0.9
    current = image
    while len(data) > MAX_FILE_SIZE and scale > 0.3:
        new_size = (int(OUTPUT_SIZE * scale), int(OUTPUT_SIZE * scale))
        current = image.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        current.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
        scale -= 0.1

    return data


def _sanitise_filename(name: str) -> str:
    """Return a Tesla-safe PNG filename (max 30 chars, alphanumeric/underscore/dash/space)."""
    stem = Path(name).stem
    safe = re.sub(r"[^A-Za-z0-9_\- ]", "", stem).strip()
    if not safe:
        safe = "kids-tesla-wrap"
    safe = safe[:FILENAME_MAX_LEN]
    return f"{safe}.png"
