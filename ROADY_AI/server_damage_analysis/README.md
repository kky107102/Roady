# ROADY 서버 AI 파손 분석 v2

Jira: `S15P11A404-168`

서버 AI는 Edge가 전송한 점자블록 기준 분석 ROI를 4클래스 Segmentation 모델로 분석합니다. 분석 전제조건을 검증할 수 없으면 비율이나 심각도를 확정하지 않고 `review_required=true`로 반환합니다.

## 모델 계약

필수 클래스는 `tactile_block`, `missing`, `crack`, `wear`입니다. 클래스 ID는 고정하지 않고 모델의 `names` 메타데이터로 확인합니다. 필수 클래스가 없으면 `MODEL_CLASS_MAPPING_INVALID`로 검토 전환합니다. 기존 2클래스 모델의 통합 `damage` 결과는 `missing ∪ crack ∪ wear`로 계산한 deprecated 호환 필드에서만 제공합니다.

## 분석 단위

- `block`: 모델이 개별 점자블록 인스턴스로 분리했고 형태 검사를 통과한 경우
- `block_group`: 여러 블록이 한 인스턴스로 연결되었거나 개별 블록 여부가 불명확한 경우

임의 격자나 영상처리로 블록을 강제 분할하지 않습니다. `block_group`에는 `BLOCK_INSTANCE_UNRESOLVED` 검토 사유가 추가됩니다. `local_unit_id`는 한 이미지 안에서만 유효합니다.

## Mask와 비율

- 균열과 마모: `type_mask ∩ tactile_unit_mask`
- 결손: tactile 교집합을 사용하지 않습니다. 주변 개별 블록의 크기와 간격이 안정적인 경우에만 `expected_block_region`을 사용합니다.
- expected region을 신뢰할 수 없으면 결손 비율과 심각도는 `null`, 상태는 `not_estimable`이며 0%나 임의 등급으로 바꾸지 않습니다. 보수 우선순위는 자동 판정이 아니라 `inspection_required`로 전환합니다.

| 비율 상태 | 의미 |
|---|---|
| `measured_no_damage` | 해당 유형 파손이 없어 0% |
| `estimated` | 유효 기준 영역에서 계산한 추정 비율 |
| `not_estimable` | 파손은 있으나 기준 영역을 검증할 수 없어 계산 불가 |

## 심각도 정책

정책은 [severity_policy.yaml](severity_policy.yaml)에 있습니다. 현재 `draft-1`은 검증된 행정 기준이 아닌 잠정 정책이므로 모든 결과는 `advisory_only=true`입니다. 유형별 하위 심각도와 `minimum_severity`를 적용한 뒤 가장 높은 등급을 분석 단위 등급으로 사용합니다. 마모에도 상한을 두지 않습니다.

## Edge 메타데이터와 품질 검토

서버는 `roi_source`, `roi_fallback_used`, `frame_quality_verified`를 입력 메타데이터로 받습니다. damage fallback ROI 또는 품질 미검증 프레임은 검토 사유로 전파됩니다. 메타데이터가 없으면 안전하게 `frame_quality_verified=false`로 간주합니다.

```json
{
  "original_image": "event_001_original.jpg",
  "analysis_roi": "event_001_analysis_roi.jpg",
  "roi_source": "tactile_block",
  "roi_fallback_used": false,
  "frame_quality_verified": true
}
```

## 실행

Edge pending 이벤트 JSON을 직접 분석할 때:

```bash
python -m ROADY_AI.server_damage_analysis.analyze_image \
  --model /path/to/4class_best.pt \
  --event-json /path/to/pending/damage_event.json \
  --output output --device cpu --imgsz 1024
```

이벤트 JSON의 `images[0]`은 원본 프레임, `images[1]`은 Server 분석 ROI로 처리합니다. 분석 ROI가 없으면 원본 프레임을 대신 분석하지 않고 입력 계약 오류를 반환합니다. 이미지 폴더가 기본 `pending/../images` 구조가 아니면 `--event-image-dir`로 지정합니다.

개별 ROI 파일을 직접 분석할 때:

```bash
python -m ROADY_AI.server_damage_analysis.analyze_image \
  --model /path/to/4class_best.pt \
  --image analysis_roi.jpg \
  --input-metadata input_metadata.json \
  --policy ROADY_AI/server_damage_analysis/severity_policy.yaml \
  --output output --device cpu --imgsz 1024
```

출력은 `analysis.json`, 원본 ROI 사본, Overlay, 통합 damage mask입니다. `units`와 `summary`가 v2 기준 응답이며 `regions`와 최상위 `analysis`는 deprecated 호환 필드입니다. 계약은 [response.schema.json](response.schema.json)을 참고합니다.

## 검토·Overlay·호환성

- 검토 코드와 관리자용 한국어 메시지는 [review_reasons.py](review_reasons.py)에서 관리하며 하위 검토는 전체 결과로 전파됩니다.
- Overlay는 tactile 외곽선과 missing/crack/wear mask를 구분하고 분석 단위 ID·비율·심각도·검토 여부를 표시합니다. 계산 불가 비율은 `ratio=?`입니다.
- 기존 원본/분석 이미지 저장 흐름과 `regions.damage`, `analysis.damage_ratio_percent`를 유지하지만 두 JSON 필드는 deprecated입니다.
- 현재 저장소의 `yolo26s_seg_v1_best.pt`는 2클래스 모델이므로 v2 분석용으로 사용할 수 없습니다. 배포 전 4클래스 모델을 별도 배치하고 메타데이터 검증을 통과해야 합니다.
- 모델 품질 게이트가 기준을 만족하지 않으면 계산 결과에도 `MODEL_QUALITY_GATE_NOT_MET` 검토 사유가 붙습니다.

## 개발 환경에서 테스트 재현

현재 ROADY 로컬 작업공간에서 검증에 사용한 Python은 저장소 루트의 `.venv-yolo`입니다. `numpy`, `opencv-python`, `pytest`, `ultralytics`가 설치되어 있습니다.

PowerShell:

```powershell
$env:PYTHONPATH='Roady_Embedded/src/perception;Roady_Embedded/src/storage'
& 'C:\Users\SSAFY\Desktop\ROADY\.venv-yolo\Scripts\python.exe' -m pytest `
  ROADY_AI/tests `
  Roady_Embedded/src/perception/test `
  Roady_Embedded/src/storage/test -q
```

Linux/Jupyter 환경에서는 별도의 가상환경에 테스트 의존성을 설치하고 다음과 같이 같은 테스트 경로를 실행합니다.

```bash
export PYTHONPATH="Roady_Embedded/src/perception:Roady_Embedded/src/storage"
python -m pytest ROADY_AI/tests \
  Roady_Embedded/src/perception/test \
  Roady_Embedded/src/storage/test -q
```

필수 테스트 패키지는 최소 `pytest`, `numpy`, `opencv-python`, `PyYAML`입니다. 실제 모델 샘플 추론에는 `ultralytics`와 대응되는 PyTorch 환경이 추가로 필요합니다.
