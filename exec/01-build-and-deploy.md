# Roady 빌드·배포 가이드

GitLab 저장소를 클론한 뒤 Docker Compose로 프론트엔드, Spring 백엔드, 서버 AI, MySQL, Redis, MQTT를 함께 실행하는 절차를 정리한다.

## 1. 구성 및 버전

| 구분 | 제품/버전 | 설정 및 비고 |
| --- | --- | --- |
| JVM | Eclipse Temurin JDK/JRE 21 | 백엔드 Dockerfile의 빌드·실행 이미지 |
| WAS | Spring Boot 4.0.7 내장 Servlet 컨테이너 | 별도 WAS 설치 없이 `app.jar` 실행 |
| 빌드 도구 | Gradle Wrapper 9.5.1 | `Roady_BE/gradlew` 또는 `gradlew.bat` 사용 |
| 백엔드 | Spring Boot 4.0.7, MyBatis Spring Boot 4.0.1 | 포트 8080(컨테이너 내부) |
| 웹 서버 | Nginx 1.27-alpine | 정적 Vue 파일 제공, `/api`·`/ws`를 backend로 reverse proxy |
| 프론트엔드 빌드 | Node 24-alpine, npm | `package.json` 엔진은 Node 22.18 이상 또는 24.12 이상 |
| 프론트엔드 | Vue 3.5, Vite 8, TypeScript 6 | Docker 빌드 결과를 Nginx가 제공 |
| AI 런타임 | Python 3.11-slim-bookworm | FastAPI/Uvicorn, Ultralytics, OpenCV |
| AI 추론 | PyTorch 2.8.0, TorchVision 0.23.0 | 기본 Docker Compose는 CPU, GPU overlay는 CUDA 12.8 wheel |
| 관계형 DB | MySQL 8.4 | 문자셋 `utf8mb4`, 콜레이션 `utf8mb4_unicode_ci` |
| 캐시/큐 | Redis 7.4-alpine | AI 분석 큐·refresh session·로봇 최신 위치 |
| 메시지 브로커 | Eclipse Mosquitto 2 | MQTT 1883, 로봇 telemetry/command |
| IDE | 저장소에 버전 고정 없음 | IDE 없이 Docker/Gradle/npm 명령으로 빌드 가능. 백엔드는 IntelliJ IDEA, 프론트엔드는 VS Code 계열을 권장 |

IDE 버전과 운영체제 버전은 프로젝트 파일에 고정되어 있지 않다. 재현성은 IDE가 아니라 Docker 이미지, Gradle Wrapper, `package-lock.json`을 기준으로 확보한다.

## 2. 소스 클론 및 사전 조건

### 2.1 필요한 도구

- Git
- Docker Engine 또는 Docker Desktop
- Docker Compose v2 (`docker compose` 명령)
- GPU 추론을 사용할 경우 NVIDIA GPU, NVIDIA Driver, NVIDIA Container Toolkit

```bash
git clone <GitLab 저장소 주소>
cd S15P11A404
docker --version
docker compose version
```

### 2.2 환경 파일 준비

실제 비밀 값은 Git에 커밋하지 않는다. 백엔드 컨테이너가 읽는 파일은 `Roady_BE/.env`이며, 시작점은 `Roady_BE/.env.example`이다.

```bash
cp Roady_BE/.env.example Roady_BE/.env
```

Windows PowerShell:

```powershell
Copy-Item Roady_BE/.env.example Roady_BE/.env
```

`MYSQL_DATABASE`, `SPRING_DATASOURCE_URL`의 DB 이름, `MYSQL_USER`, `SPRING_DATASOURCE_USERNAME`을 동일하게 맞춘다. 현재 Compose 기본 DB 이름은 `roadbuddy`다. 운영에서는 반드시 임의의 강한 비밀번호와 JWT secret으로 교체한다.

Compose 파일의 `${...}` 치환값은 저장소 루트의 `.env`, 셸 환경 변수 또는 명령행에서 공급한다. `Roady_BE/.env`의 `env_file` 값은 컨테이너 내부 환경에 주입되지만 Compose 파일의 `${...}` 치환값을 자동으로 공급하지 않는다.

## 3. Docker Compose 빌드 및 실행

### 3.1 전체 서비스 실행

```bash
docker compose up -d --build
docker compose ps
```

서비스와 포트는 다음과 같다.

| 서비스 | 컨테이너 포트 | 호스트 기본 포트 | 확인 방법 |
| --- | ---: | ---: | --- |
| frontend | 80 | 3000 | `http://localhost:3000` |
| backend | 8080 | 8081 | `http://localhost:8081/actuator`는 별도 노출하지 않음. 프론트 `/api` proxy 사용 |
| ai | 8000 | 8000 | `http://localhost:8000/health/live` |
| mysql | 3306 | 3306 | MySQL client 또는 healthcheck |
| redis | 6379 | 6379 | `redis-cli ping` |
| mqtt | 1883 | 1883 | Mosquitto client |

프론트엔드에서는 `http://localhost:3000/api/...`를 호출한다. Nginx가 `/api/`를 `http://backend:8080/api/`로 전달하므로 브라우저에서 `localhost:8081`을 API base URL로 직접 지정할 필요가 없다.

### 3.2 빌드 로그 및 상태 확인

```bash
docker compose logs -f ai
docker compose logs -f backend
docker compose logs -f frontend
docker compose ps
```

AI 컨테이너는 모델 해시 검증과 warm-up 후 `/health/ready`가 성공한다. backend는 AI healthcheck가 성공한 뒤 시작한다.


## 4. 환경 변수

### 4.1 MySQL, Spring, 공통 환경 (`Roady_BE/.env`)

| 변수 | 예시/기본값 | 설명 |
| --- | --- | --- |
| `MYSQL_DATABASE` | `roady` | MySQL 초기 데이터베이스 |
| `MYSQL_USER` | 별도 지정 | 애플리케이션 DB 계정 |
| `MYSQL_PASSWORD` | 별도 지정 | 애플리케이션 DB 비밀번호 |
| `MYSQL_ROOT_PASSWORD` | 별도 지정 | MySQL root 비밀번호 |
| `SPRING_DATASOURCE_URL` | `jdbc:mysql://mysql:3306/roady?...` | backend 컨테이너 기준 DB 주소 |
| `SPRING_DATASOURCE_USERNAME/PASSWORD` | DB 계정과 동일 | Spring JDBC 접속 정보 |
| `SPRING_DATA_REDIS_HOST/PORT` | `redis` / `6379` | Redis 주소 |
| `ROADY_DEFAULT_USERS_ENABLED` | `true` | admin/inspector/repairer/viewer 샘플 계정 생성 |
| `ROADY_SAMPLE_DATA_ENABLED` | `true` | 로봇, 파손 시연 데이터 생성 |
| `MQTT_ENABLED` | `true` | MQTT adapter 활성화 |
| `MQTT_BROKER_IP/PORT` | `mqtt` / `1883` | Mosquitto 주소 |
| `ROADY_ROBOT_LOCATION_REDIS_KEY_PATTERN` | `roady:robots:{robotId}:location` | 최신 위치 Redis key |
| `ROADY_ROBOT_LOCATION_TTL` | `5m` | 최신 위치 보관 시간 |
| `ROADY_ROBOT_LOCATION_RDB_PERSISTENCE_INTERVAL` | `1m` | 위치 RDB 저장 주기 |
| `ROADY_AI_IMAGE_ANALYSIS_ENDPOINT_URL` | `http://ai:8000/analyze` | Spring → AI endpoint |
| `ROADY_AI_IMAGE_ANALYSIS_WORKER_ENABLED` | `true`(Compose) | Redis AI worker 활성화 |
| `ROADY_AI_IMAGE_ANALYSIS_QUEUE_KEY` | `roady:damage:image-analysis:queue` | 분석 대기 큐 |
| `ROADY_AI_IMAGE_ANALYSIS_DEAD_LETTER_QUEUE_KEY` | `roady:damage:image-analysis:dead-letter` | 실패 큐 |
| `ROADY_AI_IMAGE_ANALYSIS_BATCH_SIZE` | `3` | worker polling batch |
| `ROADY_AI_IMAGE_ANALYSIS_POLL_DELAY_MS` | `1000` | polling 간격 |
| `ROADY_AI_IMAGE_ANALYSIS_REQUEST_TIMEOUT` | `3m` | AI 요청 timeout |
| `ROADY_KAKAO_GEOCODING_ENABLED` | `false` | Kakao 역지오코딩 사용 여부 |
| `ROADY_KAKAO_REST_API_KEY` | 비밀 값 | Kakao Local REST API key |
| `ROADY_CORS_ALLOWED_ORIGINS` | 프론트 origin 목록 | 쉼표로 구분 |

JWT secret은 `roady.jwt.secret`으로 관리한다. 운영에서는 `application.properties`의 개발용 기본값을 사용하지 말고 Spring 외부 설정(`ROADY_JWT_SECRET` 또는 실행 인자)으로 교체한다. access token 기본 유효기간은 30분, refresh token은 14일이다.

### 4.2 Compose, 프론트, AI 환경

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `FRONTEND_PORT` | `3000` | frontend 호스트 포트 |
| `VITE_API_BASE_URL` | `/api` | 빌드 시 프론트 API base URL |
| `AI_PORT` | `8000` | AI 호스트 포트 |
| `ROADY_AI_DEVICE` | `cpu`(Compose) | `cpu` 또는 GPU device 번호 |
| `ROADY_AI_IMGSZ` | `1024`(Compose) | 추론 입력 크기 |
| `ROADY_AI_INFERENCE_CONCURRENCY` | `1` | 한 번에 처리할 추론 수 |
| `ROADY_AI_VERIFY_MODEL_HASH` | `true` | weight SHA-256 검증 |
| `ROADY_AI_WARMUP_ENABLED` | `true` | readiness 전 warm-up |
| `ROADY_AI_MODEL_PATH` | 서버 v2 weight 경로 | 모델 파일 경로 |
| `ROADY_AI_MODEL_SHA256_PATH` | `.sha256` 경로 | 모델 해시 파일 |
| `ROADY_AI_MAX_IMAGES` | `50` | 한 요청 이미지 개수 |
| `ROADY_AI_MAX_IMAGE_BYTES` | `20MB` | 이미지 1개 제한 |
| `ROADY_AI_MAX_REQUEST_BYTES` | `200MB` | 전체 요청 제한 |
| `ROADY_AI_SCORE_MINOR_MAX_PIXELS` | `10000` | score 구간 1 상한 |
| `ROADY_AI_SCORE_MODERATE_MAX_PIXELS` | `50000` | score 구간 2 상한 |
| `ROADY_AI_SCORE_MAX_PIXELS` | `100000` | score 100 도달 픽셀 수 |

## 5. 주요 설정, 계정 파일 목록

| 파일 | 용도 |
| --- | --- |
| `docker-compose.yml` | 전체 서비스, 포트, 네트워크, volume, healthcheck |
| `docker-compose.gpu.yml` | NVIDIA GPU overlay |
| `Roady_BE/.env` | 운영/로컬 비밀값. Git 커밋 금지 |
| `Roady_BE/.env.example` | 환경 변수 템플릿 |
| `Roady_BE/src/main/resources/application.properties` | Spring 기본 설정 및 환경 변수 매핑 |
| `Roady_BE/src/main/resources/application-local.properties` | 로컬 profile 설정 |
| `Roady_BE/src/main/resources/rdb/schema.sql` | 애플리케이션 시작 시 초기화되는 최신 DB schema |
| `Roady_BE/Dockerfile` | Gradle build 및 Temurin JRE 실행 이미지 |
| `Roady_FE/Dockerfile` | Node build 및 Nginx 실행 이미지 |
| `Roady_FE/nginx.conf` | `/api`, `/ws`, SPA fallback reverse proxy |
| `ROADY_AI/Dockerfile` | Python·PyTorch·모델을 포함한 AI 이미지 |
| `ROADY_AI/models/server/*.sha256` | 서버 AI weight 무결성 검증 |
| `Roady_BE/docker/mosquitto/mosquitto.conf` | MQTT listener/persistence 설정 |

샘플 계정은 `ROADY_DEFAULT_USERS_ENABLED=true`일 때 생성된다. 계정은 `admin`, `inspector`, `repairer`, `viewer`이며 초기 샘플 비밀번호는 애플리케이션 initializer에 정의된 개발용 값이다. 운영 환경에서는 seed를 끄고 별도 계정을 생성한다.

## 6. 배포 특이사항 및 운영 점검

1. MySQL, Redis, Mosquitto, AI가 healthy가 된 뒤 backend가 시작되므로 첫 기동은 이미지 다운로드와 AI warm-up 시간만큼 기다린다.
2. `docker compose down`은 named volume을 보존한다. DB까지 삭제하려면 `down -v`가 필요하지만 데이터가 삭제되므로 운영에서는 실행하지 않는다.
3. `mysql-data`, `redis-data`, `mqtt-data`는 영속 volume이다. EC2 장애에 대비해 별도 백업을 보관한다.
4. 프론트 API 주소는 운영 도메인의 `/api`를 사용한다. `localhost:3000/api` 요청이 Nginx를 거쳐 backend로 전달되어야 한다.
5. 운영 도메인이 바뀌면 `ROADY_CORS_ALLOWED_ORIGINS`와 TLS reverse proxy 설정을 함께 변경한다.
6. Mosquitto 기본 설정은 `allow_anonymous true`인 시연용이다. 운영에서는 인증·ACL·TLS(MQTTS)를 적용한다.
7. AI 모델 파일과 `.sha256` 파일을 함께 배포한다. 해시가 맞지 않으면 readiness가 실패한다.
8. 운영에서는 JWT secret, DB 비밀번호, Kakao API key를 Secret Manager 또는 EC2 환경 변수로 주입한다.
9. `/health/live`, `/health/ready`, `/model-info`는 운영 모니터링에 사용하되 외부 공개 범위를 제한한다.
