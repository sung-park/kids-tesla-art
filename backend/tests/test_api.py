"""Integration tests for the FastAPI endpoints."""

import io
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def make_jpeg_bytes(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color=(180, 120, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png_bytes(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color=(100, 200, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_output_rgba(size: int = 1024) -> np.ndarray:
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :] = (200, 100, 50, 255)
    return arr


def make_output_png() -> bytes:
    img = Image.new("RGB", (1024, 1024), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


class TestHealthEndpoint:
    def test_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestTemplatesEndpoint:
    def test_returns_model_list(self, client):
        resp = client.get("/api/templates")
        assert resp.status_code == 200
        data = resp.json()
        model_ids = [m["id"] for m in data["models"]]
        assert "model3" in model_ids
        assert "modely" in model_ids


class TestProcessEndpoint:
    def _mock_pipeline(self):
        """Context manager that mocks the entire processing pipeline."""
        rgba = make_output_rgba()
        png_bytes = make_output_png()
        return (
            patch("app.routers.process.detect_and_warp", return_value=rgba),
            patch("app.routers.process.remove_background", return_value=rgba),
            patch(
                "app.routers.process.composite_and_optimise",
                return_value=(png_bytes, "test-wrap.png"),
            ),
        )

    def test_success_returns_png(self, client):
        with (
            patch("app.routers.process.detect_and_warp", return_value=make_output_rgba()),
            patch("app.routers.process.remove_background", return_value=make_output_rgba()),
            patch("app.routers.process.composite_and_optimise", return_value=(make_output_png(), "test-wrap.png")),
        ):
            resp = client.post(
                "/api/process",
                files={"image": ("photo.jpg", make_jpeg_bytes(), "image/jpeg")},
                data={"model": "model3"},
            )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert "test-wrap.png" in resp.headers["content-disposition"]

    def test_invalid_model_returns_400(self, client):
        resp = client.post(
            "/api/process",
            files={"image": ("photo.jpg", make_jpeg_bytes(), "image/jpeg")},
            data={"model": "cybertruck"},
        )
        assert resp.status_code == 400
        assert "cybertruck" in resp.json()["detail"].lower()

    def test_non_image_file_returns_400(self, client):
        resp = client.post(
            "/api/process",
            files={"image": ("doc.pdf", b"pdf-data", "application/pdf")},
            data={"model": "model3"},
        )
        assert resp.status_code == 400

    def test_marker_detection_failure_returns_422(self, client):
        from app.services.detection import MarkerDetectionError

        with patch(
            "app.routers.process.detect_and_warp",
            side_effect=MarkerDetectionError("Only 2 of 4 alignment markers detected."),
        ):
            resp = client.post(
                "/api/process",
                files={"image": ("photo.jpg", make_jpeg_bytes(), "image/jpeg")},
                data={"model": "model3"},
            )
        assert resp.status_code == 422
        assert "marker" in resp.json()["detail"].lower()

    def test_file_too_large_returns_413(self, client):
        large_bytes = b"x" * (21 * 1024 * 1024)
        resp = client.post(
            "/api/process",
            files={"image": ("big.jpg", large_bytes, "image/jpeg")},
            data={"model": "model3"},
        )
        assert resp.status_code == 413

    def test_png_upload_also_works(self, client):
        with (
            patch("app.routers.process.detect_and_warp", return_value=make_output_rgba()),
            patch("app.routers.process.remove_background", return_value=make_output_rgba()),
            patch("app.routers.process.composite_and_optimise", return_value=(make_output_png(), "test-wrap.png")),
        ):
            resp = client.post(
                "/api/process",
                files={"image": ("art.png", make_png_bytes(), "image/png")},
                data={"model": "modely"},
            )
        assert resp.status_code == 200

    def test_background_removal_error_returns_500(self, client):
        with (
            patch("app.routers.process.detect_and_warp", return_value=make_output_rgba()),
            patch("app.routers.process.remove_background", side_effect=RuntimeError("ONNX error")),
        ):
            resp = client.post(
                "/api/process",
                files={"image": ("photo.jpg", make_jpeg_bytes(), "image/jpeg")},
                data={"model": "model3"},
            )
        assert resp.status_code == 500
        assert "background" in resp.json()["detail"].lower()
