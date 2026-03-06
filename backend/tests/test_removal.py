"""Tests for threshold-based background removal service."""

import numpy as np

from app.services.removal import remove_background


def make_rgba_array(size: int = 64, color=(200, 150, 100, 255)) -> np.ndarray:
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :] = color
    return arr


class TestRemoveBackground:
    def test_returns_rgba_array_of_same_dimensions(self):
        input_arr = make_rgba_array(64)
        result = remove_background(input_arr)
        assert result.shape == (64, 64, 4)
        assert result.dtype == np.uint8

    def test_white_pixels_become_transparent(self):
        white_arr = make_rgba_array(32, color=(255, 255, 255, 255))
        result = remove_background(white_arr)
        assert result[:, :, 3].max() == 0

    def test_colored_pixels_remain_opaque(self):
        colored_arr = make_rgba_array(32, color=(200, 50, 50, 255))
        result = remove_background(colored_arr)
        assert result[:, :, 3].min() > 200

    def test_near_white_is_transparent(self):
        near_white = make_rgba_array(32, color=(240, 238, 235, 255))
        result = remove_background(near_white)
        assert result[:, :, 3].max() < 30

    def test_preserves_rgb_channels(self):
        input_arr = make_rgba_array(32, color=(100, 150, 200, 255))
        result = remove_background(input_arr)
        np.testing.assert_array_equal(result[:, :, :3], input_arr[:, :, :3])

    def test_mixed_image(self):
        arr = np.zeros((64, 64, 4), dtype=np.uint8)
        arr[:32, :, :] = (255, 255, 255, 255)
        arr[32:, :, :] = (255, 0, 0, 255)
        result = remove_background(arr)
        # Interior white region (away from edge) should be transparent
        assert result[:30, :, 3].max() == 0
        # Interior red region (away from edge) should be opaque
        assert result[34:, :, 3].min() > 200
