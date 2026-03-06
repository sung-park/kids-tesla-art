"""Composite drawing onto Tesla UV template and optimise to ≤1MB PNG."""

import io
import re
from pathlib import Path

import numpy as np
from PIL import Image

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_SIZE = 1024
MAX_FILE_SIZE = 1024 * 1024  # 1MB in bytes
FILENAME_MAX_LEN = 30


def _load_template(model: str) -> Image.Image:
    """Load the Tesla UV template PNG for the given model id.

    Args:
        model: One of 'model3' or 'modely'.

    Returns:
        PIL Image in RGBA mode, resized to OUTPUT_SIZE x OUTPUT_SIZE.

    Raises:
        ValueError: If the model is unsupported or the template file is missing.
    """
    path = TEMPLATES_DIR / f"{model}.png"
    if not path.exists():
        raise ValueError(f"No template found for model '{model}'. Expected: {path}")

    template = Image.open(path).convert("RGBA").resize(
        (OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS
    )
    return template


def composite_and_optimise(
    drawing_rgba: np.ndarray,
    model: str,
    original_filename: str = "drawing",
) -> tuple[bytes, str]:
    """Composite the drawing onto the Tesla template and return an optimised PNG.

    Args:
        drawing_rgba: Background-removed drawing as RGBA numpy array (H x W x 4).
        model: Tesla model id ('model3' or 'modely').
        original_filename: Original filename hint for output naming.

    Returns:
        Tuple of (png_bytes, safe_filename).  png_bytes is guaranteed ≤ 1MB.
    """
    template = _load_template(model)

    drawing = Image.fromarray(drawing_rgba, mode="RGBA").resize(
        (OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS
    )

    # Composite: paste drawing over template using drawing's alpha as mask
    result = template.copy()
    result.paste(drawing, (0, 0), mask=drawing)

    # Convert to RGB for final PNG (Tesla does not use alpha)
    final = result.convert("RGB")

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
