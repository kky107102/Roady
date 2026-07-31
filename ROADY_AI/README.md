# ROADY AI — Edge 모델

ROADY 로봇의 Edge AI 학습·평가·배포 코드를 관리한다.

## 현재 기능

Jetson Orin Nano 8GB에서 두 카메라를 분리해 사용한다.

```text
장애물용 USB 카메라
→ YOLO11n Detect @640
→ foot / lower_leg Bounding Box
→ 하나 이상 탐지되면 human_lower_limb_detected=true

점자블록용 카메라
→ YOLO11n Detect @640
→ tactile_block / damage_candidate Bounding Box
→ 점자블록 ROI와 서버 전송 후보 생성
```

카메라 AI는 LiDAR의 CPU 기반 안전 정지 기능을 보조한다. 장애물 AI 결과만으로 로봇의 최종 안전을 보장하지 않는다.

손상 유무 분류기는 Detect가 만든 점자블록 ROI를 재판정하고 서버 전송 후보를 결정한다.

## 구성

```text
ROADY_AI/
├─ obstacle_lower_limb/
│  ├─ build_coco_body_part.py
│  ├─ camera_test.py
│  ├─ capture_frames.py
│  ├─ dataset.yaml
│  ├─ export_jetson.py
│  ├─ train.py
│  ├─ validate_dataset.py
│  └─ README.md
├─ tactile_damage_detect/
│  ├─ build_dataset.py
│  ├─ validate_dataset.py
│  ├─ train.py
│  ├─ camera_test.py
│  ├─ export_jetson.py
│  └─ README.md
├─ damage_classifier/
│  ├─ build_dataset.py
│  ├─ train.py
│  ├─ evaluate.py
│  ├─ predict.py
│  ├─ export_jetson.py
│  └─ README.md
├─ models/edge/
│  ├─ obstacle_lower_limb_yolo11n_best.pt
│  ├─ tactile_damage_candidate_yolo11n_best.pt
│  └─ damage_presence_yolo11n_cls_best.pt
├─ .gitignore
├─ requirements.txt
└─ README.md
```

## 장애물 모델

- 구조: YOLO11n Detect
- 클래스: `foot`, `lower_leg`
- 입력: 640
- 초기 가중치: Ultralytics COCO 사전학습 `yolo11n.pt`
- 배포 목표: Jetson TensorRT FP16

최종 Test 결과:

| Precision | Recall | mAP50 | mAP50-95 |
|---:|---:|---:|---:|
| 86.6% | 68.6% | 78.2% | 40.7% |

클래스 Recall:

- `foot`: 67.8%
- `lower_leg`: 69.5%

가중치:

```text
ROADY_AI/models/edge/obstacle_lower_limb_yolo11n_best.pt
```

SHA-256:

```text
072dc889d93b01274cf2fdb6cce1d1922b0da91aa8609c2dbcfa91a6d3cd7b44
```

## 설치

```powershell
cd ROADY_AI
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

Jetson에서는 JetPack에 맞는 PyTorch와 TensorRT를 먼저 설치한다.

## 학습

데이터셋은 Git에 포함하지 않는다. `dataset.yaml` 기준 구조로 준비한 후 저장소 루트에서 실행한다.

```powershell
python ROADY_AI/obstacle_lower_limb/train.py `
  --data ROADY_AI/obstacle_lower_limb/dataset.yaml `
  --weights yolo11n.pt `
  --epochs 50 `
  --imgsz 640
```

## 데이터 검증

```powershell
python ROADY_AI/obstacle_lower_limb/validate_dataset.py `
  --dataset ROADY_AI/datasets/obstacle_lower_limb_v1
```

## 카메라 추론

PyTorch 가중치 테스트:

```powershell
python ROADY_AI/obstacle_lower_limb/camera_test.py `
  --model ROADY_AI/models/edge/obstacle_lower_limb_yolo11n_best.pt `
  --camera 0 `
  --imgsz 640
```

TensorRT 엔진은 실제 Jetson에서 생성하며 Git에 올리지 않는다.

## 점자블록·파손 후보 모델

- 구조: YOLO11n Detect
- 클래스: `tactile_block`, `damage_candidate`
- 입력: 640
- 역할: 파손 최종 확정이 아닌 점자블록 ROI와 서버 전송 후보 생성

Validation:

| 클래스 | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| `tactile_block` | 94.5% | 94.8% | 97.0% | 90.7% |
| `damage_candidate` | 59.9% | 44.7% | 46.1% | 23.7% |

가중치:

```text
ROADY_AI/models/edge/tactile_damage_candidate_yolo11n_best.pt
```

자세한 학습·검증·카메라 실행 방법은 [`tactile_damage_detect/README.md`](tactile_damage_detect/README.md)를 확인한다.

## 점자블록 ROI 손상 분류기

- 구조: YOLO11n Classification
- 클래스: `damage_suspected`, `normal`
- 입력: 점자블록 ROI 320
- 역할: Detect가 만든 점자블록 ROI의 손상 유무 재판정
- Test Accuracy: 89.6%
- 후보 전송 권장 초기 임계값: 0.275

임계값 0.275에서 Damage Recall 85.0%, Precision 62.9%다. 정확한 파손 위치·유형·면적은 출력하지 않는다.

가중치:

```text
ROADY_AI/models/edge/damage_presence_yolo11n_cls_best.pt
```

자세한 데이터 생성·학습·평가·추론 방법은 [`damage_classifier/README.md`](damage_classifier/README.md)를 확인한다.
