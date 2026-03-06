# Kids Tesla Art — Backend Dockerfile
#
# IMPORTANT: We install rembg via pip (NOT using the official danielgatis/rembg
# Docker image) because the official image dropped ARM64 support in March 2025.
# This Dockerfile works on both linux/amd64 and linux/arm64 (OCI Ampere A1).

FROM python:3.11-slim AS base

WORKDIR /app

# System dependencies required by OpenCV and rembg/onnxruntime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the U2Net model at build time so the first request is fast.
# The model is cached in /root/.u2net/ inside the image (~176MB).
RUN python -c "from rembg import new_session; new_session('u2net'); print('U2Net model loaded OK')"

# Copy application code
COPY app/ ./app/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
