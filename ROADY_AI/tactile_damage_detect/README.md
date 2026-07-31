# 점자블록·파손 후보 탐지

Jira `S15P11A404-98`의 YOLO11n-detect 기반 점자블록 및 파손 후보 탐지 모델이다.

## 역할

주행 카메라의 전체 이미지에서 다음 두 클래스를 Bounding Box로 탐지한다.

- `tactile_block`: 선형·점형 점자블록
- `damage_candidate`: 균열·깨짐·결손·심한 마모로 의심되는 영역

이 모델의 목적은 파손을 최종 확정하는 것이 아니라 서버로 보낼 후보와 점자블록 ROI를 찾는 것이다. 오염·그림자·나뭇잎 등도 후보가 될 수 있다.

손상 유무 분류기는 이 Detect 결과의 점자블록 ROI를 입력받아 파손 여부를 다시 판단하는 별도 모델이며 이번 이슈에 포함하지 않는다.

## 현재 기준 모델

- 구조: YOLO11n Detect
- 입력: 640
- 학습: 20 Epoch 기준선
- 클래스 수: 2

Validation:

| 클래스 | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| `tactile_block` | 94.5% | 94.8% | 97.0% | 90.7% |
| `damage_candidate` | 59.9% | 44.7% | 46.1% | 23.7% |

점자블록은 안정적으로 탐지하지만 파손 후보 Recall은 운영 목표에 미달한다. 현장 데이터와 정제 라벨로 Fine-tuning하기 전까지 후보 탐지 기준선으로 사용한다.

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
  --data ROADY_AI/datasets/edge_detect_v1/dataset.yaml `
  --model yolo11n.pt `
  --epochs 20 `
  --imgsz 640 `
  --batch 8
```

## 카메라 확인

```powershell
python ROADY_AI/tactile_damage_detect/camera_test.py `
  --model ROADY_AI/models/edge/tactile_damage_candidate_yolo11n_best.pt `
  --camera 0 `
  --conf 0.15
```

## Jetson 변환

TensorRT 엔진은 JetPack·TensorRT 버전 영향을 받으므로 실제 Jetson에서 생성한다.

```bash
python ROADY_AI/tactile_damage_detect/export_jetson.py \
  --weights ROADY_AI/models/edge/tactile_damage_candidate_yolo11n_best.pt \
  --imgsz 640
```

생성되는 `.engine` 파일은 Git에 올리지 않는다.
