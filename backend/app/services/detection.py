"""ArUco marker detection and perspective correction.

Template convention:
  - Dictionary: DICT_4X4_50
  - Marker IDs map to corners:
      0 → top-left
      1 → top-right
      2 → bottom-right
      3 → bottom-left
"""

import cv2
import numpy as np


ARUCO_DICT = cv2.aruco.DICT_4X4_50
MARKER_CORNER_MAP: dict[int, int] = {0: 0, 1: 1, 2: 2, 3: 3}
# Corner indices within each marker's corners array (returned as TL,TR,BR,BL):
# For a given corner of the template rectangle, use the nearest marker corner.
MARKER_INNER_CORNER: dict[int, int] = {
    0: 2,  # marker 0 (top-left of page)  → use its bottom-right corner
    1: 3,  # marker 1 (top-right of page) → use its bottom-left corner
    2: 0,  # marker 2 (bottom-right)      → use its top-left corner
    3: 1,  # marker 3 (bottom-left)       → use its top-right corner
}


class MarkerDetectionError(ValueError):
    pass


def _build_detector() -> cv2.aruco.ArucoDetector:
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    params = cv2.aruco.DetectorParameters()
    return cv2.aruco.ArucoDetector(aruco_dict, params)


_detector: cv2.aruco.ArucoDetector | None = None


def _get_detector() -> cv2.aruco.ArucoDetector:
    global _detector
    if _detector is None:
        _detector = _build_detector()
    return _detector


def detect_and_warp(
    image_bgr: np.ndarray,
    output_size: int = 1024,
) -> np.ndarray:
    """Detect ArUco markers and return a perspective-corrected RGBA crop.

    Args:
        image_bgr: Input image as a BGR numpy array (as read by cv2.imread).
        output_size: Side length of the square output image in pixels.

    Returns:
        Perspective-corrected RGBA image as a numpy array (H x W x 4).

    Raises:
        MarkerDetectionError: If fewer than 4 expected markers are detected.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # Enhance contrast for low-light photos
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    detector = _get_detector()
    corners, ids, _ = detector.detectMarkers(enhanced)

    if ids is None or len(ids) < 4:
        found = len(ids) if ids is not None else 0
        raise MarkerDetectionError(
            f"Only {found} of 4 alignment markers detected. "
            "Make sure all 4 corner markers are clearly visible and the photo is not blurry."
        )

    # Map detected marker IDs to template corners
    id_to_corners: dict[int, np.ndarray] = {}
    for corner_arr, marker_id in zip(corners, ids.flatten()):
        mid = int(marker_id)
        if mid in MARKER_CORNER_MAP:
            id_to_corners[mid] = corner_arr[0]  # shape (4, 2)

    missing = [mid for mid in range(4) if mid not in id_to_corners]
    if missing:
        raise MarkerDetectionError(
            f"Marker(s) with ID {missing} not detected. "
            "Ensure the printed template includes all 4 corner markers."
        )

    # Extract the specific inner corner point for each template corner
    src_pts = np.float32(
        [
            id_to_corners[mid][MARKER_INNER_CORNER[mid]]
            for mid in range(4)  # TL, TR, BR, BL
        ]
    )

    dst_pts = np.float32(
        [
            [0, 0],
            [output_size - 1, 0],
            [output_size - 1, output_size - 1],
            [0, output_size - 1],
        ]
    )

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_bgr = cv2.warpPerspective(image_bgr, M, (output_size, output_size))

    # Convert to RGBA
    warped_rgba = cv2.cvtColor(warped_bgr, cv2.COLOR_BGR2RGBA)
    return warped_rgba
