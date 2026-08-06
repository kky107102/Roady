# 서버 AI 점자블록 파손 분석 v1

Jira: `S15P11A404-168`

YOLO26s-seg v1의 Mask를 관리자 화면에서 사용할 수 있는 분석 JSON과 시각화 이미지로 변환한다.

## 제공 기능

- Mask IoU 기반 중복 인스턴스 제거
- 여러 파손 후보 Mask의 합집합 생성
- `damage ∩ tactile_block`만 유효 파손 면적으로 계산
- 점자블록 대비 파손 픽셀 비율 계산
- 정상/경미/보통/심각 추정 및 보수 우선순위 매핑
- 모델·이미지·경계 신뢰도 기반 `review_required` 판단
- 점자블록 얇은 윤곽선과 파손 반투명 Mask가 포함된 Overlay 생성
- 원본·Overlay·Mask 파일명과 Polygon 좌표를 포함한 JSON 반환

프론트엔드는 JSON의 Polygon/파일 URL을 표시하고, 백엔드는 이미지 저장 및 URL 치환을 담당한다.

## 모델

`models/server/yolo26s_seg_v1_best.pt`

클래스는 `0: tactile_block`, `1: damage`이다. SHA-256은 같은 폴더의 `.sha256` 파일에서 확인한다.

## 실행

```bash
python -m ROADY_AI.server_damage_analysis.analyze_image \
  --model ROADY_AI/models/server/yolo26s_seg_v1_best.pt \
  --image sample.jpg --output output --device cpu --imgsz 1024
```

출력은 `analysis.json`, Overlay, 이진 Damage Mask이다. API 계약은 `response.schema.json`을 따른다.

## 판정 정책

| 파손 비율 | 추정 심각도 | 보수 우선순위 |
|---:|---|---|
| 0.5% 미만 | 정상 추정 | 이상 없음 |
| 0.5% 이상 5% 미만 | 경미 추정 | 경과 관찰 |
| 5% 이상 15% 미만 | 보통 추정 | 보수 확인 필요 |
| 15% 이상 | 심각 추정 | 보수 필수 후보 |

현재 v1은 후보 중 가장 우수하지만 정밀 면적·심각도 자동 확정 기준은 충족하지 못했다. 따라서 추정값을 제공하되 `review_required=true`, `advisory_only=true`를 반환한다.

- Damage F2: 0.8261
- Positive Damage Dice: 0.0830
- 파손 비율 MAE: 6.085%p
- 심각도 Macro-F1: 0.2187

## 책임 범위

- AI: Mask 병합, 비율·등급·우선순위·검토 판단, Polygon/Mask/JSON 생성
- 백엔드: 원본·분석 이미지 저장, URL 발급, 분석 이력 저장
- 프론트엔드: 원본/분석 비교 UI, Polygon/테두리 표시, 담당자 검토 UI
