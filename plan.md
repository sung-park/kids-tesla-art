# Plan: Piecewise Affine Warping 재설계 (2026-03-06)

## 목표
아이가 차 실루엣 템플릿에 색칠 → 사진 업로드 → UV 맵에 **자연스럽게** 매핑.
4점 perspective 대신 **삼각 메시 기반 piecewise affine warping** 사용.

## 핵심 변경

### 1. `warping.py` (신규) — Piecewise Affine 워핑 엔진

제어점 기반 삼각 메시 워핑:

```python
def build_warp_map(src_pts, dst_pts, output_size=1024):
    """제어점 쌍으로부터 cv2.remap()용 맵 생성.

    1. dst_pts에 대해 Delaunay 삼각분할
    2. 각 출력 픽셀이 어느 삼각형에 속하는지 판별
    3. 해당 삼각형의 아핀 역변환으로 소스 좌표 계산
    4. mapx, mapy 배열 반환
    """
    ...

def apply_warp(src_image, mapx, mapy):
    """사전 계산된 워프맵으로 이미지 변형."""
    return cv2.remap(src_image, mapx, mapy, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
```

**성능**: 워프맵 생성 1회 (서버 시작 시), 이후 `cv2.remap()`은 <10ms.

### 2. 제어점 JSON (model3_warp.json, modely_warp.json)

각 영역별 src(아이 템플릿) → dst(UV 맵) 대응점:

```json
{
  "regions": [
    {
      "name": "left_side",
      "src_points": [
        [20, 20], [266, 20], [512, 20], [758, 20], [1004, 20],
        [20, 205], [266, 205], [512, 205], [758, 205], [1004, 205],
        [20, 390], [266, 390], [512, 390], [758, 390], [1004, 390]
      ],
      "dst_points": [
        [14, 994], [14, 800], [14, 590], [14, 380], [14, 131],
        [146, 994], [146, 800], [146, 590], [146, 380], [146, 131],
        [278, 994], [278, 800], [278, 590], [278, 380], [278, 131]
      ]
    },
    {
      "name": "right_side",
      "src_points": "... (좌측 미러 + UV 우측 칼럼 좌표)"
    },
    {
      "name": "hood",
      "src_points": [[220,420],[500,420],[780,420],[220,520],[500,520],[780,520]],
      "dst_points": [[368,175],[512,175],[655,175],[368,399],[512,399],[655,399]]
    },
    { "name": "roof", "...": "..." },
    { "name": "trunk", "...": "..." }
  ]
}
```

### 3. UV 마스크 합성 (compositing.py 업데이트)

```python
def generate_uv_mask(uv_template):
    """UV 템플릿에서 색칠 가능 영역 마스크 생성.
    흰색(밝은) 영역 = 색칠 가능, 아웃라인/투명 = 보호."""
    gray = cv2.cvtColor(uv_template[:,:,:3], cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
    return mask

def composite(warped_drawing, uv_template, mask):
    """마스크를 통해 워핑된 아이 그림을 UV 템플릿에 합성."""
    # mask가 흰색인 곳에만 아이 그림 표시
    # 나머지는 UV 템플릿(아웃라인 등) 유지
```

### 4. panel_map.py 대체

기존 `panel_map.py`의 `composite_with_panels()` → `warping.py`의 `apply_warp()` + 새 합성 로직으로 교체.

---

## 파이프라인 비교

```
Before: Photo → ArUco → threshold BG → per-panel perspective(4점) → UV composite
After:  Photo → ArUco → threshold BG → piecewise affine warp(N점) → UV mask composite
```

## 변경 파일

| 파일 | 변경 |
|------|------|
| `backend/app/services/warping.py` | **신규** — piecewise affine 엔진 |
| `backend/app/templates/model3_warp.json` | **신규** — 제어점 |
| `backend/app/templates/modely_warp.json` | **신규** — 제어점 |
| `backend/app/services/compositing.py` | warping 호출 + UV 마스크 합성 |
| `backend/app/services/panel_map.py` | 삭제 (warping.py로 대체) |
| `backend/tests/test_warping.py` | **신규** |
| `backend/tests/test_compositing.py` | 업데이트 |

**변경 없음**: detection.py, removal.py, 프론트엔드, 템플릿 PDF, generate_templates.py

---

## Todo

- [ ] `warping.py` — piecewise affine 워핑 엔진 구현
- [ ] `model3_warp.json` — Model 3 제어점 정의
- [ ] `modely_warp.json` — Model Y 제어점 정의
- [ ] `compositing.py` — UV 마스크 합성 로직으로 교체
- [ ] `panel_map.py` 정리 (warping.py import로 대체)
- [ ] `test_warping.py` — 워핑 유닛 테스트
- [ ] `test_compositing.py` — 업데이트
- [ ] 백엔드 전체 테스트 통과
- [ ] 커밋 & 푸쉬
