# ROADY AI

ROADY 프로젝트의 AI 모델, 학습·평가 코드와 Jetson 전달용 변환 도구를 관리한다.

## 현재 AI 구성

### 점자블록 파손 후보 탐지

- 모델: YOLO26n Detect
- 입력 크기: 768 × 768
- 클래스: `tactile_block`, `damage_candidate`
- 가중치: `models/edge/tactile_damage_candidate_yolo26n_best.pt`
- 역할: 로봇 카메라 영상에서 점자블록과 파손 후보를 한 번에 탐지
- 운영 결정: 별도 손상 분류기를 병행하지 않고 단일 Detect 모델 사용

학습·평가·카메라 테스트 방법은 [`tactile_damage_detect/README.md`](tactile_damage_detect/README.md)를 참고한다.

### 보행 장애물 탐지

- 모델: YOLO11n Detect
- 클래스: `foot`, `lower_leg`
- 가중치: `models/edge/obstacle_lower_limb_yolo11n_best.pt`
- 역할: 로봇 전방 보행 장애물 탐지

이 모델은 점자블록 손상 분류기와 관계없는 별도 기능이므로 유지한다.

## 폴더 구조

```text
ROADY_AI/
├─ tactile_damage_detect/     # YOLO26n 점자블록·파손 후보 탐지
├─ obstacle_lower_limb/       # 보행 장애물 탐지
├─ dataset_docs/              # 데이터셋 구성 및 검수 문서
├─ models/edge/
│  ├─ tactile_damage_candidate_yolo26n_best.pt
│  └─ obstacle_lower_limb_yolo11n_best.pt
├─ requirements.txt
└─ README.md
```

대용량 원본 데이터셋, 학습 결과 디렉터리와 Jetson에서 생성한 TensorRT `.engine` 파일은 Git에 저장하지 않는다.

## 설치

```powershell
cd ROADY_AI
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

## Jetson 전달 범위

AI 담당자는 다음 항목을 전달한다.

- YOLO26n PyTorch 가중치
- 입력 크기 768
- 클래스 순서와 신뢰도 기준
- ONNX→TensorRT FP16 변환 스크립트
- 검증 결과와 모델 SHA-256

ROS 노드 연결과 TensorRT 런타임 출력 처리는 임베디드 담당 범위이다.
