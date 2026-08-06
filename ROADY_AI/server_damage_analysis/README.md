# ROADY 서버 AI 파손 분석 v2

Jira: `S15P11A404-168`

서버 AI는 Edge가 전송한 점자블록 기준 ROI를 4클래스 Segmentation 모델로 분석합니다. 분석 전제조건을 검증할 수 없으면 비율이나 심각도를 확정하지 않고 `null`, `review_required=true`, `advisory_only=true`로 반환합니다.

## 모델 계약

필수 클래스는 `tactile_block`, `missing`, `crack`, `wear`입니다. 클래스 ID를 고정하지 않고 모델의 `names` 메타데이터를 검사합니다. 필수 클래스가 없으면 `MODEL_CLASS_MAPPING_INVALID`로 검토 전환합니다. 기존 통합 `damage` 결과는 `missing ∪ crack ∪ wear`로 계산한 deprecated 호환 필드에서만 제공합니다.

## 분석 단위

- `block`: 모델이 개별 점자블록 인스턴스로 분리했고 형태 검사를 통과한 경우
- `block_group`: 여러 블록이 연결되었거나 개별 블록 여부가 불명확한 경우

블록을 임의 격자로 강제 분할하지 않습니다. `block_group`에는 `BLOCK_INSTANCE_UNRESOLVED` 검토 사유를 추가하며 `local_unit_id`는 한 이미지 안에서만 유효합니다.

## Mask와 비율

- 균열과 마모: `type_mask ∩ tactile_unit_mask`
- 결손: tactile 교집합을 사용하지 않습니다. 주변 개별 블록의 크기와 간격이 안정적인 경우에만 `expected_block_region`을 사용합니다.
- expected region을 신뢰할 수 없으면 결손 비율과 심각도는 `null`, 상태는 `not_estimable`입니다. 0%나 임의 등급으로 바꾸지 않고 보수 우선순위를 `inspection_required`로 전환합니다.

| 비율 상태 | 의미 |
|---|---|
| `measured_no_damage` | 해당 유형 파손이 없어 0% |
| `estimated` | 유효 기준 영역에서 계산한 추정 비율 |
| `not_estimable` | 파손은 있으나 기준 영역을 검증할 수 없어 계산 불가 |

## 심각도 정책

정책은 [severity_policy.yaml](severity_policy.yaml)에 있습니다. 현재 `draft-1`은 검증된 행정 기준이 아닌 잠정 정책이므로 모든 결과는 `advisory_only=true`입니다. 유형별 심각도와 `minimum_severity`를 적용한 뒤 가장 높은 등급을 분석 단위 등급으로 사용합니다. 마모에도 상한을 두지 않습니다.

## Edge 입력 계약

서버는 `roi_source`, `roi_fallback_used`, `frame_quality_verified`를 입력 메타데이터로 받습니다. damage fallback ROI 또는 품질 미검증 프레임은 검토 사유로 전파됩니다. 이벤트 JSON의 `images[0]`은 원본 프레임, `images[1]`은 분석 ROI입니다. 분석 ROI가 없으면 원본을 대신 분석하지 않습니다.

```json
{
  "original_image": "event_001_original.jpg",
  "analysis_roi": "event_001_analysis_roi.jpg",
  "roi_source": "tactile_block",
  "roi_fallback_used": false,
  "frame_quality_verified": true
}
```

## 명령행 실행

Edge 이벤트 JSON:

```bash
python -m ROADY_AI.server_damage_analysis.analyze_image \
  --model /path/to/4class_best.pt \
  --event-json /path/to/pending/damage_event.json \
  --output output --device cpu --imgsz 1024
```

개별 ROI:

```bash
python -m ROADY_AI.server_damage_analysis.analyze_image \
  --model /path/to/4class_best.pt \
  --image analysis_roi.jpg \
  --input-metadata input_metadata.json \
  --policy ROADY_AI/server_damage_analysis/severity_policy.yaml \
  --output output --device cpu --imgsz 1024
```

출력은 `analysis.json`, ROI 사본, Overlay, 통합 damage mask입니다. `units`와 `summary`가 v2 기준 응답이며 `regions`와 최상위 `analysis`는 deprecated 호환 필드입니다.

## FastAPI

Spring의 Redis Queue Worker가 호출하는 동기식 분석 API입니다. Redis Queue와 작업 상태는 Spring이 관리하며 AI 서버는 DB나 Redis에 직접 연결하지 않습니다.

```bash
uvicorn ROADY_AI.server_damage_analysis.api:app \
  --host 0.0.0.0 --port 8000 --workers 1
```

- `POST /analyze`: Spring multipart 요청 분석
- `GET /health/live`: 프로세스 생존 확인
- `GET /health/ready`: 모델 로딩 완료 확인
- `GET /model-info`: 실제 모델 파일명, SHA-256, 클래스 매핑 확인

Spring은 최상위 요약 필드를 구조화된 컬럼으로 파싱하고 응답 전체를 `raw_result`에 보존합니다. 계산 불가 결손은 `damaged=true`이지만 `damage_score`, `repair_required`, 비율, 심각도가 `null`일 수 있습니다. 백엔드 필드는 nullable 타입을 사용하며 이를 0 또는 `false`로 치환하면 안 됩니다.

```json
{
  "damaged": true,
  "damage_score": null,
  "damage_type": null,
  "repair_required": null,
  "repair_priority": null,
  "confidence_score": 0.82,
  "analysis_detail": {
    "schema_version": "2.0",
    "damage_ratio": null,
    "damage_ratio_percent": null,
    "estimated_severity": null,
    "review_required": true,
    "advisory_only": true
  }
}
```

외부 API 스키마는 [api_response.schema.json](api_response.schema.json), 상세 분석 스키마는 [response.schema.json](response.schema.json)을 참고합니다.

## Docker

```bash
docker build -f ROADY_AI/Dockerfile -t roady-ai:latest .
docker run --rm --gpus all -e ROADY_AI_DEVICE=0 -p 8000:8000 roady-ai:latest
```

CPU에서는 `ROADY_AI_DEVICE=cpu`를 사용합니다. GPU 서버는 시작 단계에서 모델 SHA-256 검증과 워밍업을 완료한 뒤 `/health/ready`를 활성화합니다.

## Overlay와 하위 호환성

- 검토 코드와 한국어 메시지는 [review_reasons.py](review_reasons.py) 한곳에서 관리합니다.
- Overlay는 tactile 외곽선과 missing/crack/wear mask, 분석 단위 ID, 비율, 심각도, 검토 여부를 표시합니다. 계산 불가 비율은 `ratio=?`입니다.
- 기존 이미지 저장 흐름과 `regions.damage`, `analysis.damage_ratio_percent`는 유지하지만 deprecated입니다.
- 저장소의 기존 `yolo26s_seg_v1_best.pt`는 2클래스이므로 v2 분석에 사용할 수 없습니다. 배포 전 4클래스 가중치를 배치해야 합니다.
- 모델 품질 게이트 미달 시 `MODEL_QUALITY_GATE_NOT_MET` 검토 사유가 추가됩니다.

## 테스트

PowerShell:

```powershell
$env:PYTHONPATH='Roady_Embedded/src/perception;Roady_Embedded/src/storage'
& 'C:\Users\SSAFY\Desktop\ROADY\.venv-yolo\Scripts\python.exe' -m pytest `
  ROADY_AI/tests `
  Roady_Embedded/src/perception/test `
  Roady_Embedded/src/storage/test -q
```

Linux/Jupyter:

```bash
export PYTHONPATH="Roady_Embedded/src/perception:Roady_Embedded/src/storage"
python -m pytest ROADY_AI/tests \
  Roady_Embedded/src/perception/test \
  Roady_Embedded/src/storage/test -q
```

필수 테스트 패키지는 `pytest`, `numpy`, `opencv-python`, `PyYAML`입니다. 실제 모델 추론에는 `ultralytics`와 대응 PyTorch 환경이 추가로 필요합니다.
