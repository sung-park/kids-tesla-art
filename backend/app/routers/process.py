"""POST /api/process — main image processing endpoint."""

import io
import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image

from app.services.detection import detect_and_warp, MarkerDetectionError
from app.services.removal import remove_background
from app.services.compositing import composite_and_optimise

router = APIRouter()

SUPPORTED_MODELS = {"model3", "modely"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20MB


def _decode_image(data: bytes) -> np.ndarray:
    """Decode image bytes to a BGR numpy array."""
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        # Fallback via Pillow (handles HEIC/HEIF on some systems)
        try:
            pil = Image.open(io.BytesIO(data)).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="Could not decode image. Please upload a JPEG, PNG, or WEBP file.",
            ) from exc
    return img


@router.post("/process")
async def process_image(
    image: UploadFile = File(..., description="Photo of the colored template"),
    model: str = Form(..., description="Tesla model id: model3 or modely"),
):
    """Process a photo of a colored template and return a Tesla-ready wrap PNG."""

    if model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model '{model}'. Choose from: {sorted(SUPPORTED_MODELS)}",
        )

    content_type = image.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are accepted.",
        )

    raw_bytes = await image.read()
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum upload size is 20MB.",
        )

    try:
        image_bgr = _decode_image(raw_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Failed to read image.") from exc

    try:
        warped_rgba = detect_and_warp(image_bgr)
    except MarkerDetectionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Marker detection failed unexpectedly."
        ) from exc

    try:
        drawing_rgba = remove_background(warped_rgba)
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Background removal failed."
        ) from exc

    try:
        png_bytes, safe_filename = composite_and_optimise(
            drawing_rgba,
            model,
            original_filename=image.filename or "drawing",
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Image compositing failed."
        ) from exc

    return StreamingResponse(
        io.BytesIO(png_bytes),
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Content-Length": str(len(png_bytes)),
        },
    )
