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

### 서버 파손 정밀 분석

- 모델: YOLO26s Segmentation
- 입력 크기: 768 × 768
- 클래스: `tactile_block`, `missing`, `crack`, `wear`, `obstruction`
- 가중치: `models/server/yolo26s_seg_multiclass_v4_best.pt`
- 역할: Edge가 전송한 점자블록 기준 ROI에서 파손 유형, Mask, 면적 비율, 심각도, 보수 우선순위, 검토 필요 여부를 분석
- 운영 정책: 분석 전제조건이 부족하면 확정 판정하지 않고 `review_required=true`, `advisory_only=true`로 반환

서버 분석 로직과 API 응답 계약은 [`server_damage_analysis/README.md`](server_damage_analysis/README.md)를 참고한다.

### 보행 장애물 탐지

- 모델: YOLO11n Detect
- 클래스: `foot`, `lower_leg`
- 가중치: `models/edge/obstacle_lower_limb_yolo11n_best.pt`
- 역할: 로봇 전방 보행 장애물 탐지

이 모델은 점자블록 손상 분류기와 관계없는 별도 기능이므로 유지한다.

## 데이터셋 구성 원칙

AI-Hub 등 공개 점자블록·도로 이미지는 초기 점자블록 탐지 구조와 라벨 형식 설계에 활용했다. 최종 시연 모델은 실제 시연 장소에서 휴대폰과 로봇 카메라로 촬영한 데이터를 중심으로 재구성했다.

- Edge 데이터셋: `tactile_block`, `damage_candidate` Detect 라벨
- Server 데이터셋: `tactile_block`, `missing`, `crack`, `wear`, `obstruction` Segmentation 라벨
- Hard Negative: 흙, 낙엽, 그림자, 얼룩, 정상 검은 틈 등 파손과 혼동되는 사례
- 개선 방식: 실제 주행 영상에서 미탐·오탐 프레임을 검수하고 Replay 학습에 반영

상세 통계와 검수 규칙은 [`dataset_docs/demo_environment/README.md`](dataset_docs/demo_environment/README.md)를 참고한다.

## 폴더 구조

```text
ROADY_AI/
├─ tactile_damage_detect/     # YOLO26n 점자블록·파손 후보 탐지
├─ server_damage_analysis/     # YOLO26s 서버 파손 유형·면적 분석
├─ obstacle_lower_limb/       # 보행 장애물 탐지
├─ dataset_docs/              # 데이터셋 구성 및 검수 문서
├─ models/edge/
│  ├─ tactile_damage_candidate_yolo26n_best.pt
│  └─ obstacle_lower_limb_yolo11n_best.pt
├─ models/server/
│  └─ yolo26s_seg_multiclass_v4_best.pt
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

## Server/Backend 전달 범위

AI 담당자는 다음 항목을 전달한다.

- YOLO26s Segmentation 가중치
- 클래스 순서와 모델 SHA-256
- FastAPI 분석 서버 코드
- 분석 JSON 응답 스키마
- Overlay와 통합 damage mask 생성 로직
- `review_required`, `advisory_only`, `OBSTRUCTION_SUSPECTED` 등 검토 사유 정책

DB 저장, Redis Queue 관리, 관리자 화면 표시와 최종 후처리 연동은 Server/Frontend 담당 범위이다.
