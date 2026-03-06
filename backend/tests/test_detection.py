"""Tests for ArUco marker detection and perspective warp."""

import cv2
import numpy as np
import pytest

from app.services.detection import (
    detect_and_warp,
    MarkerDetectionError,
    ARUCO_DICT,
)

OUTPUT_SIZE = 1024  # default from detect_and_warp signature


def _generate_template_image(
    size: int = 800, marker_size: int = 60
) -> np.ndarray:
    """Generate a synthetic test image with 4 ArUco markers at corners.

    Returns a BGR numpy array with markers at IDs 0,1,2,3.
    """
    image = np.ones((size, size, 3), dtype=np.uint8) * 255  # white background
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    margin = 20

    # Positions: TL, TR, BR, BL
    positions = [
        (margin, margin),
        (size - margin - marker_size, margin),
        (size - margin - marker_size, size - margin - marker_size),
        (margin, size - margin - marker_size),
    ]

    for marker_id, (x, y) in enumerate(positions):
        marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
        image[y : y + marker_size, x : x + marker_size] = cv2.cvtColor(
            marker_img, cv2.COLOR_GRAY2BGR
        )

    return image


class TestDetectAndWarp:
    def test_returns_correct_output_shape(self):
        image = _generate_template_image()
        result = detect_and_warp(image)
        assert result.shape == (OUTPUT_SIZE, OUTPUT_SIZE, 4)
        assert result.dtype == np.uint8

    def test_raises_when_no_markers(self):
        blank = np.ones((800, 800, 3), dtype=np.uint8) * 255
        with pytest.raises(MarkerDetectionError, match="0 of 4"):
            detect_and_warp(blank)

    def test_raises_when_only_some_markers_present(self):
        """Image with only markers 0 and 1 (top row only)."""
        size = 800
        marker_size = 60
        image = np.ones((size, size, 3), dtype=np.uint8) * 255
        aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
        margin = 20

        for marker_id, (x, y) in enumerate(
            [(margin, margin), (size - margin - marker_size, margin)]
        ):
            marker_img = cv2.aruco.generateImageMarker(
                aruco_dict, marker_id, marker_size
            )
            image[y : y + marker_size, x : x + marker_size] = cv2.cvtColor(
                marker_img, cv2.COLOR_GRAY2BGR
            )

        with pytest.raises(MarkerDetectionError):
            detect_and_warp(image)

    def test_output_is_rgba(self):
        image = _generate_template_image()
        result = detect_and_warp(image)
        # RGBA = 4 channels
        assert result.shape[2] == 4

    def test_custom_output_size(self):
        image = _generate_template_image()
        result = detect_and_warp(image, output_size=512)
        assert result.shape == (512, 512, 4)

    def test_error_message_is_descriptive(self):
        blank = np.ones((800, 800, 3), dtype=np.uint8) * 255
        with pytest.raises(MarkerDetectionError) as exc_info:
            detect_and_warp(blank)
        assert "marker" in str(exc_info.value).lower()
