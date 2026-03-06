# Kids Tesla Art — Research Document

## TPS 기반 Image Warping 재설계 (2026-03-06)

### 왜 이전 접근법이 실패하는가

`cv2.getPerspectiveTransform` (4점→4점 매핑)의 근본적 한계:
- 직사각형→직사각형 변환만 가능 (선형 변환)
- 사이드뷰 가로 차(984×370) → UV 세로 스트립(264×863)은 **90° 회전 + 비균일 스케일링**
- 이건 4점 perspective로 표현 불가능 → 아무리 패널을 잘게 잘라도 왜곡 불가피

### 해결: Piecewise Affine Warping (삼각 메시 기반)

**핵심 아이디어**: 두 공간 (아이 템플릿 ↔ UV 맵) 사이에 **대응 제어점(control points)**을 정의하고,
Delaunay 삼각분할 → 삼각형별 아핀 변환으로 부드러운 비선형 워핑 수행.

```
아이 템플릿 (1024×1024)              UV 템플릿 (1024×1024)
┌──────────────────────┐          ┌──────────────────────┐
│  Left Side (가로 차)  │   TPS    │  ┌──┐ ┌────┐ ┌──┐  │
│  ──────────────────  │  =====>  │  │L │ │Roof│ │R │  │
│  Top (Hood/Roof/Trunk)│  warp   │  │  │ │Hood│ │  │  │
│  ──────────────────  │          │  │  │ │Trnk│ │  │  │
│  Right Side (반전 차) │          │  └──┘ └────┘ └──┘  │
└──────────────────────┘          └──────────────────────┘
```

### UV 템플릿 정밀 분석

**Model 3 UV (1024×1024)**에서 직접 관찰한 패널 영역:

```
중앙 영역:
  Roof:    (276, 25)  ~ (748, 166)   — 가로 472, 세로 141
  Hood:    (368, 175) ~ (655, 399)   — 가로 287, 세로 224
  Trunk:   (366, 684) ~ (655, 897)   — 가로 289, 세로 213

좌측 칼럼 (x: 14~278):
  상단 (rear quarter): y ≈ 131~380
  중상 (rear door):    y ≈ 380~590
  중하 (front door):   y ≈ 590~800
  하단 (front fender): y ≈ 800~994
  → 차 앞쪽이 UV 하단, 뒤쪽이 UV 상단 (90° 회전 관계)

우측 칼럼 (x: 749~1014): 좌측 미러
```

**핵심 관찰**: 사이드뷰→UV는 단순 스케일이 아니라 **90° 회전** 관계.
- 아이 템플릿의 가로축(차 앞→뒤) = UV의 세로축(아래→위)
- 아이 템플릿의 세로축(루프→휠아치) = UV의 가로축(좌→우)

이것은 4점 perspective로는 불가능하지만 **TPS/piecewise affine warping**으로 자연스럽게 처리 가능.

### 제어점 설계 (Left Side 예시)

아이 템플릿 좌측뷰 (20,20)~(1004,390)에서 5×3 격자:
```
Kid (x, y)        →    UV (x, y)
(20,  20)         →    (14,  994)    # 앞-상단 → UV 하단-좌
(266, 20)         →    (14,  800)
(512, 20)         →    (14,  590)
(758, 20)         →    (14,  380)
(1004, 20)        →    (14,  131)    # 뒤-상단 → UV 상단-좌

(20,  205)        →    (146, 994)    # 앞-중간 → UV 하단-중
(266, 205)        →    (146, 800)
(512, 205)        →    (146, 590)
(758, 205)        →    (146, 380)
(1004, 205)       →    (146, 131)

(20,  390)        →    (278, 994)    # 앞-하단 → UV 하단-우
(266, 390)        →    (278, 800)
(512, 390)        →    (278, 590)
(758, 390)        →    (278, 380)
(1004, 390)       →    (278, 131)    # 뒤-하단 → UV 상단-우
```

이 15개 점으로 Delaunay 삼각분할 → 각 삼각형별 아핀 변환 → 부드러운 워핑.

### 마스크 합성 전략

UV 템플릿에서 흰색(패널 내부) vs 검정 아웃라인 vs 투명(배경) 구분:
1. UV 템플릿을 그레이스케일 변환 → threshold → 흰색 영역 = 색칠 가능 마스크
2. 워핑된 아이 그림 × 마스크 = UV 패널 내부에만 색칠 적용
3. 아웃라인은 보존, 색칠은 내부만 → 깨끗한 출력

### 구현 기술 선택

| 방법 | 장점 | 단점 |
|------|------|------|
| TPS (Thin Plate Spline) | 수학적으로 깨끗, 글로벌 smooth | 경계 overshoot 가능 |
| **Piecewise Affine (삼각 메시)** | 예측 가능, 경계 안정적, 디버그 쉬움 | 삼각분할 필요 |
| cv2.remap() 기반 | 적용 매우 빠름 (lookup table) | 맵 생성은 별도 필요 |

**선택: Piecewise Affine + cv2.remap()**
- 삼각 메시로 워프맵 사전 생성 → JSON에 저장 or 시작 시 1회 계산
- 실제 워핑은 cv2.remap()으로 <10ms
- 추가 의존성 없음 (OpenCV + NumPy)
- 마스크는 UV 템플릿에서 자동 생성

### 변경 범위

| 파일 | 변경 |
|------|------|
| `backend/app/services/warping.py` | **신규** — piecewise affine 워핑 엔진 |
| `backend/app/services/panel_map.py` | 삭제 또는 warping.py로 대체 |
| `backend/app/services/compositing.py` | warping.py 호출 + UV 마스크 합성 |
| `backend/app/templates/model3_warp.json` | **신규** — 제어점 좌표 |
| `backend/app/templates/modely_warp.json` | **신규** — 제어점 좌표 |
| `backend/tests/test_warping.py` | **신규** |
| `backend/tests/test_compositing.py` | 업데이트 |

**변경 없음**: detection.py, removal.py, 프론트엔드, 템플릿 PDF

---

## Previous Research (archived)

### Fix 1-3 (2026-03-06): 이미 적용됨
- rembg → threshold 기반 배경 제거 (removal.py) ✅
- RGBA→RGB 흰색 배경 합성 (compositing.py) ✅
- 패널 세분화 시도 → 근본적으로 부족하여 TPS 접근으로 전환

### Tesla Custom Wrap Specs
- PNG, 1024x1024, ≤1MB, USB "Wraps" 폴더
- Apply via Toybox → Paint Shop → Wraps

### Infrastructure
- OCI ARM64, Docker, Nginx, GitHub Actions CI/CD
