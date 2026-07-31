# 점자블록 ROI 손상 분류기

Jira `S15P11A404-225`의 점자블록 ROI 손상 분류기 모델이다.

## 역할

점자블록 Detect가 만든 ROI 또는 대표 타일을 다음 두 클래스로 분류한다.

- `damage_suspected`: 균열·깨짐·결손·심한 마모가 의심됨
- `normal`: 파손이 확인되지 않음

```text
점자블록 카메라
→ tactile_block Detect
→ 점자블록 ROI Crop
→ YOLO11n-cls @320
→ damage_score가 임계값 이상이면 서버 전송 후보
```

분류기는 파손의 정확한 Bounding Box, 유형, 면적, 비율을 출력하지 않는다. 미세 균열은 ROI 해상도와 학습 데이터에 충분히 보일 때만 `damage_suspected`로 분류할 수 있다.

## 모델과 성능

- 모델: YOLO11n-cls
- 입력: 320
- Test Accuracy: 89.6%
- 기본 임계값 0.5의 Damage Recall: 71.0%
- 후보 전송 권장 초기 임계값: 0.275

임계값 0.275 기준:

| Damage Recall | Damage Precision | False Positive Rate |
|---:|---:|---:|
| 85.0% | 62.9% | 13.7% |

Recall을 우선하기 위해 낮춘 초기값이다. 현장 연속 주행 데이터에서 오탐 이벤트/km와 서버·관리자 검토량을 함께 측정한 뒤 다시 보정해야 한다.

가중치:

```text
ROADY_AI/models/edge/damage_presence_yolo11n_cls_best.pt
```

SHA-256:

```text
dd80cf8c676a2bf0895d93d6335f9a0678f626386b87f6f8e887e3a7e13fe2d7
```

## 파일

```text
damage_classifier/
├─ build_dataset.py
├─ train.py
├─ evaluate.py
├─ predict.py
├─ export_jetson.py
└─ README.md
```

## 데이터 생성

Detect ROI 데이터의 비어 있지 않은 파손 라벨은 양성, 빈 라벨은 음성으로 변환한다.

```powershell
python ROADY_AI/damage_classifier/build_dataset.py `
  --source ROADY_AI/datasets/damage_tactile_roi_detect_v1 `
  --output ROADY_AI/datasets/damage_presence_cls_v1 `
  --train-negative-ratio 1.5
```

Train의 정상 이미지는 양성의 최대 1.5배로 제한하고 Validation과 Test는 고정 분포를 유지한다.

## 학습

```powershell
python ROADY_AI/damage_classifier/train.py `
  --data ROADY_AI/datasets/damage_presence_cls_v1 `
  --model yolo11n-cls.pt `
  --epochs 40 `
  --imgsz 320
```

## Test 및 임계값 분석

```powershell
python ROADY_AI/damage_classifier/evaluate.py `
  --model ROADY_AI/models/edge/damage_presence_yolo11n_cls_best.pt `
  --dataset ROADY_AI/datasets/damage_presence_cls_v1 `
  --source-detect ROADY_AI/datasets/damage_tactile_roi_detect_v1 `
  --output ROADY_AI/reports/damage_presence_test_analysis
```

Test를 반복해서 임계값 선정에 사용하지 않는다. 임계값은 Validation에서 선택하고 Test에서는 한 번 고정 평가한다.

## 단일 ROI 추론

```powershell
python ROADY_AI/damage_classifier/predict.py sample_roi.jpg `
  --model ROADY_AI/models/edge/damage_presence_yolo11n_cls_best.pt `
  --threshold 0.275
```

## Jetson 변환

TensorRT 엔진은 실제 Jetson에서 생성한다.

```bash
python ROADY_AI/damage_classifier/export_jetson.py \
  --weights ROADY_AI/models/edge/damage_presence_yolo11n_cls_best.pt \
  --imgsz 320
```

생성되는 `.engine` 파일은 Git에 올리지 않는다.
