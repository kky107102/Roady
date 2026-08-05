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
- 학습: YOLO26n 기준 모델에서 시연환경 검수 데이터 Fine-tuning
- 클래스 수: 2

고정 Test 15장 평가:

| 클래스 | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| `tactile_block` | 92.4% | 94.8% | 96.2% | 90.7% |
| `damage_candidate` | 84.6% | 76.9% | 85.4% | 61.5% |

기존 YOLO26n 기준 모델 대비 파손 후보 Recall은 73.1%에서 76.9%, F2-score는 0.760에서 0.783으로 개선됐다. Edge AI는 파손을 최종 확정하지 않고 서버 정밀 분석 대상으로 전달하므로 Recall과 F2-score를 우선한다.

모델 파일:

```text
ROADY_AI/models/edge/tactile_damage_candidate_yolo26n_best.pt
```

SHA-256:

```text
488e33c14e3d3fb2a764da05ce4cf7d8b38d783993f1bb1600018c73b80db388
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
  --data ROADY_AI/datasets/edge_yolo26n_detect_review_ft_v3/dataset.yaml `
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
