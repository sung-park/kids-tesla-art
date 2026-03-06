"""Per-panel perspective warp: kid-template space → UV space compositing."""

import json
from pathlib import Path

import cv2
import numpy as np

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
UV_SIZE = 1024


def load_panels(model: str) -> list[dict]:
    path = TEMPLATES_DIR / f"{model}_panels.json"
    if not path.exists():
        raise ValueError(f"Panel map not found for model '{model}': {path}")
    return json.loads(path.read_text())["panels"]


def composite_with_panels(
    kid_drawing: np.ndarray,
    uv_template: np.ndarray,
    panels: list[dict],
) -> np.ndarray:
    """Warp each panel region from kid-template space into UV space and composite.

    Args:
        kid_drawing: RGBA numpy array (1024x1024) — warped photo of kid's coloring.
        uv_template: RGBA numpy array (1024x1024) — Tesla UV template base.
        panels: Panel list from load_panels().

    Returns:
        RGBA numpy array (1024x1024) with kid's coloring composited onto UV template.
    """
    result = uv_template.astype(np.float32)

    for panel in panels:
        kid_quad = np.float32(panel["kid_quad"])
        uv_quad = np.float32(panel["uv_quad"])

        M = cv2.getPerspectiveTransform(kid_quad, uv_quad)
        warped = cv2.warpPerspective(
            kid_drawing.astype(np.float32),
            M,
            (UV_SIZE, UV_SIZE),
            flags=cv2.INTER_LINEAR,
        )

        # Only composite where the kid's drawing has painted pixels (alpha > 0)
        # and where the UV template has a paintable (white-ish) surface.
        alpha = warped[:, :, 3:4] / 255.0

        # Restrict compositing to within UV panel region to avoid bleed
        panel_mask = np.zeros((UV_SIZE, UV_SIZE, 1), dtype=np.float32)
        uv_pts = uv_quad.astype(np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(panel_mask, [uv_pts], (1.0,))

        combined_alpha = alpha * panel_mask
        result = result * (1.0 - combined_alpha) + warped * combined_alpha

    return np.clip(result, 0, 255).astype(np.uint8)
