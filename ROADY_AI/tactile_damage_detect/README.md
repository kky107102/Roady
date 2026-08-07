# 점자블록·파손 후보 탐지

Jira `S15P11A404-98`의 YOLO26n Detect 기반 점자블록 및 파손 후보 탐지 모델이다.

## 역할

주행 카메라의 전체 이미지에서 다음 두 클래스를 Bounding Box로 탐지한다.

- `tactile_block`: 선형·점형 점자블록
- `damage_candidate`: 균열·깨짐·결손·심한 마모로 의심되는 영역

이 모델의 목적은 파손을 최종 확정하는 것이 아니라 서버로 보낼 후보와 점자블록 ROI를 찾는 것이다. 오염·그림자·나뭇잎 등도 후보가 될 수 있다.

손상 유무 분류기는 이 Detect 결과의 점자블록 ROI를 입력받아 파손 여부를 다시 판단하는 별도 모델이며 이번 이슈에 포함하지 않는다.

## 현재 기준 모델

- 구조: YOLO26n Detect
- 입력: 768
- 모델 버전: `edge_yolo26n_balanced_replay_v3`
- 시작 가중치: 큰 결손 탐지가 안정적이었던 기존 v1 `best.pt`
- 학습: 큰 결손 Replay와 신규 마모 데이터를 균형 구성한 Fine-tuning
- 클래스 수: 2

시연환경과 분리한 고정 Test 37장 평가(`imgsz=768`, 2026-08-07 재검증):

| 클래스 | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| `tactile_block` | 92.5% | 95.0% | 98.3% | 93.0% |
| `damage_candidate` | 80.0% | 74.1% | 85.7% | 67.9% |

동일한 고정 Test에서 직전 모델의 `damage_candidate` 성능은 Precision 86.2%, Recall 69.6%, mAP50 75.9%, mAP50-95 58.1%였다. 새 균형 Replay 모델은 Precision이 일부 낮아졌지만 Recall은 4.5%p, mAP50은 9.8%p, mAP50-95는 9.8%p 개선됐으며 F2-score는 약 0.752이다. Edge AI는 파손을 최종 확정하지 않고 서버 정밀 분석 대상으로 전달하므로 Recall과 F2-score를 우선한다.

학습 표본은 원본 유형 기준으로 큰 결손 30%, 마모 30%, 작은 결손·균열 등 기타 파손 25%, 흙·낙엽 등 Hard Negative 15%가 되도록 구성했다. 씽씽이는 현 결정에 따라 `damage_candidate` 후보에 포함하며, 서버에서 분석 불확실 시 판단 보류 대상으로 처리한다.

평가 중 일부 정답 파일에서 중복 라벨이 제거되었다. 다음 데이터셋 버전에서는 중복 Polygon을 정리한 뒤 같은 고정 Test로 재평가한다.

모델 파일:

```text
ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt
```

SHA-256:

```text
085684f195398ba0af8cbea1a104a116ca4b71e41b9005bb2cdd1affd30868a7
```

기존 YOLO11n 모델과 별도 손상 분류기는 운영 대상에서 제외한다.

## 파일

```text
tactile_damage_detect/
├─ build_dataset.py
├─ validate_dataset.py
├─ train.py
├─ camera_test.py
├─ export_jetson.py
└─ README.md
```

## 데이터셋 생성

대용량 이미지와 라벨은 Git에 포함하지 않는다.

```powershell
python ROADY_AI/tactile_damage_detect/build_dataset.py `
  --manifest ROADY_AI/datasets/tactile_combined_v1.csv `
  --output ROADY_AI/datasets/edge_detect_v1 `
  --resume
```

출력 `dataset.yaml`:

```yaml
names:
  0: tactile_block
  1: damage_candidate
```

## 검증

```powershell
python ROADY_AI/tactile_damage_detect/validate_dataset.py `
  --dataset ROADY_AI/datasets/edge_detect_v1 `
  --report ROADY_AI/reports/edge_detect_v1_validation.json `
  --overlays ROADY_AI/reports/edge_detect_v1_overlays
```

## 학습

```powershell
python ROADY_AI/tactile_damage_detect/train.py `
  --data ROADY_AI/datasets/edge_balanced_replay_v3/dataset.yaml `
  --model ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt `
  --epochs 30 `
  --imgsz 768 `
  --batch 16
```

## 카메라 확인

```powershell
python ROADY_AI/tactile_damage_detect/camera_test.py `
  --model ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt `
  --camera 0 `
  --imgsz 768 `
  --conf 0.10 `
  --damage-only
```

## Jetson 변환

TensorRT 엔진은 JetPack·TensorRT 버전 영향을 받으므로 실제 Jetson에서 생성한다.

```bash
python ROADY_AI/tactile_damage_detect/export_jetson.py \
  --weights ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt \
  --imgsz 768
```

생성되는 `.engine` 파일은 Git에 올리지 않는다.

TensorRT 엔진은 Jetson Orin Nano에서 직접 생성하고 FP16, batch 1 조건으로 FPS 15 이상 및 전체 메모리 4GB 이하를 실측한다. 배포 성능이 목표에 미달하면 입력 크기 640 또는 기존 YOLO11n 모델을 롤백 후보로 사용한다.

## 현장 검수

학습·Validation·Test와 겹치지 않는 시연환경 원본 100장으로 별도 추론 결과를 생성한다. 정답 라벨이 없는 현장 이미지는 탐지 수만으로 성능을 확정하지 않고, 오탐·미탐을 수동 검수한 뒤 Precision, Recall, F2-score를 계산한다.
