"""Tests for piecewise affine warping service."""

import numpy as np
import pytest

from app.services.warping import (
    build_warp_maps,
    warp_image,
    generate_uv_mask,
    _delaunay_triangles,
    _warp_cache,
    UV_SIZE,
)


def make_rgba_array(size: int = UV_SIZE, color=(200, 50, 50, 255)) -> np.ndarray:
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :] = color
    return arr


class TestDelaunayTriangles:
    def test_returns_triangle_indices(self):
        pts = np.float32([
            [100, 100], [500, 100], [900, 100],
            [100, 500], [500, 500], [900, 500],
        ])
        triangles = _delaunay_triangles(pts)
        assert len(triangles) > 0
        assert triangles.shape[1] == 3
        assert triangles.max() < len(pts)

    def test_min_three_points_needed(self):
        pts = np.float32([[100, 100], [500, 500]])
        triangles = _delaunay_triangles(pts)
        assert len(triangles) == 0


class TestBuildWarpMaps:
    def setup_method(self):
        _warp_cache.clear()

    def test_returns_correct_shape_model3(self):
        mapx, mapy = build_warp_maps("model3")
        assert mapx.shape == (UV_SIZE, UV_SIZE)
        assert mapy.shape == (UV_SIZE, UV_SIZE)
        assert mapx.dtype == np.float32

    def test_returns_correct_shape_modely(self):
        mapx, mapy = build_warp_maps("modely")
        assert mapx.shape == (UV_SIZE, UV_SIZE)
        assert mapy.shape == (UV_SIZE, UV_SIZE)

    def test_caches_results(self):
        mapx1, _ = build_warp_maps("model3")
        mapx2, _ = build_warp_maps("model3")
        assert mapx1 is mapx2

    def test_has_valid_mappings(self):
        mapx, mapy = build_warp_maps("model3")
        valid = mapx >= 0
        assert valid.sum() > 0

    def test_raises_for_unknown_model(self):
        with pytest.raises(ValueError, match="Warp config not found"):
            build_warp_maps("cybertruck")


class TestWarpImage:
    def setup_method(self):
        _warp_cache.clear()

    def test_returns_correct_shape(self):
        src = make_rgba_array()
        result = warp_image(src, "model3")
        assert result.shape == (UV_SIZE, UV_SIZE, 4)
        assert result.dtype == np.uint8

    def test_warps_colored_pixels_to_uv_regions(self):
        src = make_rgba_array(color=(255, 0, 0, 255))
        result = warp_image(src, "model3")
        # Left UV column (x:14-278) should have red content from left side mapping
        left_col = result[131:994, 14:278, :]
        has_red = (left_col[:, :, 0] > 200) & (left_col[:, :, 3] > 0)
        assert has_red.sum() > 0

    def test_transparent_input_produces_transparent_output(self):
        src = make_rgba_array(color=(0, 0, 0, 0))
        result = warp_image(src, "model3")
        assert result[:, :, 3].max() == 0


class TestGenerateUvMask:
    def test_returns_single_channel(self):
        template = np.full((100, 100, 4), 255, dtype=np.uint8)
        mask = generate_uv_mask(template)
        assert mask.shape == (100, 100)
        assert mask.dtype == np.uint8

    def test_white_areas_are_paintable(self):
        template = np.full((100, 100, 4), 255, dtype=np.uint8)
        mask = generate_uv_mask(template)
        # Interior should be 255 (edges eroded)
        assert mask[10:90, 10:90].min() == 255

    def test_dark_areas_are_protected(self):
        template = np.zeros((100, 100, 4), dtype=np.uint8)
        template[:, :, 3] = 255  # Opaque black
        mask = generate_uv_mask(template)
        assert mask.max() == 0

    def test_transparent_areas_are_protected(self):
        template = np.full((100, 100, 4), 255, dtype=np.uint8)
        template[:, :, 3] = 0  # Fully transparent white
        mask = generate_uv_mask(template)
        assert mask.max() == 0
