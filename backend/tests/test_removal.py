"""Tests for background removal service."""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io


def make_rgba_array(size: int = 64) -> np.ndarray:
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :] = (200, 150, 100, 255)
    return arr


class TestGetSession:
    def test_returns_session_singleton(self):
        from app.services.removal import get_session
        import app.services.removal as removal_mod

        removal_mod._session = None  # reset

        with patch("app.services.removal.new_session") as mock_new:
            mock_session = MagicMock()
            mock_new.return_value = mock_session

            s1 = get_session()
            s2 = get_session()

        mock_new.assert_called_once_with("u2net")
        assert s1 is s2

        removal_mod._session = None  # cleanup


class TestRemoveBackground:
    def test_returns_rgba_array_of_same_dimensions(self):
        input_arr = make_rgba_array(64)

        mock_result = Image.new("RGBA", (64, 64), (100, 100, 100, 0))
        buf = io.BytesIO()
        mock_result.save(buf, format="PNG")
        mock_png_bytes = buf.getvalue()

        with patch("app.services.removal.get_session") as mock_get, \
             patch("app.services.removal.remove") as mock_remove:
            mock_get.return_value = MagicMock()
            mock_remove.return_value = mock_png_bytes

            from app.services.removal import remove_background
            result = remove_background(input_arr)

        assert result.shape == (64, 64, 4)
        assert result.dtype == np.uint8

    def test_remove_called_with_session(self):
        input_arr = make_rgba_array(32)

        mock_result = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        buf = io.BytesIO()
        mock_result.save(buf, format="PNG")
        mock_png_bytes = buf.getvalue()

        mock_session = MagicMock()

        with patch("app.services.removal.get_session", return_value=mock_session), \
             patch("app.services.removal.remove", return_value=mock_png_bytes) as mock_remove:
            from app.services.removal import remove_background
            remove_background(input_arr)

        mock_remove.assert_called_once()
        _, kwargs = mock_remove.call_args
        assert kwargs.get("session") is mock_session
