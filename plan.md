# Kids Tesla Art — Implementation Plan

## Overview

A stateless, open-source web application that transforms children's hand-drawn Tesla templates into custom Tesla Toybox wrap files. No database, no user accounts — process in memory and return a downloadable PNG.

---

## Repository Structure

```
kids-tesla-art/
├── frontend/                    # Next.js app
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx             # Landing / upload page
│   │   └── guide/
│   │       └── page.tsx         # USB guide page
│   ├── components/
│   │   ├── ModelSelector.tsx
│   │   ├── ImageUploader.tsx    # drag-and-drop + camera capture
│   │   ├── ProcessingStatus.tsx
│   │   └── DownloadButton.tsx
│   ├── public/
│   │   └── templates/           # Preview images per model
│   ├── Dockerfile
│   ├── package.json
│   └── next.config.ts
│
├── backend/                     # FastAPI app
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   └── process.py       # POST /api/process
│   │   ├── services/
│   │   │   ├── detection.py     # ArUco detection + perspective warp
│   │   │   ├── removal.py       # Background removal (rembg)
│   │   │   └── compositing.py   # UV mapping + PNG optimization
│   │   └── templates/           # Bundled Tesla UV PNGs
│   │       ├── model3.png
│   │       └── modely.png
│   ├── Dockerfile
│   └── requirements.txt
│
├── nginx/
│   └── nginx.conf               # Reverse proxy config
│
├── docker-compose.yml           # Production compose (OCI)
├── docker-compose.dev.yml       # Local dev compose
├── .github/
│   └── workflows/
│       └── deploy.yml           # CI/CD pipeline
├── LICENSE
├── CONTRIBUTING.md
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15 (App Router), Tailwind CSS v4, TypeScript |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Image Processing | opencv-contrib-python, rembg, Pillow, numpy |
| Reverse Proxy | Nginx (Alpine) |
| Containerization | Docker (multi-stage builds) |
| Registry | DockerHub (public) |
| Hosting | OCI VM.Standard.A1.Flex (ARM64, 4 OCPU, 24GB RAM) |
| CI/CD | GitHub Actions → DockerHub → SSH deploy to OCI |

---

## Backend API

### `POST /api/process`

**Request:** `multipart/form-data`
- `image`: image file (JPEG / PNG / WEBP / HEIC)
- `model`: `"model3"` | `"modely"`

**Processing pipeline:**
1. Decode uploaded image to numpy array
2. Convert to grayscale for ArUco detection
3. Detect 4 ArUco markers (DICT_4X4_50, IDs 0–3)
4. If fewer than 4 detected → return `422` with descriptive error message
5. Map marker corners to template corners → `getPerspectiveTransform` + `warpPerspective`
6. Remove background → `rembg` (u2net model, pre-loaded at startup)
7. Composite RGBA drawing onto Tesla UV template PNG
8. Resize to 1024×1024
9. Compress to ≤ 1MB (`Pillow` PNG optimize loop, reducing quality if needed)
10. Sanitize output filename (strip non-alphanumeric except `_-`, truncate to 30 chars)
11. Return PNG as `StreamingResponse` with `Content-Disposition: attachment`

**Error responses:**
- `422`: Markers not detected (< 4 found)
- `400`: Unsupported file type
- `500`: Internal processing error

### `GET /api/health`
Returns `{"status": "ok"}` — used by Docker healthcheck.

### `GET /api/templates`
Returns list of supported models and their template metadata.

---

## Frontend Pages

### `/` — Upload Page
- Model selector (Model 3 / Model Y) with preview images
- Upload zone:
  - **Desktop:** drag-and-drop area + file picker
  - **Mobile:** "Take Photo" button using `<input type="file" accept="image/*" capture="environment">`
- Processing spinner with status message
- On success: download button + link to `/guide`

### `/guide` — USB Guide Page
- Step-by-step instructions with illustrations:
  1. Format USB as exFAT/FAT32
  2. Create `Wraps` folder at root
  3. Copy PNG file
  4. Insert USB → Tesla Toybox → Paint Shop → Wraps
- Printable-friendly layout

---

## Docker Configuration

### Backend Dockerfile (multi-stage, ARM64-safe)
```dockerfile
FROM python:3.11-slim AS base

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Pre-download rembg U2Net model at build time to avoid runtime delay
RUN python -c "from rembg import new_session; new_session('u2net')"

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Key: **no `danielgatis/rembg` base image** — installs via pip to support ARM64.

### Frontend Dockerfile (multi-stage)
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
CMD ["node", "server.js"]
```

### docker-compose.yml (production)
```yaml
services:
  frontend:
    image: ${DOCKERHUB_USERNAME}/kids-tesla-art-frontend:latest
    restart: unless-stopped
    expose:
      - "3000"

  backend:
    image: ${DOCKERHUB_USERNAME}/kids-tesla-art-backend:latest
    restart: unless-stopped
    expose:
      - "8000"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/certs:/etc/nginx/certs:ro
    depends_on:
      - frontend
      - backend
```

---

## Nginx Configuration

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 20M;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;  # rembg processing can take 10–30s
    }

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## CI/CD Pipeline: GitHub Actions

**File:** `.github/workflows/deploy.yml`

**Trigger:** push to `main`

**Steps:**
1. Checkout code
2. Set up QEMU (for multi-arch emulation)
3. Set up Docker Buildx
4. Login to DockerHub
5. Build & push **backend** image: `linux/amd64,linux/arm64`
6. Build & push **frontend** image: `linux/amd64,linux/arm64`
7. SSH into OCI server → `docker compose pull && docker compose up -d`

**GitHub Secrets required:**
| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | DockerHub username |
| `DOCKERHUB_TOKEN` | DockerHub access token |
| `OCI_HOST` | OCI server public IP |
| `OCI_SSH_KEY` | Private SSH key for OCI ubuntu user |

---

## OCI Server Setup (one-time manual)

1. Provision `VM.Standard.A1.Flex` (4 OCPU, 24GB, Ubuntu 22.04)
2. Open ports in OCI Security Lists: TCP 22, 80, 443 ingress
3. Open ports in OS firewall:
   ```bash
   sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
   sudo apt install iptables-persistent -y
   ```
4. Install Docker + Docker Compose plugin
5. Add ubuntu user to docker group
6. Clone repo → `docker compose up -d`
7. Add SSH public key from GitHub Actions secret

---

## PDF Template Design

The printable PDF templates must include:
- Simplified, bold-outlined Tesla silhouette (coloring-book style)
- 4 ArUco markers (DICT_4X4_50, IDs 0–3) at the four corners, sized ≥ 2cm for reliable detection
- Clear border region with instruction text ("Color inside the lines!")
- One template per model (Model 3, Model Y)
- Generated programmatically using `reportlab` or designed in Inkscape, exported as PDF

---

## Todo List

### Phase 1: Project Scaffolding
- [ ] Initialize Next.js 15 project with TypeScript + Tailwind CSS in `frontend/`
- [ ] Initialize FastAPI project with `uv` or plain pip in `backend/`
- [ ] Create `requirements.txt` (fastapi, uvicorn, opencv-contrib-python, rembg, Pillow, numpy, python-multipart)
- [ ] Create `backend/Dockerfile` (multi-stage, pip-based rembg, ARM64-safe)
- [ ] Create `frontend/Dockerfile` (multi-stage, Next.js standalone output)
- [ ] Create `nginx/nginx.conf`
- [ ] Create `docker-compose.yml` and `docker-compose.dev.yml`
- [ ] Create `.github/workflows/deploy.yml`

### Phase 2: Backend — Image Processing Pipeline
- [ ] `backend/app/main.py`: FastAPI app entry, CORS, startup rembg session preload
- [ ] `backend/app/services/detection.py`: ArUco detection + perspective warp
- [ ] `backend/app/services/removal.py`: rembg background removal wrapper
- [ ] `backend/app/services/compositing.py`: UV template compositing + resize + PNG compression
- [ ] `backend/app/routers/process.py`: `POST /api/process` endpoint
- [ ] Bundle official Tesla UV templates (`model3.png`, `modely.png`) in `backend/app/templates/`
- [ ] `GET /api/health` and `GET /api/templates` endpoints

### Phase 3: Frontend — UI
- [ ] `app/layout.tsx`: root layout, metadata, fonts
- [ ] `app/page.tsx`: main upload page structure
- [ ] `components/ModelSelector.tsx`: Model 3 / Model Y toggle with preview
- [ ] `components/ImageUploader.tsx`: drag-and-drop + mobile camera input
- [ ] `components/ProcessingStatus.tsx`: spinner + status messages
- [ ] `components/DownloadButton.tsx`: trigger download of processed PNG
- [ ] `app/guide/page.tsx`: step-by-step USB guide
- [ ] Wire up `POST /api/process` call with form data

### Phase 4: PDF Template Generation
- [ ] Script to generate printable PDF templates with ArUco markers for Model 3 and Model Y
- [ ] Place generated PDFs in `frontend/public/templates/`

### Phase 5: Polish & Docs
- [ ] `README.md`: project overview, local dev setup, deployment guide
- [ ] `CONTRIBUTING.md`
- [ ] `LICENSE` (MIT)
- [ ] Verify output PNG meets Tesla specs: 1024×1024, ≤1MB, valid filename

---

## Key Constraints to Enforce

- rembg must be installed via `pip`, not from the official Docker image (ARM64 incompatible)
- rembg session must be pre-loaded at FastAPI startup (not per-request) to avoid 30s cold start
- `proxy_read_timeout` in Nginx must be ≥ 60s (rembg processing time on CPU)
- Output PNG filename must be sanitized: only `[A-Za-z0-9_\- ]`, max 30 chars
- File upload size limit: 20MB (raw phone photos can be large)
- No user data persisted server-side — process entirely in memory
