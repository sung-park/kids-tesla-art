"""Background removal using color thresholding.

Instead of neural-network-based rembg (designed for natural photos),
we use simple HSV thresholding to detect and remove the white paper background.
This is faster (<100ms vs 30-60s), more accurate for colored templates,
and avoids ARM64 compatibility issues with ONNX Runtime.
"""

import cv2
import numpy as np


def remove_background(rgba_image: np.ndarray) -> np.ndarray:
    """Remove the white paper background from a perspective-corrected RGBA image.

    Detects white/near-white pixels (high brightness + low saturation)
    and makes them transparent, preserving crayon/marker coloring.

    Args:
        rgba_image: Input image as a numpy array (H x W x 4, RGBA).

    Returns:
        RGBA numpy array with background pixels made transparent.
    """
    rgb = rgba_image[:, :, :3]

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    is_white = (gray > 230) & (hsv[:, :, 1] < 30)

    alpha = np.where(is_white, 0, 255).astype(np.uint8)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    result = rgba_image.copy()
    result[:, :, 3] = alpha
    return result
