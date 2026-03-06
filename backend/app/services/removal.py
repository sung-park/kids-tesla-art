"""Background removal using rembg (U2Net model).

The rembg session is expensive to create (~5s on first load) because it downloads
and initialises the ONNX model.  We create it once at application startup and
reuse it for all requests.
"""

import io
import numpy as np
from PIL import Image
from rembg import new_session, remove

_session = None


def get_session():
    """Return the singleton rembg session, creating it on first call."""
    global _session
    if _session is None:
        _session = new_session("u2net")
    return _session


def remove_background(rgba_image: np.ndarray) -> np.ndarray:
    """Remove the white/paper background from a perspective-corrected RGBA image.

    Args:
        rgba_image: Input image as a numpy array (H x W x 4, RGBA).

    Returns:
        RGBA numpy array with background pixels made transparent.
    """
    session = get_session()

    pil_image = Image.fromarray(rgba_image, mode="RGBA")
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    buf.seek(0)

    result_bytes = remove(buf.read(), session=session)

    result_image = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
    return np.array(result_image)
