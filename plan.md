# Plan: Car-Silhouette Template Redesign (2026-03-06)

## Goal
아이가 실제 테슬라 모양을 보고 색칠할 수 있는 템플릿으로 교체.
- 현재: UV 맵 패널 사각형 블록 나열 (평면도) → 아이 입장에서 의미 없음
- 목표: 사이드뷰 + 탑뷰 실루엣 → 아이가 "테슬라 차다!" 즉시 인식

## 변경 범위

**변경 없음**: `panel_map.py`, `compositing.py`, `detection.py`, 프론트엔드 전체
**변경 필요**: `*_panels.json` (kid_quad 좌표), `generate_templates.py` (실루엣 드로잉)

---

## 새 레이아웃 설계

A4 PDF (2480×3508px), 내부 드로잉 영역 1024×1024 기준 좌표계:

```
┌──────────────────────────────────────┐
│  [ArUco0]              [ArUco1]       │
│  ┌────────────────────────────────┐  │
│  │   테슬라 LEFT SIDE 실루엣       │  │  Row1: y=20~390
│  │   (차체 색칠 영역)              │  │
│  └────────────────────────────────┘  │
│                                       │
│      ┌──────────────────────┐        │
│      │  Hood  │ Roof │Trunk │        │  Row2: y=420~700
│      │ (탑뷰 — 위에서 본 차) │        │
│      └──────────────────────┘        │
│                                       │
│  ┌────────────────────────────────┐  │
│  │   테슬라 RIGHT SIDE 실루엣(반전)│  │  Row3: y=730~1000
│  │   (차체 색칠 영역)              │  │
│  └────────────────────────────────┘  │
│                                       │
│  [ArUco3]  Kids Tesla Art  [ArUco2]  │
└──────────────────────────────────────┘
```

---

## 새 kid_quad 좌표 (1024×1024 기준)

```json
left_side:   [[20, 20],   [1004, 20],  [1004, 390], [20, 390]]
hood:        [[220, 420], [780, 420],  [780, 520],  [220, 520]]
roof:        [[220, 520], [780, 520],  [780, 620],  [220, 620]]
trunk:       [[220, 620], [780, 620],  [780, 710],  [220, 710]]
right_side:  [[20, 730],  [1004, 730], [1004, 1000],[20, 1000]]
```

*uv_quad는 기존 좌표 그대로 유지 — 실제 UV 맵 위치이므로 변경 불필요*

---

## 구현: `generate_templates.py`

`generate_template_png()` 를 아래 구조로 전면 교체:

```python
def generate_template_png(model):
    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 1. ArUco 마커 4 모서리
    _draw_aruco_markers(img)

    # 2. LEFT SIDE 실루엣 (Row 1)
    _draw_car_side(draw, region=_page_rect(20, 20, 1004, 390), flip=False,
                   fill=(255, 235, 235), label="Left Side  →  색칠하세요!")

    # 3. TOP VIEW (Row 2: hood / roof / trunk 3분할)
    _draw_car_top(draw,
                  hood_rect=_page_rect(220, 420, 780, 520),
                  roof_rect=_page_rect(220, 520, 780, 620),
                  trunk_rect=_page_rect(220, 620, 780, 710))

    # 4. RIGHT SIDE 실루엣 (Row 3, 좌우 반전)
    _draw_car_side(draw, region=_page_rect(20, 730, 1004, 1000), flip=True,
                   fill=(235, 235, 255), label="Right Side  →  색칠하세요!")

    # 5. 하단 안내 텍스트
    _draw_instructions(draw, model)

    return img
```

### `_draw_car_side()` 핵심 로직
- 테슬라 Model 3/Y 사이드뷰를 좌표 점 리스트로 정의 (PIL polygon)
- 차체 외곽선: 두꺼운 검은 선 (width=8)
- 차 내부: 연한 파스텔 fill (아이 색칠이 잘 보이도록)
- 창문: 연한 파란 fill + 테두리
- 바퀴: 회색 원
- 도어 라인: 얇은 회색 구분선
- 레이블: 영역 하단에 작게

### `_draw_car_top()` 핵심 로직
- 위에서 본 차 실루엣 (좁고 긴 타원형 + 테이퍼)
- Hood/Roof/Trunk 3구역을 서로 다른 파스텔 색으로 구분
- 각 구역 레이블 중앙 배치
- 앞유리/뒷유리 표시

---

## 실루엣 좌표 (Python 코드 핵심 부분)

### Tesla Model 3 사이드 프로파일 (정규화 0~1, region에 fit)

```python
# flip=False 기준 (Left Side) — 앞이 왼쪽
SIDE_PROFILE = [
    # (x_ratio, y_ratio) — 0,0은 region 좌상단
    (0.03, 0.95),   # 앞 하단
    (0.03, 0.65),   # 앞 범퍼 상단
    (0.07, 0.52),   # 후드 시작
    (0.28, 0.44),   # 후드 끝 / 앞유리 하단
    (0.34, 0.14),   # 앞유리 상단
    (0.40, 0.08),   # 루프 앞
    (0.68, 0.08),   # 루프 뒤
    (0.77, 0.22),   # 뒤 유리 상단
    (0.86, 0.42),   # 트렁크
    (0.92, 0.50),   # 후방 범퍼 상단
    (0.97, 0.65),   # 후방 범퍼
    (0.97, 0.95),   # 뒤 하단
]
FRONT_WHEEL = (0.20, 0.88, 0.10)  # cx_r, cy_r, r_r
REAR_WHEEL  = (0.78, 0.88, 0.10)
```

### Tesla Model Y 사이드 프로파일 (더 높은 루프라인)
```python
SIDE_PROFILE_Y = [
    (0.03, 0.95),
    (0.03, 0.60),
    (0.07, 0.46),
    (0.26, 0.38),
    (0.32, 0.10),   # Y는 루프가 더 높고 직선적
    (0.38, 0.06),
    (0.70, 0.06),
    (0.78, 0.10),
    (0.85, 0.38),
    (0.90, 0.46),
    (0.97, 0.60),
    (0.97, 0.95),
]
```

---

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/templates/model3_panels.json` | kid_quad 좌표 새 레이아웃으로 교체 |
| `backend/app/templates/modely_panels.json` | 동일 |
| `scripts/generate_templates.py` | 실루엣 드로잉 + 새 레이아웃 |
| `frontend/public/templates/model3-template.pdf` | 재생성 (스크립트 실행) |
| `frontend/public/templates/modely-template.pdf` | 재생성 |

---

## Todo List

- [ ] `model3_panels.json` — kid_quad를 새 레이아웃 좌표로 교체
- [ ] `modely_panels.json` — 동일
- [ ] `generate_templates.py` — 실루엣 드로잉 함수 구현 (`_draw_car_side`, `_draw_car_top`)
- [ ] 로컬에서 PDF 재생성 및 시각 확인 (`/tmp/tesla-venv/bin/python scripts/generate_templates.py`)
- [ ] 생성된 PDF `frontend/public/templates/` 에 커밋
- [ ] 커밋 & 푸쉬
