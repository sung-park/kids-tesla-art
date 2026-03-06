"""Tests for compositing service."""

import io
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from app.services.compositing import (
    composite_and_optimise,
    _sanitise_filename,
    _compress_to_limit,
    MAX_FILE_SIZE,
    OUTPUT_SIZE,
)


def make_rgba_array(size: int = 64, color=(255, 0, 0, 255)) -> np.ndarray:
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :] = color
    return arr


def make_template_image(size: int = OUTPUT_SIZE) -> Image.Image:
    return Image.new("RGBA", (size, size), color=(200, 200, 200, 255))


def _mock_warp_image(src_image, model):
    return src_image.copy()


def _mock_generate_uv_mask(uv_template):
    return np.full(uv_template.shape[:2], 255, dtype=np.uint8)


class TestSanitiseFilename:
    def test_removes_special_characters(self):
        result = _sanitise_filename("my photo!@#$.jpg")
        assert result == "my photo.png"

    def test_truncates_to_30_chars(self):
        long_name = "a" * 50 + ".jpg"
        result = _sanitise_filename(long_name)
        assert len(result) <= 30 + 4  # 30 chars + ".png"
        assert result.endswith(".png")

    def test_fallback_for_empty_stem(self):
        result = _sanitise_filename("!!!")
        assert result == "kids-tesla-wrap.png"

    def test_preserves_valid_chars(self):
        result = _sanitise_filename("kids-art_v2 final.jpg")
        assert result == "kids-art_v2 final.png"

    def test_handles_no_extension(self):
        result = _sanitise_filename("myfile")
        assert result == "myfile.png"


class TestCompressToLimit:
    def test_small_image_passes_unchanged_size_constraint(self):
        img = Image.new("RGB", (64, 64), color=(255, 0, 0))
        data = _compress_to_limit(img)
        assert len(data) <= MAX_FILE_SIZE

    def test_output_is_valid_png(self):
        img = Image.new("RGB", (64, 64), color=(100, 150, 200))
        data = _compress_to_limit(img)
        result = Image.open(io.BytesIO(data))
        assert result.format == "PNG"


class TestCompositeAndOptimise:
    def _patch_warping(self):
        return [
            patch("app.services.compositing.warp_image", side_effect=_mock_warp_image),
            patch("app.services.compositing.generate_uv_mask", side_effect=_mock_generate_uv_mask),
        ]

    def test_returns_valid_png_bytes_and_safe_filename(self, tmp_path):
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template = make_template_image()
        template.save(template_path / "model3.png")

        drawing = make_rgba_array(OUTPUT_SIZE)

        with patch("app.services.compositing.TEMPLATES_DIR", template_path):
            for p in self._patch_warping():
                p.start()
            try:
                png_bytes, filename = composite_and_optimise(
                    drawing, "model3", "my_drawing.jpg"
                )
            finally:
                patch.stopall()

        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0
        assert len(png_bytes) <= MAX_FILE_SIZE
        img = Image.open(io.BytesIO(png_bytes))
        assert img.format == "PNG"

        assert filename.endswith(".png")
        assert len(filename) <= 34  # 30 + ".png"

    def test_no_black_background_in_output(self, tmp_path):
        template_path = tmp_path / "templates"
        template_path.mkdir()
        template = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), (0, 0, 0, 0))
        template.save(template_path / "model3.png")

        drawing = make_rgba_array(OUTPUT_SIZE, color=(0, 0, 0, 0))

        with patch("app.services.compositing.TEMPLATES_DIR", template_path):
            for p in self._patch_warping():
                p.start()
            try:
                png_bytes, _ = composite_and_optimise(drawing, "model3", "test.jpg")
            finally:
                patch.stopall()

        img = Image.open(io.BytesIO(png_bytes))
        pixels = np.array(img)
        assert pixels.mean() > 200

    def test_raises_for_unknown_model(self):
        drawing = make_rgba_array()
        with pytest.raises(ValueError, match="No template found"):
            composite_and_optimise(drawing, "cybertruck")

    def test_filename_sanitised_in_output(self, tmp_path):
        template_path = tmp_path / "templates"
        template_path.mkdir()
        make_template_image().save(template_path / "modely.png")

        drawing = make_rgba_array(OUTPUT_SIZE)
        with patch("app.services.compositing.TEMPLATES_DIR", template_path):
            for p in self._patch_warping():
                p.start()
            try:
                _, filename = composite_and_optimise(
                    drawing, "modely", "photo (1)!.jpg"
                )
            finally:
                patch.stopall()
        assert "!" not in filename
        assert filename.endswith(".png")
