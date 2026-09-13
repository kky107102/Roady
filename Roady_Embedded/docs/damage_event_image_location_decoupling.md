# 파손 이벤트 대표 이미지와 위치 선택 분리

## 1. 문서 목적

파손 이벤트에는 서버 분석용 이미지와 파손 위치가 함께 저장된다. 기존 구현은 하나의 대표 프레임을 선택한 뒤 그 프레임의 이미지와 당시 로봇 위치를 함께 사용한다.

하지만 두 값의 선택 목적은 다르다.

- 대표 이미지는 파손 상태를 분석하기 위해 최대한 선명하고 온전해야 한다.
- 이벤트 위치는 실제 파손 블록 좌표에 가까워지도록 로봇이 블록에 가장 근접한 시점의 좌표를 사용해야 한다.

따라서 이 문서는 대표 이미지 선택과 위치 선택을 하나의 프레임에 묶지 않고, 동일 track 안에서 독립적으로 선택하는 변경안을 정리한다.

> 이 문서의 내용은 현재 코드에 모두 적용된 결과가 아니라 후속 구현을 위한 설계안이다.

## 2. 현재 구현

현재 `DamageCandidate`는 대표 프레임과 위치를 하나의 선택 결과로 보관한다.

```text
best_original
best_analysis_roi
best_location
best_closeness_score
```

검증된 프레임 중 점자블록 ROI가 크고 화면 아래쪽에 위치한 프레임을 우선 선택하고, 해당 프레임의 이미지와 로봇 위치를 함께 저장한다.

```text
closeness_score
= 0.65 × ROI 면적 점수
+ 0.35 × ROI 하단 위치 점수
```

결과적으로 현재 구조는 다음과 같다.

```text
가까워 보이는 대표 프레임 선택
├─ 해당 프레임 이미지 저장
└─ 해당 프레임 촬영 시점의 로봇 위치 저장
```

## 3. 문제점

### 3.1 선명한 프레임과 가까운 프레임이 다를 수 있음

파손이 선명하게 촬영된 프레임이 항상 로봇과 가장 가까운 프레임은 아니다. 가까워질수록 다음 문제가 발생할 수 있다.

- 주행 진동과 motion blur 증가
- ROI 일부가 화면 밖으로 잘림
- Bounding box 면적이 급변해 안정성 조건 실패
- 가까운 구간에서 detection이 일시적으로 끊김

하나의 프레임으로 이미지와 위치를 동시에 결정하면 다음 중 하나를 희생해야 한다.

```text
선명한 이미지 선택 → 로봇 위치가 블록에서 상대적으로 멀 수 있음
가까운 위치 선택   → 저장 이미지가 흐리거나 잘릴 수 있음
```

### 3.2 저장 위치는 블록 좌표가 아닌 로봇 좌표

현재 저장되는 값은 실제 블록 위치가 아니라 대표 프레임 촬영 당시 로봇 위치다.

```text
현재 저장 위치 = 촬영 시점의 로봇 위치
원하는 위치     = 파손 블록의 실제 위치
```

따라서 로봇과 블록 사이의 거리가 클 때 선택된 위치일수록 블록 실제 위치와의 차이가 커질 수 있다.

### 3.3 위치 조건을 이벤트 생성 조건으로 사용하면 Recall이 감소할 수 있음

화면의 특정 ROI band에 블록이 도달했을 때만 이벤트를 만들면 가까운 위치를 얻을 수 있다. 하지만 다음 상황에서는 실제 파손 이벤트가 사라질 수 있다.

- 목표 band에 도달하기 전에 detection 종료
- 장애물 회피나 정차로 블록에 충분히 접근하지 않음
- 카메라 중심에서 벗어나 목표 band를 통과하지 않음
- 가까운 프레임이 blur 또는 경계 조건으로 탈락

파손 이벤트의 우선 요구사항은 실제 파손을 누락하지 않는 것이다. 위치 품질 조건이 Event Recall을 낮춰서는 안 된다.

## 4. 변경 목표

대표 이미지와 위치를 다음과 같이 독립적으로 선택한다.

```text
동일 파손 track
├─ 대표 이미지 후보
│  └─ 가장 선명하고 분석하기 좋은 검증 프레임
│
└─ 위치 후보
   └─ 파손 블록이 가장 가까워 보이는 검증 프레임의 로봇 위치
```

최종 이벤트 구성은 다음과 같다.

```text
이벤트 이미지 = 이미지 품질이 가장 높은 검증 프레임
이벤트 위치   = 가장 가까운 검증 프레임 시점의 로봇 위치
```

두 프레임의 timestamp는 서로 다를 수 있으며, 이 차이를 metadata로 명시한다.

## 5. 변경 전후 비교

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 대표 이미지 기준 | 가까움 점수 우선 | 선명도·ROI 완전성·안정성 우선 |
| 위치 기준 | 대표 이미지 시점 | 가장 가까운 검증 프레임 시점 |
| 이미지·위치 timestamp | 항상 동일 | 서로 다를 수 있음 |
| 위치 후보 실패 | 대표 이미지 위치 사용 | Fallback 위치와 품질 등급 저장 |
| 위치 조건과 Event Recall | 결합 가능성 있음 | 이벤트 확정과 완전히 분리 |
| 위치의 의미 | 대표 프레임 시점 로봇 좌표 | 가장 근접한 검증 시점의 로봇 좌표 |

## 6. 선택 기준

### 6.1 대표 이미지 선택

대표 이미지는 서버에서 파손 상태를 분석하기 적합한지를 기준으로 선택한다.

```text
image_quality_score
= 선명도
+ ROI 완전성
+ Detection confidence
+ ROI 안정성
```

필수 조건은 다음과 같다.

- `tactile_block`과 `damage_candidate` 관계가 확인됨
- ROI 최소 폭·높이·면적 충족
- 프레임 경계에서 지나치게 잘리지 않음
- 최소 선명도 충족
- ROI 면적과 중심점 변화가 허용 범위 이내

이 조건을 통과한 프레임 중 `image_quality_score`가 가장 높은 이미지를 저장한다.

### 6.2 위치 선택

위치는 파손 블록이 로봇에 가장 가까워 보이는 검증 프레임에서 선택한다.

```text
location_closeness_score
= ROI 면적 점수
+ ROI 하단 위치 점수
+ 목표 band 접근 점수
```

위치 후보도 최소한 다음 조건을 통과해야 한다.

- 점자블록과 파손 관계가 확인됨
- Bounding box가 비정상적으로 튀지 않음
- ROI가 화면에서 완전히 사라지거나 과도하게 잘리지 않음
- 촬영 시점의 유효한 로봇 위치가 존재함

가장 마지막 프레임을 무조건 선택하지 않고, 검증된 후보 중 가장 가까움 점수가 높은 시점을 선택한다.

## 7. 데이터 구조 변경안

현재 하나로 묶인 이미지·위치 상태를 다음과 같이 분리한다.

```python
@dataclass
class DamageCandidate:
    # 대표 이미지 선택 결과
    best_image_original: np.ndarray | None = None
    best_image_roi: np.ndarray | None = None
    best_image_quality: float = -1.0
    best_image_timestamp: float | None = None

    # 위치 선택 결과
    closest_location: tuple[float, float] | None = None
    closest_location_score: float = -1.0
    closest_location_timestamp: float | None = None
    closest_location_roi_bbox: BBox | None = None
```

프레임 관찰 시 두 후보를 독립적으로 갱신한다.

```python
if image_verified and image_quality > candidate.best_image_quality:
    candidate.best_image_original = frame.copy()
    candidate.best_image_roi = analysis_roi
    candidate.best_image_quality = image_quality
    candidate.best_image_timestamp = timestamp

if location_verified and closeness_score > candidate.closest_location_score:
    candidate.closest_location = location
    candidate.closest_location_score = closeness_score
    candidate.closest_location_timestamp = timestamp
    candidate.closest_location_roi_bbox = roi_bbox
```

최종 이벤트 생성 시 두 결과를 결합한다.

```python
ReadyDamageEvent(
    original_image=candidate.best_image_original,
    analysis_roi=candidate.best_image_roi,
    location=candidate.closest_location,
)
```

## 8. Metadata 변경안

이미지와 위치의 선택 기준과 timestamp를 분리해 기록한다.

```json
{
  "representative_frame": {
    "selection": "highest_verified_image_quality",
    "timestamp": 10.2,
    "quality_score": 0.91
  },
  "event_location": {
    "selection": "closest_verified_tactile_roi",
    "timestamp": 10.8,
    "closeness_score": 0.89,
    "quality": "HIGH"
  }
}
```

이 Metadata를 통해 이미지와 위치가 서로 다른 시점에서 선택됐음을 명확하게 확인할 수 있다.

## 9. Fallback 정책

위치 품질 때문에 실제 파손 이벤트를 폐기하지 않는다.

| 상황 | 이벤트 | 위치 선택 | 위치 품질 |
|---|---|---|---|
| 목표 band에 도달한 검증 프레임 존재 | 생성 | 해당 시점 로봇 위치 | `HIGH` |
| Band 미도달, 가까움 후보 존재 | 생성 | 최고 closeness 후보 위치 | `ESTIMATED` |
| 유효 위치가 없고 대표 이미지 위치 존재 | 생성 | 대표 이미지 시점 위치 | `FALLBACK` |
| 유효 위치가 전혀 없음 | 생성 | 위치 없음 | `UNAVAILABLE` |

핵심 원칙은 다음과 같다.

> 이벤트 생성 여부는 파손 검출 신뢰도로 결정하고, 위치 품질은 별도의 등급으로 표현한다.

## 10. 기대 효과

### 10.1 이미지 분석 품질 보존

가까운 위치를 선택하기 위해 흐리거나 잘린 프레임을 대표 이미지로 저장하지 않는다. 서버에는 track 전체에서 가장 분석하기 좋은 이미지를 전달한다.

### 10.2 블록 위치 근사 오차 감소

대표 이미지가 멀리서 촬영됐더라도 위치는 더 가까운 시점의 로봇 좌표를 사용할 수 있다. 이를 통해 로봇 위치를 블록 위치로 근사할 때 발생하는 거리 차이를 줄일 수 있다.

### 10.3 Event Recall 보존

목표 band에 도달하지 못하거나 가까운 프레임 품질이 낮아도 파손 이벤트는 유지한다. 위치 품질 조건이 실제 파손 이벤트 누락으로 이어지지 않는다.

### 10.4 문제 추적 가능성 향상

이미지와 위치 선택 timestamp, 점수와 품질 등급을 저장하므로 위치가 멀리 기록된 원인을 사후 분석할 수 있다.

## 11. 검증 지표

변경 효과는 다음 지표로 평가한다.

| 구분 | 지표 |
|---|---|
| 이벤트 품질 | Event Recall, Precision, 중복률 |
| 이미지 품질 | 대표 이미지 선명도, ROI 완전성, 서버 분석 성공률 |
| 위치 품질 | 목표 band 선택률, Fallback 비율, 선택 시점의 closeness score |
| 위치 정확도 | 실제 블록 좌표 대비 거리 오차 평균·중앙값·p95 |
| 반복 주행 일관성 | 동일 블록의 저장 위치 분산 |

현재 영상에는 프레임별 위치 로그와 실제 블록 측량 좌표가 없으므로 위치 정확도 개선은 아직 수치화할 수 없다. 향후 영상 timestamp, 로봇 pose와 블록 ground truth 좌표를 함께 수집해야 한다.

## 12. 남는 한계와 후속 개선

이미지와 위치 선택을 분리해도 저장되는 위치는 블록 자체 좌표가 아니라 가장 가까워 보이는 시점의 로봇 좌표다. 따라서 이 변경만으로 블록 위치를 완벽하게 계산할 수는 없다.

정확한 블록 절대 위치가 필요하면 다음 정보가 필요하다.

- 카메라 내부 파라미터
- 카메라 높이와 설치 각도
- 카메라와 로봇 좌표계 관계
- 촬영 시점 로봇 pose와 진행 방향
- 바닥 평면 homography

향후에는 이미지의 블록 기준점을 바닥 좌표계로 투영해 로봇과 블록 사이의 상대 위치를 계산할 수 있다.

```text
블록 추정 위치
= 촬영 시점 로봇 pose
+ 카메라로 계산한 블록 상대 위치
```

이 단계가 적용되면 블록이 멀리 있을 때도 로봇 위치를 그대로 저장하지 않고 실제 블록 위치 방향으로 보정할 수 있다.

## 13. 구현 순서

1. `DamageCandidate`의 이미지 후보와 위치 후보 필드 분리
2. 이미지 품질 점수와 위치 closeness 점수 독립 계산
3. 위치 후보용 목표 band와 검증 조건 추가
4. `ReadyDamageEvent` 생성 시 이미지와 위치 결과 결합
5. Metadata에 두 선택의 timestamp와 품질 등급 기록
6. Band 미도달 및 위치 없음에 대한 Fallback 구현
7. 기존 Event Recall·중복 단위 테스트 유지
8. 대표 이미지 선택과 위치 선택이 서로 다른 프레임을 사용하는 테스트 추가
9. 실제 주행 로그로 위치 오차와 반복 주행 분산 검증

## 14. 결론

기존 구조는 대표 이미지와 위치를 하나의 프레임에서 선택해 이미지 분석 품질과 위치 근접성 사이에 충돌이 있었다. 이를 해결하기 위해 동일 track 안에서 대표 이미지는 가장 선명하고 분석하기 좋은 검증 프레임으로, 위치는 파손 블록이 가장 가까워 보이는 검증 프레임 시점의 로봇 좌표로 독립 선택한다.

이 변경은 이미지 품질을 유지하면서 블록 위치 근사 오차를 줄이고, 위치 조건 때문에 실제 파손 이벤트가 누락되는 것을 방지한다. 다만 저장 위치는 여전히 로봇 좌표 기반 근삿값이므로 정확한 블록 절대 위치가 필요하면 카메라 calibration과 ground-plane projection을 이용한 상대 위치 보정이 추가로 필요하다.
