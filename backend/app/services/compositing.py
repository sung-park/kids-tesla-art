"""Composite drawing onto Tesla UV template and optimise to ≤1MB PNG."""

import io
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.services.panel_map import load_panels, composite_with_panels

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
    panels = load_panels(model)

    drawing = np.array(
        Image.fromarray(drawing_rgba, mode="RGBA").resize(
            (OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS
        )
    )

    composited = composite_with_panels(drawing, uv_template, panels)
    rgba_img = Image.fromarray(composited)
    white_bg = Image.new("RGBA", rgba_img.size, (255, 255, 255, 255))
    final = Image.alpha_composite(white_bg, rgba_img).convert("RGB")

    png_bytes = _compress_to_limit(final)
    safe_name = _sanitise_filename(original_filename)

    return png_bytes, safe_name


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
