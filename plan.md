# Plan: UV 미러링/클리핑 버그 수정 (2026-03-07)

## 문제 요약
1. **오른쪽 좌우 반전**: 오른쪽 UV 스트립의 화살표/텍스트가 왼쪽과 반대 방향
2. **사각형 클리핑**: wheel_exclusions 직사각형이 실제 휠아치와 안 맞아 바디 패널까지 잘림
3. **오른쪽 영역 좁음**: 오른쪽 warp src y 범위 95px (왼쪽 185px 대비 절반)

## 수정 방식

### Step 1: wheel_exclusions 제거 (Bug 2)
- `model3_panels.json`, `modely_panels.json`에서 `wheel_exclusions` 배열 삭제
- UV 템플릿 brightness 마스킹(`gray > 200`)이 이미 휠아치 처리함

### Step 2: 오른쪽 kid template 방향 통일 (Bug 1 + 3)
아이 템플릿 오른쪽 차를 왼쪽과 같은 방향(앞이 왼쪽)으로 변경:

#### 2a. `*_panels.json` 오른쪽 kid_quad x좌표 반전
현재 (차가 오른쪽 보는 배치):
```
right_front_fender: kid_quad x [758-1004]  (우측)
right_front_door:   kid_quad x [512-758]
right_rear_door:    kid_quad x [266-512]
right_rear_quarter: kid_quad x [20-266]    (좌측)
```
변경 후 (차가 왼쪽 보는 배치, 왼쪽과 동일):
```
right_front_fender: kid_quad x [20-266]    (좌측 = 차 앞)
right_front_door:   kid_quad x [266-512]
right_rear_door:    kid_quad x [512-758]
right_rear_quarter: kid_quad x [758-1004]  (우측 = 차 뒤)
```

#### 2b. `*_warp.json` right_side src_points 수정
현재 (x 역순):
```json
"src_points": [
  [1004, 865], [807, 865], ..., [20, 865],
  [1004, 935], ..., [20, 935],
  [1004, 960], ..., [20, 960]
]
```
변경 (x 정순, 왼쪽과 동일 + y 범위 확대):
```json
"src_points": [
  [20, 865], [217, 865], ..., [1004, 865],
  [20, 928], [217, 928], ..., [1004, 928],
  [20, 990], [217, 990], ..., [1004, 990]
]
```

#### 2c. `generate_templates.py` 오른쪽 flip=False
```python
# 변경 전
_draw_car_side(draw, ..., flip=True)
# 변경 후
_draw_car_side(draw, ..., flip=False)
```

### Step 3: 테스트 업데이트
- `test_colored_rect.py`로 시각적 검증
- 기존 backend 테스트 좌표 의존성 확인 및 업데이트
- `test_warp_local.py`로 전체 파이프라인 검증

### Step 4: 로컬 검증 후 커밋

## Todo
- [ ] model3_panels.json: wheel_exclusions 제거, 오른쪽 kid_quad 수정
- [ ] modely_panels.json: wheel_exclusions 제거, 오른쪽 kid_quad 수정
- [ ] model3_warp.json: right_side src_points x 정순 + y 범위 확대
- [ ] modely_warp.json: right_side src_points x 정순 + y 범위 확대
- [ ] generate_templates.py: 오른쪽 flip=False
- [ ] backend tests 업데이트
- [ ] test_colored_rect.py로 시각적 검증
- [ ] test_warp_local.py로 전체 파이프라인 검증
- [ ] 커밋

---

# (Archive) Plan: 유리 영역 분리 + 바디 전용 맵핑 (2026-03-06)

## 문제
1. 아이 템플릿의 유리(창문)가 너무 작음 → 실제 차 비율로 크게 키워야 함 (프레임만 남기고)
2. UV 맵핑 시 유리 영역까지 아이 그림이 칠해짐 → 바디만 맵핑되어야 함
3. UV 출력에서 유리 영역이 비어 보임 → 유리 틴트 효과 필요

## 접근 방식

### A. 아이 템플릿 유리 크기 확대 (generate_templates.py)
현재 유리(앞유리, 뒷유리)가 차 실루엣 대비 너무 작음.
실제 Tesla Model 3 비율에 맞게 유리를 대폭 확대:
- 사이드뷰: 윈드실드와 후면유리가 A/B/C 필러 사이를 거의 전부 채우도록
- 유리 하단 라인을 도어 핸들 바로 위 높이까지 내림
- 프레임(필러)만 남기고 나머지는 유리 영역으로

### B. UV 공간에 유리 제외 마스크 추가
- `model3_panels.json`에 `glass_regions` 폴리곤 좌표 추가
- `generate_uv_mask()`에서 glass_regions를 paintable mask에서 제외
- UV 유리 영역에 반투명 틴트 칼라 적용 (현실감)

### C. 워프 제어점 정밀화 (바디 중심 + 휠아치 정렬)
현재: 5×3 균일 격자 → 휠아치 곡선 추적 불가
변경:
- 상단 행을 유리 아래(바디 시작)로 이동
- 휠아치 근처에 제어점 추가 (5×3 → 7×3 이상)
- dst 제어점을 실제 UV 휠아치 위치에 맞춤

### D. 아이 템플릿 사이드뷰 좌우 확장
현재 차 실루엣이 패널 영역을 완전히 채우지 않음 → 범퍼/펜더 끝까지 확장하여
UV 템플릿 가장자리(노즈, 리어 범퍼)와 정렬

---

## 상세 구현

### 1. generate_templates.py — 유리 크기 확대

현재 유리 포인트:
```python
# 윈드실드 (너무 작음)
_MODEL3_WINDSHIELD = [
    (0.27, 0.44), (0.35, 0.17), (0.41, 0.10),
    (0.41, 0.16), (0.36, 0.38),
]
# 후면유리 (너무 작음)
_MODEL3_REAR_WINDOW = [
    (0.68, 0.10), (0.75, 0.25), (0.82, 0.43),
    (0.76, 0.42), (0.72, 0.28),
]
```

변경 방향:
- 유리 하단을 y≈0.50 정도까지 내림 (현재 ~0.43)
- 유리 상단은 루프라인에 더 가깝게
- 사이드 윈도우(도어 유리) 추가: 윈드실드~후면유리 사이 전체를 유리로 채움
- B필러(door_x=0.535) 양쪽의 도어 유리 표현

새 유리 영역 (Model 3):
```python
# 전체 사이드 윈도우 (도어 유리 포함)
_MODEL3_SIDE_WINDOWS = [
    # 윈드실드
    (0.27, 0.48), (0.35, 0.18), (0.41, 0.10),
    # 루프라인 따라
    (0.68, 0.10),
    # 후면유리
    (0.76, 0.26), (0.83, 0.48),
]
# 필러 라인으로 구분 (시각적 가이드)
# A필러: (0.33, 0.20) ~ (0.27, 0.48)
# B필러: (0.535 ± offset) 세로선
# C필러: (0.72, 0.20) ~ (0.83, 0.48)
```

### 2. model3_panels.json — glass_regions 추가

UV 공간에서 유리 영역 폴리곤:
```json
{
  "glass_regions": [
    {
      "name": "left_side_glass",
      "polygon": [
        [210, 131], [278, 131], [278, 994],
        [210, 994]
      ]
    },
    {
      "name": "right_side_glass",
      "polygon": [
        [749, 131], [817, 131], [817, 994],
        [749, 994]
      ]
    }
  ]
}
```
Note: 정확한 폴리곤은 UV 템플릿 아웃라인 분석 후 조정 필요.
좌측 스트립 x≈210~278 영역이 유리/상단 부분.

### 3. warping.py — generate_uv_mask() 수정

```python
def generate_uv_mask(uv_template, model):
    # 기존: 밝은 영역 = paintable
    gray = cv2.cvtColor(uv_template[:,:,:3], cv2.COLOR_RGB2GRAY)
    mask = ((gray > 200) & (alpha > 128)).astype(np.uint8) * 255

    # 추가: glass_regions 제외
    panels_config = load_panels_config(model)
    for region in panels_config.get("glass_regions", []):
        pts = np.array(region["polygon"], dtype=np.int32)
        cv2.fillPoly(mask, [pts], 0)  # 유리 영역 = 비페인팅

    return mask
```

### 4. compositing.py — 유리 틴트 적용

```python
def _apply_glass_tint(composited, model):
    """UV 유리 영역에 반투명 틴트 적용."""
    config = load_panels_config(model)
    tint_color = np.array([180, 200, 220, 180])  # 연한 블루 반투명
    for region in config.get("glass_regions", []):
        pts = np.array(region["polygon"], dtype=np.int32)
        glass_mask = np.zeros(composited.shape[:2], dtype=np.uint8)
        cv2.fillPoly(glass_mask, [pts], 255)
        # 블렌딩
        alpha = 0.3
        for c in range(3):
            composited[:,:,c] = np.where(
                glass_mask > 0,
                composited[:,:,c] * (1 - alpha) + tint_color[c] * alpha,
                composited[:,:,c]
            )
```

### 5. model3_warp.json — 제어점 정밀화 + 휠아치 정렬

UV 템플릿 실측 데이터:
```
왼쪽 스트립 (x=0-278):
  앞 휠아치: UV y ≈ 786-846 (폭 196→31→79, 깊이 있는 인덴트)
  뒤 휠아치: UV y ≈ 336-381 (폭 141→0→96, 패널 경계에서 끊김)
  도어 유리: UV y ≈ 436-465 (폭 240, 루프까지 확장)
  일반 바디: UV x ≈ 30-210 (폭 ~175)
  유리/상단: UV x ≈ 210-278 (바디 위 영역)
```

현재 5×3 격자 (열: x=20, 266, 512, 758, 1004):
→ 앞바퀴(kid x≈217)와 뒷바퀴(kid x≈778) 근처에 제어점 없음

변경: 7×3 격자로 확장, 휠아치 위치에 제어점 추가:
```json
{
  "name": "left_side",
  "src_points": [
    [20, 20], [217, 20], [400, 20], [512, 20], [625, 20], [778, 20], [1004, 20],
    [20, 205], [217, 205], [400, 205], [512, 205], [625, 205], [778, 205], [1004, 205],
    [20, 390], [217, 390], [400, 390], [512, 390], [625, 390], [778, 390], [1004, 390]
  ],
  "dst_points": [
    [278, 994], [278, 816], [278, 610], [278, 450], [278, 380], [278, 358], [278, 131],
    [146, 994], [146, 816], [146, 610], [146, 450], [146, 380], [146, 358], [146, 131],
    [14, 994], [14, 816], [14, 610], [14, 450], [14, 380], [14, 358], [14, 131]
  ]
}
```
핵심: kid x=217 → UV y=816 (앞 휠아치 중심), kid x=778 → UV y=358 (뒤 휠아치 중심)

---

## 변경 파일

| 파일 | 변경 |
|------|------|
| `scripts/generate_templates.py` | 유리 영역 대폭 확대 (사이드 윈도우 추가) |
| `backend/app/templates/model3_panels.json` | glass_regions 폴리곤 추가 |
| `backend/app/templates/modely_panels.json` | glass_regions 폴리곤 추가 |
| `backend/app/services/warping.py` | generate_uv_mask()에 glass 제외 로직 |
| `backend/app/services/compositing.py` | 유리 틴트 효과 적용 |
| `frontend/public/templates/` | 재생성된 PDF |

**변경 없음**: detection.py, removal.py, warping 엔진 코어, 프론트엔드 코드

---

## Todo

- [ ] generate_templates.py: 사이드뷰 유리 영역 대폭 확대 (필러만 남기고 전부 유리)
- [ ] generate_templates.py: 사이드뷰 차체 좌우 확장 (범퍼/펜더 끝까지)
- [ ] generate_templates.py: Model Y도 동일 적용
- [ ] model3_warp.json: 7×3 격자로 확장 + 휠아치 제어점 추가
- [ ] modely_warp.json: 동일 적용
- [ ] model3_panels.json: glass_regions UV 폴리곤 정의
- [ ] modely_panels.json: glass_regions UV 폴리곤 정의
- [ ] warping.py: generate_uv_mask()에서 glass_regions 제외
- [ ] compositing.py: 유리 틴트 효과 추가
- [ ] 템플릿 PDF 재생성
- [ ] 테스트 실행 및 통과
- [ ] 커밋
