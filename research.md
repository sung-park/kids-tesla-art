# Kids Tesla Art — Research Document

## 1. Tesla Custom Wrap Specifications

### File Requirements (Official)
- **Format:** PNG only
- **Resolution:** 512×512 to 1024×1024 pixels (PRD targets 1024×1024)
- **File size:** ≤ 1 MB
- **Filename:** Alphanumeric, underscores, dashes, spaces only — max 30 characters
- **Max files:** 10 images per USB load

### USB / Application Flow
1. Format USB drive as exFAT or FAT32 (MS-DOS FAT on Mac; ext3/ext4 also supported; **NTFS not supported**)
2. Create folder named `Wraps` at USB root
3. Copy PNG file(s) into `Wraps/`
4. Insert USB into Tesla → Toybox → Paint Shop → Wraps tab

### Official UV Templates
- **Repo:** [teslamotors/custom-wraps](https://github.com/teslamotors/custom-wraps)
- Available models: `/model3`, `/modely` (including all variants: Standard, Premium, Performance, Legacy, L)
- Cybertruck support exists in community repos but not yet fully stable
- Templates are PNGs with UV-mapped regions clearly visible in white/grey

### Source: [teslamotors/custom-wraps README](https://github.com/teslamotors/custom-wraps/blob/master/README.md)

---

## 2. Image Processing Pipeline

### ArUco Marker Detection + Perspective Warp

**Library:** `opencv-python` (cv2.aruco module, included in `opencv-contrib-python`)

**Workflow:**
```python
import cv2
import numpy as np

# 1. Detect markers
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
corners, ids, rejected = detector.detectMarkers(image)

# 2. Extract 4 corner points (top-left, top-right, bottom-right, bottom-left order)
# Each marker gives one corner of the template rectangle

# 3. Perspective warp
src_pts = np.float32([corner_tl, corner_tr, corner_br, corner_bl])
dst_pts = np.float32([[0,0], [W,0], [W,H], [0,H]])
M = cv2.getPerspectiveTransform(src_pts, dst_pts)
warped = cv2.warpPerspective(image, M, (W, H))
```

**Recommended dictionary:** `DICT_4X4_50` — smallest markers, easiest to print and detect
**Marker placement:** One at each corner of the printable template area (IDs: 0, 1, 2, 3)
**Fallback:** If fewer than 4 markers detected, return error to user with guidance

**Sources:**
- [OpenCV ArUco Detection Docs](https://docs.opencv.org/4.x/d5/dae/tutorial_aruco_detection.html)
- [PyImageSearch ArUco Tutorial](https://pyimagesearch.com/2020/12/21/detecting-aruco-markers-with-opencv-and-python/)

---

### Background Removal

**Library:** `rembg` — uses U²-Net deep learning model

**⚠️ Critical ARM64 Issue:**
The official `danielgatis/rembg` Docker image **dropped ARM64 support on March 15, 2025** (PR #743) due to build timeouts in GitHub Actions. The Docker image is AMD64-only.

**Solution for OCI Ampere A1 (ARM64):**
Install `rembg` via `pip` in a custom Dockerfile — the Python library itself works on ARM64. The U²-Net model (~176MB) must be pre-downloaded during the Docker build to avoid runtime delay.

```dockerfile
FROM python:3.11-slim AS builder
# ... install rembg via pip
RUN pip install rembg[gpu] onnxruntime
# Pre-download model at build time
RUN python -c "from rembg import new_session; new_session('u2net')"
```

**Alternative libraries if rembg proves too slow on CPU:**
- `carvekit` — faster inference options
- `backgroundremover` — lighter weight

**Sources:**
- [rembg GitHub](https://github.com/danielgatis/rembg)
- [ARM64 removal PR #743](https://github.com/danielgatis/rembg/pull/743)
- [ARM64 feature request issue #745](https://github.com/danielgatis/rembg/issues/745)

---

### UV Mapping
After perspective correction and background removal:
1. Load the Tesla UV template PNG for the selected model (bundled in the app)
2. Composite the processed drawing onto the UV template using Pillow (`Image.paste` with alpha mask)
3. Resize to 1024×1024 and compress to ≤ 1MB using `Pillow` with `optimize=True`

---

## 3. Infrastructure: OCI ARM Free Tier

### Instance Specs
- **Shape:** `VM.Standard.A1.Flex`
- **Architecture:** ARM64 (Ampere A1)
- **Free allowance:** Up to 4 OCPU + 24 GB RAM (always free, never expires)
- **Storage:** 200 GB block storage
- **Recommended OS:** Ubuntu 22.04 LTS

### Port Configuration (Critical)
Two layers of firewall must be opened:
1. **OCI Security Rules:** Compute → Network → Security Lists → add ingress rules for TCP 80, 443
2. **OS iptables:** `sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT` (iptables rules persist via `iptables-persistent`)

### Docker on OCI ARM64
- Use official Docker install script or apt repository
- Docker Compose v2 plugin: `docker-compose-plugin`
- ARM64 images are supported by most popular base images (nginx, python, node)

**Sources:**
- [Tim Nolte: Docker on OCI ARM64](https://www.timnolte.com/2023/03/16/setting-up-a-web-server-using-docker-on-oracle-cloud-infrastructure-ampere-arm64-always-free-instance/)
- [OneUptime: Docker on OCI Free Tier 2026](https://oneuptime.com/blog/post/2026-02-08-how-to-set-up-docker-on-an-oracle-cloud-free-tier-instance/view)

---

## 4. CI/CD Pipeline: GitHub → DockerHub → OCI

### Strategy: GitHub Actions + QEMU + Watchtower

```
[Push to main] → GitHub Actions → Build multi-arch image (amd64 + arm64)
              → Push to DockerHub
              → Watchtower on OCI polls DockerHub every 5 min
              → Auto-pulls new arm64 image → Restarts containers
```

### GitHub Actions Workflow (multi-platform build)
```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
- name: Build and push
  uses: docker/build-push-action@v6
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ${{ secrets.DOCKERHUB_USERNAME }}/sketch2wrap:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**Note:** ARM64 builds via QEMU emulation are 3–10x slower than native. For faster CI, use native ARM64 runner: `ubuntu-24.04-arm` (GitHub-hosted, billed separately) or keep QEMU since builds are infrequent for a personal project.

### Watchtower on OCI (auto-deploy)
```yaml
# docker-compose.yml on OCI server
services:
  watchtower:
    image: containrrr/watchtower:latest  # or nicholas-fedor/watchtower fork
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_POLL_INTERVAL=300
```

**⚠️ Note:** Original `containrrr/watchtower` was archived December 17, 2025. Use the active fork: [`nicholas-fedor/watchtower`](https://github.com/nicholas-fedor/watchtower) or switch to SSH-based deployment trigger in GitHub Actions.

**Alternative to Watchtower:** SSH deploy step in GitHub Actions:
```yaml
- name: Deploy to OCI
  uses: appleboy/ssh-action@v1
  with:
    host: ${{ secrets.OCI_HOST }}
    username: ubuntu
    key: ${{ secrets.OCI_SSH_KEY }}
    script: |
      docker compose pull
      docker compose up -d
```

### DockerHub Registry
- Free tier: unlimited public repos, 1 private repo
- Use `DOCKERHUB_USERNAME` + `DOCKERHUB_TOKEN` secrets in GitHub Actions
- Public repo is fine for an open-source project

**Sources:**
- [Docker Multi-platform CI docs](https://docs.docker.com/build/ci/github-actions/multi-platform/)
- [docker/build-push-action](https://github.com/marketplace/actions/build-and-push-docker-images)
- [Watchtower + GitHub Actions guide](https://medium.com/@raphael.derouelle.pro/automating-docker-image-builds-and-deployment-with-github-actions-and-watchtower-8edbe426352f)

---

## 5. Application Architecture

### Proposed Stack

```
┌─────────────────────────────────────────────┐
│                OCI ARM Server                │
│                                              │
│  [Nginx] :80/:443                            │
│    ├── /api  → FastAPI (Python) :8000        │
│    └── /     → Next.js (Node)  :3000         │
│                                              │
│  [Watchtower]  polls DockerHub every 5min    │
└─────────────────────────────────────────────┘
```

**Frontend (Next.js + Tailwind CSS):**
- Mobile-first, responsive
- Camera capture API (`getUserMedia`) for mobile scanner UI
- Drag-and-drop upload zone for desktop
- Step-by-step USB guide page
- Model selection (Model 3 / Model Y)

**Backend (FastAPI + Python):**
- `POST /api/process` — accepts image upload, returns processed PNG
- `GET /api/templates/{model}` — returns available template metadata
- Processing pipeline:
  1. Receive image (JPEG/PNG/HEIC from mobile)
  2. Detect ArUco markers (OpenCV + opencv-contrib)
  3. Perspective correction (warpPerspective)
  4. Background removal (rembg)
  5. Map onto Tesla UV template (Pillow composite)
  6. Optimize to 1024×1024, ≤1MB PNG
  7. Return as file download

**Stateless design:** No database, no user accounts. Each request is self-contained. Images are processed in memory and not persisted server-side (privacy-friendly, low maintenance).

---

## 6. Key Technical Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| rembg no official ARM64 Docker image | High | Install via pip in custom Dockerfile; pre-download model |
| rembg slow on CPU-only ARM64 | Medium | OCI A1 has 4 OCPU + 24GB — should be adequate; test with benchmark |
| ArUco marker detection fails on blurry/dark photos | Medium | Add preprocessing (grayscale, threshold, adaptive histogram); show clear UI guidance |
| Tesla UV template changes across firmware updates | Low | Bundle templates from official repo; document version; make templates configurable |
| OCI capacity constraints when provisioning | Low | Retry at off-peak hours; documented in setup guide |
| watchtower archived | Low | Use SSH-based deploy in GitHub Actions as primary strategy |

---

## 7. Open Source Considerations

- License: **MIT** (simplest, most permissive for open-source tools)
- Tesla UV templates from `teslamotors/custom-wraps` can be redistributed (Tesla's repo is public; verify license)
- All code and documentation in English
- Include `CONTRIBUTING.md` and `LICENSE`
