# Computer Vision & YOLO 학습노트

## 1. 학습 목적

SafeWalk Scout에서 카메라 영상으로 점자블록과 파손 부위를 인식하려면 Computer Vision의 기본 원리와 실시간 객체 탐지 모델을 이해해야 한다. 특히 Jetson Orin Nano에서 실시간으로 파손 후보를 선별해야 하므로 정확도뿐 아니라 추론 속도와 메모리 사용량도 함께 고려해야 한다.

이번 학습의 목표는 다음과 같다.

- 이미지 분류, 객체 탐지, 세그멘테이션의 차이를 이해한다.
- YOLO가 객체의 위치와 종류를 예측하는 방식을 이해한다.
- AI Hub polygon 라벨을 YOLO Segmentation 학습에 활용하는 방법을 정리한다.
- 모델을 평가할 때 Precision, Recall, IoU, mAP를 해석할 수 있다.
- 학습 모델을 ONNX와 TensorRT로 변환하여 Jetson에 배포하는 과정을 이해한다.

## 2. Computer Vision 기초

### 2.1 디지털 이미지

이미지는 픽셀의 집합이며 RGB 이미지는 각 픽셀마다 Red, Green, Blue의 세 값을 가진다. 일반적으로 딥러닝 모델에는 `(높이, 너비, 채널)` 형태의 이미지를 일정한 입력 크기로 변환해 넣는다.

주요 전처리는 다음과 같다.

- **Resize:** 모델 입력 크기에 맞게 이미지 크기를 변경한다.
- **Normalization:** 픽셀 값을 일정 범위로 조정하여 학습을 안정화한다.
- **Crop:** 필요한 영역만 잘라 배경 영향을 줄인다.
- **Color conversion:** OpenCV의 BGR과 일반적인 RGB 순서 차이를 처리한다.
- **Augmentation:** 밝기, 회전, blur, noise 등을 적용해 다양한 환경에 대응한다.

점자블록 프로젝트에서는 햇빛, 그림자, 오염, 카메라 진동과 촬영 각도가 주요 변수이므로 실제 환경과 비슷한 증강이 필요하다.

### 2.2 CNN의 역할

CNN은 작은 필터를 이미지에 적용해 선, 모서리, 질감 같은 특징을 추출하고, 깊은 층으로 갈수록 점자 패턴이나 파손 형태처럼 복잡한 특징을 학습한다.

- 초기 층: 선, 경계, 색 변화
- 중간 층: 돌출점, 돌출선, 균열 패턴
- 깊은 층: 점자블록 전체 형태와 파손 상태

### 2.3 비전 AI 문제 유형

| 문제 | 출력 | 프로젝트 적용 |
|---|---|---|
| Image Classification | 이미지 전체의 클래스 | 정상/불량 베이스라인 |
| Object Detection | 클래스와 bounding box | 점자블록 또는 파손 후보 위치 탐지 |
| Semantic Segmentation | 픽셀별 클래스 | 점자블록 영역과 파손 면적 계산 |
| Instance Segmentation | 객체별 mask와 클래스 | 여러 점자블록·파손 영역을 개별 구분 |
| Anomaly Detection | 정상에서 벗어난 정도 | 알려지지 않은 파손 후보 수집 |

## 3. YOLO 이해

YOLO(You Only Look Once)는 한 번의 신경망 추론으로 객체의 위치와 클래스를 함께 예측하는 실시간 비전 모델 계열이다. 속도가 빠르기 때문에 카메라 영상을 처리하는 Edge AI에 적합하다.

### 3.1 YOLO의 주요 출력

- **Bounding box:** 객체가 위치한 사각형 영역
- **Class:** 점자블록, 파손 등 객체 종류
- **Confidence:** 해당 예측을 얼마나 신뢰하는지 나타내는 값
- **Mask:** Segmentation 모델에서 객체의 픽셀 영역

### 3.2 IoU

IoU(Intersection over Union)는 예측 영역과 정답 영역이 얼마나 겹치는지 나타낸다.

```text
IoU = 예측과 정답의 교집합 면적 / 예측과 정답의 합집합 면적
```

IoU가 높을수록 객체 위치를 정확하게 찾은 것이다. 파손 부위는 모양이 불규칙하므로 bbox IoU뿐 아니라 mask IoU도 확인해야 한다.

### 3.3 NMS

하나의 객체 주변에 여러 bbox가 예측될 수 있다. NMS(Non-Maximum Suppression)는 서로 많이 겹치는 bbox 중 confidence가 가장 높은 결과만 남겨 중복 탐지를 줄인다.

### 3.4 Confidence threshold

Confidence threshold를 높이면 확실한 탐지만 남아 오탐이 줄지만 작은 파손을 놓칠 수 있다. 반대로 낮추면 미탐은 줄지만 서버에 전송되는 이벤트가 너무 많아질 수 있다.

SafeWalk Scout에서는 단일 프레임의 threshold만으로 판단하지 않고 다음을 함께 사용한다.

- 최근 N개 프레임 중 K개 이상에서 파손이 탐지되었는가
- 파손 mask가 점자블록 영역의 일정 비율 이상인가
- 같은 위치의 탐지가 연속해서 유지되는가
- 이미지가 지나치게 흐리거나 어둡지 않은가

## 4. Detection과 Segmentation 비교

### YOLO Detection

장점:

- 학습 및 추론 속도가 빠르다.
- Jetson에서 실시간 처리하기 유리하다.
- 파손 후보가 있는 대략적인 위치를 찾기 쉽다.

한계:

- 불규칙한 파손의 정확한 면적을 계산하기 어렵다.
- 정상 점자블록과 파손 부위가 하나의 bbox에 함께 포함될 수 있다.

### YOLO Segmentation

장점:

- 파손 영역을 픽셀 단위로 표현할 수 있다.
- 파손 면적 비율과 점자 경로 단절 정도를 계산하기 쉽다.
- 현재 확인한 AI Hub 점자블록 라벨이 polygon이므로 원본 정보를 잘 활용할 수 있다.

한계:

- Detection보다 학습과 추론 비용이 크다.
- polygon 품질이 낮으면 mask도 부정확하게 학습된다.

### 프로젝트 적용 결론

첫 실험은 YOLO Detection과 YOLO Segmentation을 모두 작은 모델로 학습해 비교한다. 최종 구조는 다음 두 후보를 실제 Jetson 성능으로 결정한다.

1. Edge에서 Detection으로 후보를 빠르게 선별하고 서버에서 Segmentation 수행
2. Edge에서 경량 Segmentation까지 수행하고 서버에서 고해상도 결과 재검증

## 5. AI Hub 라벨과 YOLO 형식

확인한 AI Hub JSON에는 이미지 크기와 polygon 좌표가 포함되어 있다. YOLO Segmentation 형식으로 변환할 때 각 좌표를 이미지 너비와 높이로 나누어 0~1 범위로 정규화해야 한다.

```text
class_id x1 y1 x2 y2 x3 y3 ...
```

변환 과정:

1. JSON의 `info.width`, `info.height`를 읽는다.
2. `annotations[].annotation_info`에서 polygon을 읽는다.
3. `x / width`, `y / height`로 좌표를 정규화한다.
4. 정상/불량 또는 파손 유형을 내부 class ID로 매핑한다.
5. 이미지와 같은 이름의 `.txt` 라벨 파일을 생성한다.
6. 좌표 범위와 polygon 점 개수를 검증한다.

주의할 점은 정상 annotation도 polygon으로 존재한다는 것이다. 모델 목표가 `점자블록 영역 탐지`인지 `파손 영역 탐지`인지에 따라 class 정의가 달라진다.

### 클래스 설계 후보

**실험 A: 점자블록 상태 분할**

- `0: tactile_normal`
- `1: tactile_defect_partial`
- `2: tactile_defect_full`

**실험 B: 점자블록과 파손 영역 분리**

- `0: tactile_block`
- `1: damaged_area`

AI Hub annotation이 실제로 파손 영역만 표시하는지, 점자블록 전체를 표시하는지 샘플 시각화 후 최종 결정해야 한다.

## 6. 데이터셋 디렉터리 구조

일반적인 YOLO 데이터셋은 다음과 같이 구성한다.

```text
dataset/
  images/
    train/
    val/
    test/
  labels/
    train/
    val/
    test/
  data.yaml
```

`data.yaml`에는 이미지 경로와 클래스 이름을 정의한다.

```yaml
path: dataset
train: images/train
val: images/val
test: images/test
names:
  0: tactile_normal
  1: tactile_defect_partial
  2: tactile_defect_full
```

파일을 무작위로 분할하면 같은 장소의 연속 촬영 이미지가 학습셋과 검증셋에 함께 포함될 수 있다. 따라서 촬영일, 지역 ID, 주행 구간을 기준으로 그룹 분할해야 한다.

## 7. 학습 흐름

아래 명령은 학습 과정의 예시이며 실제 모델 이름과 입력 크기, batch 크기는 개발 환경에서 정한다.

```bash
# 설치 및 환경 확인
pip install ultralytics
yolo checks

# Detection 학습 예시
yolo detect train model=<small-detection-model>.pt data=data.yaml epochs=50 imgsz=640

# Segmentation 학습 예시
yolo segment train model=<small-segmentation-model>.pt data=data.yaml epochs=50 imgsz=640

# 검증
yolo segment val model=runs/segment/train/weights/best.pt data=data.yaml

# 이미지 추론
yolo segment predict model=runs/segment/train/weights/best.pt source=test_images
```

학습 기록에는 다음 내용을 반드시 남긴다.

- 데이터 버전과 train/validation/test 수
- 클래스별 이미지 및 annotation 수
- 모델과 사전학습 가중치
- epochs, image size, batch size, learning rate
- Precision, Recall, mAP 및 클래스별 결과
- 실패 사례 이미지와 원인 분석
- 실행 환경, GPU, 학습 시간

## 8. 평가 지표 해석

### Precision

모델이 파손이라고 탐지한 결과 중 실제 파손의 비율이다. Precision이 낮으면 그림자, 오염, 노란 물체를 파손으로 잘못 판단하는 문제가 많다는 뜻이다.

```text
Precision = TP / (TP + FP)
```

### Recall

실제 파손 중 모델이 찾아낸 비율이다. Recall이 낮으면 중요한 파손을 놓친다. 안전 점검 시스템에서는 Recall을 우선 확인하되, 이벤트가 너무 많아지지 않도록 Precision과 함께 조정한다.

```text
Recall = TP / (TP + FN)
```

### mAP

여러 confidence threshold와 IoU 기준에서 객체 탐지 성능을 종합한 값이다. `mAP50`은 IoU 0.5 기준이고 `mAP50-95`는 더 엄격한 여러 IoU 기준의 평균이다.

### Confusion matrix

정상, 부분 파손, 전체 파손 중 어떤 클래스를 서로 혼동하는지 확인한다. 전체 점수만 보지 않고 클래스별 Recall을 확인해야 한다.

## 9. 오류 분석 계획

모델 학습 후 오탐과 미탐을 다음 기준으로 분류한다.

| 오류 유형 | 예상 원인 | 개선 방법 |
|---|---|---|
| 그림자를 파손으로 탐지 | 명암 변화에 과적합 | 그림자 정상 데이터 추가, 밝기 증강 |
| 노란 일반 블록 오탐 | 색상에 과도하게 의존 | 돌출 패턴·연속 구조 데이터 추가 |
| 작은 균열 미탐 | 입력 해상도 부족 | 고해상도 crop, 서버 2차 모델 |
| 사람 발에 가린 구간 미탐 | 가림 데이터 부족 | 부분 가림 증강과 실제 데이터 추가 |
| 흐린 영상 오탐 | 주행 진동 | blur 데이터 추가, 프레임 품질 필터 |
| 동일 파손 반복 등록 | 프레임별 독립 판단 | 연속 프레임 추적과 위치 기반 병합 |

## 10. OpenCV로 공부할 내용

- 이미지와 영상 읽기, 저장하기
- 동영상에서 프레임 추출하기
- RGB/BGR 변환과 resize
- bbox와 polygon mask 그리기
- blur와 밝기 측정으로 저품질 프레임 제외하기
- perspective transform으로 촬영 각도 보정 실험
- 추론 결과를 영상 위에 표시하기
- 파손 전후 프레임을 순환 버퍼에 저장하기

## 11. Jetson 배포

학습은 GPU 서버나 개발 PC에서 수행하고 Jetson은 추론 장치로 사용한다.

```text
PyTorch 모델
  -> ONNX export
  -> ONNX 결과 일치 검증
  -> TensorRT FP16 엔진 생성
  -> Jetson 카메라 입력 연결
  -> FPS·지연시간·메모리 측정
```

Jetson에서 측정할 항목:

- 평균 FPS
- p50 및 p95 추론 지연시간
- GPU/CPU 메모리 사용량
- 전력 모드별 성능
- 장시간 실행 시 온도와 throttling
- 카메라 입력부터 이벤트 저장까지의 전체 지연시간

모델 추론 속도만 측정하지 않고 전처리, 후처리, 영상 저장과 ROS 2 통신까지 포함한 end-to-end 지연시간을 확인해야 한다.

## 12. 프로젝트용 단계별 학습 계획

### 1단계: 비전 기초

- 이미지와 좌표계 이해
- CNN, classification, detection, segmentation 차이 학습
- Precision, Recall, IoU, mAP 계산 및 해석

### 2단계: OpenCV 실습

- AI Hub 이미지와 polygon 시각화
- 영상 프레임 추출과 전처리
- 그림자, blur, 밝기 변화 샘플 비교

### 3단계: YOLO 베이스라인

- AI Hub JSON을 YOLO 형식으로 변환
- 소규모 데이터로 파이프라인 정상 동작 확인
- Detection과 Segmentation 모델 학습

### 4단계: 성능 개선

- 오탐·미탐 분석
- 오탐 방지 데이터 추가
- 실제 로봇 카메라 데이터로 fine-tuning
- threshold 및 연속 프레임 조건 조정

### 5단계: Edge 적용

- ONNX/TensorRT 변환
- Jetson 실시간 추론
- 이벤트 영상 저장 및 서버 전송 연동
- 장시간 주행 성능과 발열 확인

## 13. 이번 학습의 결론

- YOLO는 실시간성이 필요한 Edge AI의 유력한 베이스라인이다.
- 점자블록 위치만 찾는다면 Detection으로 시작할 수 있지만 파손 면적과 형태까지 분석하려면 Segmentation이 더 적합하다.
- 현재 AI Hub 점자블록 라벨은 polygon이므로 Segmentation 실험에 활용할 수 있다.
- 공개 데이터만 학습하면 실제 로봇 카메라의 높이, 진동, 조명 환경에서 성능이 떨어질 수 있어 자체 촬영 데이터가 반드시 필요하다.
- 안전 점검에서는 파손을 놓치지 않는 Recall이 중요하지만, 운영 가능한 이벤트 수를 위해 Precision과 연속 프레임 필터도 함께 고려해야 한다.
- 최종 모델 선정은 PC 성능이 아니라 Jetson에서의 정확도, FPS, 지연시간과 발열을 종합해 결정한다.

