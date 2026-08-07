# Roady 외부 서비스 정보

프로젝트 소스에서 확인되는 외부 서비스와 가입·설정 정보를 정리한다. 비밀 키와 계정 비밀번호는 문서에 저장하지 않고 환경 변수로 주입한다.

## 1. 외부 서비스 사용 현황

| 서비스 | 사용 목적 | 가입/키 필요 여부 | 설정 위치 | 상태 |
| --- | --- | --- | --- | --- |
| GitLab | 소스 저장소·clone·Merge Request | 프로젝트 권한 필요 | Git remote | 사용 |
| AWS EC2 | Docker Compose 운영 호스트 | AWS 계정·EC2 접근 권한 필요 | 운영 인프라 | 배포 대상 |
| Docker Hub | MySQL, Redis, Mosquitto, Node, Nginx, Temurin base image | 공개 이미지 pull은 보통 로그인 불필요. rate limit 시 Docker 계정 필요 | Dockerfile/Compose image | 사용 |
| PyTorch wheel index | CUDA 12.8용 torch/torchvision 설치 | 별도 가입 없음 | `ROADY_AI/Dockerfile` | GPU build 시 사용 |
| Maven Central | Gradle 의존성 다운로드 | 별도 가입 없음 | `Roady_BE/build.gradle` | 사용 |
| npm registry | 프론트 의존성 다운로드 | 공개 패키지는 로그인 불필요 | `Roady_FE/package-lock.json` | 사용 |
| OpenStreetMap tile | Leaflet 지도 타일 | API key 없음. attribution 및 사용 정책 준수 | `Roady_FE/src/components/common/CommonMap.vue` | 사용 |
| Kakao Local API | 좌표 → 주소·행정구역 역지오코딩 | Kakao Developers 가입 및 REST API key 필요 | `ROADY_KAKAO_REST_API_KEY` | 선택 기능, 기본 off |
| Mosquitto MQTT | 로봇 telemetry/command 메시지 | 별도 SaaS 가입 없음. 자체 broker 운영 | `docker-compose.yml`, `mosquitto.conf` | 자체 운영 |

## 2. 인증·소셜 서비스

소셜 로그인(Google, Naver, Kakao OAuth 등)은 사용하지 않는다. Roady 백엔드가 자체 사용자 테이블과 Spring Security를 사용하며 access token과 refresh token을 JWT로 발급한다. refresh session은 Redis에 저장한다.

- 가입/로그인 API: `/api/auth/signup`, `/api/auth/login`
- 인증 헤더: `Authorization: Bearer <accessToken>`
- JWT 개발 기본값은 운영에서 사용하지 않는다.
- 계정·권한은 `ADMIN`, `INSPECTOR`, `REPAIRER`, `VIEWER`로 관리한다.

## 3. 지도·주소 서비스

### 3.1 OpenStreetMap

프론트의 Leaflet 지도는 `https://tile.openstreetmap.org/{z}/{x}/{y}.png` 타일을 사용하고 `OpenStreetMap contributors` attribution을 표시한다. 상용 서비스 수준의 대규모 트래픽에서는 OSM 사용 정책을 확인하고 자체 tile provider 또는 상용 지도 서비스로 교체한다.

### 3.2 Kakao Local API

파손 좌표의 주소명·법정동 코드를 보완하는 선택 기능이다.

1. Kakao Developers에서 애플리케이션을 생성한다.
2. Local API 사용을 활성화한다.
3. REST API key를 `ROADY_KAKAO_REST_API_KEY`에 입력한다.
4. `ROADY_KAKAO_GEOCODING_ENABLED=true`로 켠다.
5. 운영 도메인에서 호출할 경우 Kakao 콘솔의 허용 설정과 호출량 제한을 확인한다.

사용 endpoint:

- `https://dapi.kakao.com/v2/local/geo/coord2address.json`
- `https://dapi.kakao.com/v2/local/geo/coord2regioncode.json`

키가 없거나 기능을 끄면 수집된 주소·행정구역 값을 그대로 사용하고 AI 분석·기본 파손 조회는 동작한다.

## 4. 로봇 통신 서비스

MQTT는 외부 클라우드가 아니라 Compose의 Mosquitto broker를 사용한다.

| 항목 | 값 |
| --- | --- |
| broker | `mqtt:1883`(Compose 내부), 보드 연결 시 운영 EC2 hostname |
| telemetry topic | `roady/{robotId}/telemetry` |
| command topic | `roady/{robotId}/command` |
| command ack topic | `roady/{robotId}/command/ack` |
| 설정 | `Roady_BE/docker/mosquitto/mosquitto.conf` |

현재 시연용 Mosquitto 설정은 anonymous 접속을 허용한다. 운영에서는 username/password, topic ACL, TLS를 추가하고 보드의 `broker_host`, `broker_port`, `mqtt_username`, `mqtt_password` ROS parameter를 설정한다.

## 5. AI 모델·빌드 서비스

서버 AI는 외부 추론 API를 호출하지 않고 저장소의 YOLO26s-seg weight를 FastAPI 컨테이너에서 직접 실행한다.

- 모델 파일: `ROADY_AI/models/server/yolo26s_seg_multiclass_v2_best.pt`
- SHA-256: `ROADY_AI/models/server/yolo26s_seg_multiclass_v2_best.sha256`
- AI 내부 endpoint: `POST /analyze`
- Spring worker와 AI 서버는 Docker network에서 `http://ai:8000/analyze`로 통신
- GPU 이미지 build 시 PyTorch index `https://download.pytorch.org/whl/cu128`에서 wheel을 다운로드

Photon Cloud, OpenAI/Gemini API, 외부 코드 컴파일 SaaS는 현재 프로젝트에서 사용하지 않는다. Java·TypeScript·Python 빌드는 각각 Gradle Wrapper, npm scripts, Docker 내부 pip로 수행한다.

## 6. 계정·키 관리 원칙

- `.env`, AWS key, Kakao REST API key, MQTT password, JWT secret은 Git에 커밋하지 않는다.
- 문서·샘플 파일에는 `change-me` 또는 placeholder만 사용한다.
- 운영 배포에서는 EC2 환경 변수, Docker secrets 또는 AWS Secrets Manager 등 외부 비밀 저장소를 사용한다.
- 외부 서비스 장애 시 Kakao geocoding은 비활성화하고, OSM tile 장애는 지도만 영향을 받으며 파손·보수 API는 별도로 동작한다.
