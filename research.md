# Kids Tesla Art — Research Document

## Car-Silhouette Template Redesign (2026-03-06)

### Problem
현재 템플릿은 UV 맵 패널을 사각형 블록으로 나열한 평면도.
아이가 보면 "이게 뭐지?" — 차라는 걸 전혀 알 수 없음.

### Goal
아이가 한눈에 "테슬라다!" 알 수 있는 템플릿:
- **사이드뷰**: 테슬라 측면 실루엣 안에 색칠
- **탑뷰**: 위에서 본 지붕/후드/트렁크
- 색칠한 영역이 UV 맵으로 정확히 매핑되어야 함

### UV Template 구조 (실제 확인)

Model 3 & Y 둘 다 동일한 레이아웃:
```
┌─────────────────────────────────────┐
│  Left col (x≈0-280)  │ Center (x≈276-748) │ Right col (x≈749-1014) │
│  왼쪽 측면 패널들      │ 루프/후드/트렁크    │ 오른쪽 측면 패널들      │
│  (도어, 펜더 등)       │ (위에서 본 모습)    │ (왼쪽의 거울상)        │
└─────────────────────────────────────┘
```

### 핵심 기술 제약

1. **`cv2.getPerspectiveTransform()`은 정확히 4점 → 4점 매핑**
   - kid_quad: 4개 꼭짓점 (원본 - 아이 템플릿 공간)
   - uv_quad: 4개 꼭짓점 (대상 - UV 공간)
   - 사각형일 필요 없음 — 임의의 사각형(quadrilateral) 가능

2. **`cv2.fillPoly()` 마스크**: UV 영역 외부로 색이 번지지 않게 제한 → 변경 불필요

3. **ArUco 마커**: 4개 코너 마커로 사진 → 1024x1024 보정 → 변경 불필요

### 제안: 차량 실루엣 기반 레이아웃

```
A4 페이지:
[ArUco 0]                              [ArUco 1]
  ┌──────────────────────────────────────┐
  │                                      │
  │   ┏━━━━ 테슬라 사이드뷰 실루엣 ━━━━┓  │
  │   ┃  LEFT SIDE (색칠 영역)         ┃  │  ← 큰 사이드뷰
  │   ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
  │                                      │
  │   ┌─ 탑뷰 ─────────────────────┐    │
  │   │ [Hood]  [Roof]  [Trunk]    │    │  ← 위에서 본 모습
  │   └────────────────────────────┘    │
  │                                      │
  │   ┏━━━━ 테슬라 사이드뷰 (반전) ━━━┓  │
  │   ┃  RIGHT SIDE (색칠 영역)      ┃  │  ← 반전 사이드뷰
  │   ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
  │                                      │
  │   "Kids Tesla Art — Model 3"        │
  └──────────────────────────────────────┘
[ArUco 3]                              [ArUco 2]
```

### 구현 방식: 실루엣은 시각적 가이드, 매핑은 quad 기반

- **시각적 레이어**: 차 실루엣 윤곽선 (PIL bezier/polygon으로 그림)
- **매핑 레이어**: kid_quad 4점은 각 뷰의 바운딩 사각형
- 실루엣 바깥 영역은 rembg 배경 제거 + alpha 마스크로 자연스럽게 무시됨
- 아이가 실루엣 밖으로 색칠해도 상관없음 (UV fillPoly 마스크가 잘라냄)

### 실루엣 생성 방법

**Option A: PIL로 좌표 기반 드로잉 (선택)**
- Tesla Model 3/Y 프로파일을 좌표 점 리스트로 정의
- `ImageDraw.polygon()` + `ImageDraw.arc()` 조합
- 장점: 의존성 없음, 벡터 품질, 점 조정 쉬움
- 단점: 수작업으로 좌표 정의 필요

**Option B: SVG → PNG 변환**
- 실루엣 SVG 파일을 repo에 포함
- cairosvg 또는 reportlab로 렌더링
- 추가 의존성 필요

### 변경 필요 파일

| File | Change |
|------|--------|
| `backend/app/templates/model3_panels.json` | kid_quad를 새 레이아웃에 맞게 수정 |
| `backend/app/templates/modely_panels.json` | 동일 |
| `scripts/generate_templates.py` | 실루엣 드로잉 + 새 레이아웃 |
| `backend/app/services/panel_map.py` | 변경 없음 (이미 임의 quad 지원) |
| `backend/app/services/compositing.py` | 변경 없음 |
| `backend/app/services/detection.py` | 변경 없음 |
| `frontend/*` | 변경 없음 (PDF만 바뀌므로) |

### 백엔드 영향: 없음
`getPerspectiveTransform`과 `fillPoly`는 kid_quad 좌표만 바뀌면 됨.
kid_quad가 사각형이든 평행사변형이든 상관없이 동작.

---

(이전 리서치 내용은 아래 보관)

## Previous Research (archived)

### Tesla Custom Wrap Specs
- PNG, 1024x1024, ≤1MB
- USB folder: "Wraps" (exFAT/FAT32)
- Apply via Toybox → Paint Shop → Wraps

### Processing Pipeline
```
Photo → ArUco warp → rembg BG removal → per-panel composite → PNG
```

### Infrastructure
- OCI ARM64 (VM.Standard.A1.Flex), Docker, Nginx reverse proxy
- GitHub Actions (ARM64 native runner) → DockerHub → SSH deploy
