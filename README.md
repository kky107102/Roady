# ROADY

<img src="Roady_FE/public/roady-favicon.png" alt="ROADY 로고" width="180">

## 서비스 개요

ROADY는 자율주행 로봇과 AI를 활용해 점자블록의 상태를 점검하고, 발견된 파손을 보수 완료까지 관리하는 통합 서비스입니다. 사람이 넓은 구역을 직접 순찰하며 점검해야 하는 부담을 줄이고, 파손 위치와 처리 상태를 한곳에서 확인할 수 있도록 돕는 것을 목표로 합니다.

로봇은 지정된 경로에서 점자블록을 따라 주행합니다. 주행 중 Edge AI가 점자블록과 파손 후보를 탐지하고, 전방의 보행 장애물도 함께 확인합니다. 파손이 의심되는 지점을 발견하면 이미지와 위치 정보를 기록해 서버로 전송합니다.

서버 AI는 수집된 이미지를 다시 분석해 균열, 마모, 유실, 장애물과 같은 파손 유형을 구분합니다. 분석 결과에는 파손 범위와 심각도, 보수 우선순위, 추가 검토 필요 여부가 포함됩니다. 판정 근거가 충분하지 않은 경우에는 결과를 확정하지 않고 관리자가 직접 확인할 수 있도록 표시합니다.

관리자는 웹 서비스에서 파손 현황을 지도와 목록으로 확인하고 AI 분석 결과를 검토할 수 있습니다. 검토가 끝난 파손은 보수 요청으로 전환하며, 요청 내용과 처리 과정, 완료 결과를 이력으로 관리합니다. 대시보드에서는 지역과 기간, 상태에 따른 파손 현황과 보수 완료율을 확인할 수 있습니다.

이 과정을 통해 ROADY는 `주행 점검 -> 파손 탐지 -> AI 분석 -> 관리자 검토 -> 보수 처리`로 이어지는 점자블록 관리 흐름을 하나의 시스템으로 연결합니다.

## 주요 기능

- 점자블록 추종 주행과 보행 장애물 감지
- 점자블록 파손 후보 촬영과 위치 정보 수집
- AI 기반 파손 유형, 심각도, 보수 우선순위 분석
- 지도 기반 파손 위치와 상세 정보 조회
- 로봇 상태, 경로, 운행 정보 관리
- 보수 요청, 진행 상황, 완료 이력 관리
- 파손 현황과 보수 통계 대시보드
- 사용자 역할에 따른 접근 권한 관리

## 서비스 흐름

```text
로봇 주행
  -> 파손 후보 탐지
  -> 이미지와 위치 정보 전송
  -> 서버 AI 정밀 분석
  -> 관리자 검토
  -> 보수 요청과 완료 처리
```

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| Frontend | Vue 3, TypeScript, Vite, Pinia, Leaflet, Chart.js |
| Backend | Java 21, Spring Boot, MyBatis, Spring Security, WebSocket |
| AI | Python, FastAPI, YOLO, PyTorch, OpenCV |
| Embedded | NVIDIA Jetson Orin Nano, ROS 2 Humble, TensorRT |
| Data | MySQL, Redis |
| Communication | MQTT, HTTP, WebSocket |
| Infra | Docker Compose, Nginx, Mosquitto |

## 프로젝트 구조

```text
S15P11A404/
├─ Roady_FE/          # 관리자 웹 서비스
├─ Roady_BE/          # API, 인증, 데이터와 로봇 관리
├─ ROADY_AI/          # 파손 탐지 모델과 분석 서버
├─ Roady_Embedded/    # 로봇 주행, 센서, 통신 모듈
├─ exec/              # 빌드, 배포, 외부 서비스와 시연 문서
└─ docker-compose.yml # 통합 실행 환경
```

## 빠른 실행

### 사전 준비

- Git
- Docker Engine 또는 Docker Desktop
- Docker Compose v2

### 환경 파일 설정

```bash
cp Roady_BE/.env.example Roady_BE/.env
```

Windows PowerShell에서는 다음 명령을 사용합니다.

```powershell
Copy-Item Roady_BE/.env.example Roady_BE/.env
```

`Roady_BE/.env`의 데이터베이스 계정과 비밀번호를 실행 환경에 맞게 수정합니다. 데이터베이스 이름은 Docker Compose 설정과 동일하게 맞춰야 합니다.

### 전체 서비스 실행

```bash
docker compose up -d --build
docker compose ps
```

기본 접속 주소는 다음과 같습니다.

| 서비스 | 주소 |
| --- | --- |
| Web | `http://localhost:3000` |
| Backend | `http://localhost:8081` |
| Swagger UI | `http://localhost:8081/swagger-ui/index.html` |
| AI Health | `http://localhost:8000/health/live` |

서비스를 종료하려면 다음 명령을 실행합니다.

```bash
docker compose down
```

## 상세 문서

- [빌드와 배포 가이드](exec/01-build-and-deploy.md)
- [외부 서비스 설정](exec/02-external-services.md)
- [시연 시나리오](exec/04-demo-scenario.md)
- [Backend API 명세](Roady_BE/docs/api-spec.md)
- [Backend ERD](Roady_BE/docs/erd.md)
- [AI 구성](ROADY_AI/README.md)

## 팀 구성

ROADY는 Frontend, Backend, AI, Embedded 영역으로 나누어 개발했습니다.
