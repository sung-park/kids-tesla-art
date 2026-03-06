"""Tests for template generation script."""

import io
import pytest
from pathlib import Path
from PIL import Image
from unittest.mock import patch, MagicMock


class TestGenerateTemplatePng:
    def test_returns_pil_image(self):
        from scripts.generate_templates import generate_template_png
        result = generate_template_png("model3", page_w_px=620, page_h_px=877)
        assert isinstance(result, Image.Image)

    def test_correct_dimensions(self):
        from scripts.generate_templates import generate_template_png
        result = generate_template_png("model3", page_w_px=620, page_h_px=877)
        assert result.size == (620, 877)

    def test_mode_is_rgb(self):
        from scripts.generate_templates import generate_template_png
        result = generate_template_png("model3", page_w_px=620, page_h_px=877)
        assert result.mode == "RGB"


class TestGenerateUvTemplatePlaceholder:
    def test_returns_rgba_image(self):
        from scripts.generate_templates import generate_uv_template_placeholder
        result = generate_uv_template_placeholder("model3")
        assert isinstance(result, Image.Image)
        assert result.mode == "RGBA"

    def test_correct_default_size(self):
        from scripts.generate_templates import generate_uv_template_placeholder
        result = generate_uv_template_placeholder("model3", size=512)
        assert result.size == (512, 512)


class TestSanitisedFilename:
    def test_model3_pdf_filename(self):
        from scripts.generate_templates import PDF_OUTPUT_DIR
        path = PDF_OUTPUT_DIR / "model3-template.pdf"
        assert path.name == "model3-template.pdf"

    def test_modely_uv_filename(self):
        from scripts.generate_templates import UV_OUTPUT_DIR
        path = UV_OUTPUT_DIR / "modely.png"
        assert path.name == "modely.png"


class TestMain:
    def test_main_creates_files(self, tmp_path):
        from scripts import generate_templates as gt

        pdf_dir = tmp_path / "pdfs"
        uv_dir = tmp_path / "uv"

        with (
            patch.object(gt, "PDF_OUTPUT_DIR", pdf_dir),
            patch.object(gt, "UV_OUTPUT_DIR", uv_dir),
            patch.object(gt, "create_pdf") as mock_pdf,
        ):
            gt.main(["--models", "model3"])

        mock_pdf.assert_called_once()
        uv_files = list(uv_dir.glob("*.png"))
        assert len(uv_files) == 1
        assert uv_files[0].name == "model3.png"
