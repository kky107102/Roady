# Roady 시연 시나리오

시연은 현장 로봇 운행·관제 → 촬영 이미지 업로드 → AI 분석 완료 확인 → 웹 로그인·검토 → 보수 요청·완료 순서로 진행한다. 로봇에서 수집한 이미지가 Spring과 AI 서버를 거쳐 웹 화면에 반영되는 전체 흐름을 보여준다.

## 1. 시연 전 준비

### 실행

```bash
docker compose up -d --build
docker compose ps
```

브라우저에서 `http://localhost:3000` 또는 운영 도메인에 접속한다. `ROADY_DEFAULT_USERS_ENABLED=true`, `ROADY_SAMPLE_DATA_ENABLED=true`이면 아래 계정과 시연 데이터가 자동 생성된다.

### 시연 계정

| 역할 | 아이디 | 초기 비밀번호 | 권장 사용 화면 |
| --- | --- | --- | --- |
| 관리자 | `admin` | `roady0810` | 전체 시연 |
| 점검 담당자 | `inspector` | `roady0810` | 탐지 검토·로봇 관제 |
| 보수 담당자 | `repairer` | `roady0810` | 보수 화면 |
| 조회 사용자 | `viewer` | `roady0810` | 조회 권한 확인 |

위 비밀번호는 initializer에 정의된 개발용 샘플 값이다. 운영 계정에서는 사용하지 않는다.

시드 데이터는 로봇 8대와 파손 사건 8건이며 다음 상태가 포함된다.

- AI 분석 전/중: `COLLECTED`, `AI_ANALYZING`
- 검토 완료·요청 전: `AI_ANALYZED`, `REQUESTED`
- 보수 처리 중/완료: `REPAIR_IN_PROGRESS`, `REPAIR_COMPLETED`
- 취소: `CANCELED`

## 2. 로봇 운행 및 관제 시연(현장 단계)

### 2.1 운행 준비 및 순찰 시작

1. 로봇 전원, 점자블록 카메라, 장애물 카메라, LiDAR의 연결 상태를 확인한다.
2. Jetson Orin Nano에서 프로젝트의 Edge AI·장애물 탐지 노드를 실행한다.
3. 다음 ROS 토픽이 발행되는지 확인한다.
   - `/camera/wide/image_raw`: 점자블록 분석 카메라 원본 프레임
   - `/damage/events`: Edge AI가 확정한 파손 후보 이벤트
4. 로봇을 순찰 구간에 배치하고 `START_PATROL`(순찰 시작) 명령을 전송한다.
5. 로봇 상태가 `MOVING` 또는 `INSPECTING`으로 바뀌고 telemetry가 수신되는지 확인한다.

```bash
ros2 topic echo /camera/wide/image_raw --once
ros2 topic echo /damage/events --once
mosquitto_sub -h <broker-host> -t 'roady/1/telemetry' -v
```

실제 보드 launch 명령은 현장 보드 설정에 맞는 실행 스크립트를 사용한다. 보드가 없는 경우에는 시드 데이터 또는 MQTT mock publisher로 동일한 telemetry를 재현한다.

### 2.2 관제 명령 및 이벤트 확인

1. 운행 중 점자블록과 파손 후보가 탐지되는 장면을 통과시킨다.
2. Edge AI가 `tactile_block`, `damage_candidate`를 탐지하고 대표 원본 이미지와 분석 ROI를 이벤트에 포함하는지 확인한다.
3. 로봇 telemetry의 좌표·배터리·운행 상태가 `roady/{robotId}/telemetry`로 들어오는지 확인한다.
4. 시연용으로 `RETURN_HOME`(스테이션 복귀) 또는 `EMERGENCY_STOP`(긴급 정지) 명령을 전송한다.
5. `roady/{robotId}/command/ack`에서 명령 결과를 확인하고, 로봇이 실제로 복귀·정지하는지 확인한다.

명령은 관제 클라이언트에서 다음 API 계약으로 생성한다. 웹 화면에서 수행하는 조작은 후반 웹 시연에서 다시 보여준다.

```http
POST /api/robots/{robotId}/commands
Authorization: Bearer {accessToken}
Content-Type: application/json

{"commandType":"START_PATROL"}
```

## 3. 촬영 이미지 업로드 및 AI 분석

### 3.1 Spring 업로드

로봇 이벤트에서 선택한 원본 프레임과 분석 ROI를 Spring에 업로드한다. 프론트 프록시를 사용할 때는 `http://localhost:3000/api/damages`, 백엔드 포트를 직접 사용할 때는 `http://localhost:8081/api/damages`를 사용한다.

```bash
curl -X POST "http://localhost:8081/api/damages" \
  -F "robotId=1" \
  -F "description=점자블록 파손 후보" \
  -F "latitude=37.5665000" \
  -F "longitude=126.9780000" \
  -F "capturedAt=2026-08-07T13:50:00" \
  -F "images=@original-frame.jpg" \
  -F "images=@analysis-roi.jpg"
```

인증 사용자가 업로드하면 `Authorization: Bearer {accessToken}`을 추가한다. 미인증 로봇 업로드는 `robotId`가 필수다.

### 3.2 비동기 처리 확인

업로드 성공 직후 응답의 `currentStatus`는 `AI_ANALYZING`이다. 이후 다음 순서로 처리된다.

1. Spring이 `damages`와 `damage_images`에 파손 정보·이미지를 저장한다.
2. `damage_ai_analysis_results`에 `QUEUED` 작업을 만들고 Redis 분석 큐에 등록한다.
3. Spring worker가 작업을 `PROCESSING`으로 바꾸고 AI 서버 `POST /analyze`를 호출한다.
4. AI 서버가 `damaged`, `damage_score`, `damage_type`, `analysis_detail`을 반환한다.
5. Spring이 구조화 컬럼과 전체 응답 JSON(`raw_result`)을 저장하고 상태를 `SUCCESS`/`AI_ANALYZED`로 변경한다.

```bash
curl "http://localhost:8081/api/damages/{damageId}"
curl "http://localhost:8000/health/ready"
```

`AI_ANALYZED`가 될 때까지 응답을 주기적으로 조회한다. AI 서버 `/analyze`는 Spring worker 전용이므로 브라우저나 로봇에서 직접 호출하지 않는다.

## 4. 웹 시연: 로그인 및 대시보드

1. 브라우저에서 `http://localhost:3000` 또는 운영 도메인을 연다.
2. 로그인 화면에서 `아이디` 입력란을 클릭하고 `admin`을 입력한다.
3. `비밀번호`에 `roady0810`을 입력하고 `로그인`을 클릭한다.
4. `/` 대시보드에서 업로드한 사건이 통계와 최근 목록에 반영되는지 확인한다.
   - `신규 탐지`: 아직 검토하지 않은 파손 사건 수
   - `긴급 확인 필요`: 높은 우선순위 사건 수
   - `요청 전`: 검토는 끝났지만 보수 요청 전인 사건 수
   - `운행 중 로디`: 현재 운행 중인 로봇 수
   - `실시간 탐지 현황`: 지도 마커를 클릭하면 사건 상세로 이동
   - `신규 탐지 알림`: 최근 파손 목록
   - `탐지 추이 분석`: 기간별 탐지·보수 완료 차트

## 5. 웹 시연: AI 파손 분석·검토

### 5.1 사건 목록과 지도

1. 왼쪽 사이드바에서 `탐지 검토`를 클릭한다.
2. 상단 `탐지 사건 조회 조건`에서 날짜 범위를 유지하고 `검색`을 클릭한다.
3. `미확인` 탭을 선택해 아직 관리자 판정이 없는 사건을 확인한다.
4. 목록 카드 또는 중앙 지도 마커를 클릭한다.
5. 오른쪽 `사건 상세 정보` 패널에서 사건명, 주소, 탐지 시각, 탐지 로봇, 이미지를 확인한다.

### 5.2 AI 결과 설명

상세 패널의 `AI 판독 요약`에서 다음 항목을 설명한다.

- 심각도/보수 우선순위
- 파손 유형
- 파손 점수
- 모델 신뢰도
- AI 분석 상태

AI 분석 중인 사건은 `AI 분석 중입니다. 분석 완료 후 판정할 수 있습니다.`가 표시된다. 분석 완료 사건은 AI 결과와 이미지를 함께 보여준다. 결과의 전체 JSON은 Spring의 `damage_ai_analysis_results.raw_result`에 보존된다.

### 5.3 관리자 판정 저장

분석 완료 사건에서:

1. `보수 필요` 버튼을 클릭한다.
2. `우선순위`를 선택한다.
3. `파손 유형`을 선택한다.
4. 필요하면 비고를 입력한다.
5. 판정 모달의 저장/확인 버튼을 클릭한다.
6. 사건 상태가 `REQUESTED`로 바뀌고 `보수 관리`에서 요청 전 사건으로 조회되는 것을 확인한다.

보수가 필요하지 않은 사례를 보여주려면 `보수 불필요`를 클릭하고 확인한다. 사건은 `CANCELED`로 바뀐다.

## 6. 웹 시연: 보수 요청·완료

### 6.1 보수 요청

1. 왼쪽 사이드바에서 `보수 관리`를 클릭한다.
2. 상태 필터에서 `요청 전` 또는 `REQUESTED`에 해당하는 항목을 선택한다.
3. 시드 데이터의 `봉은사역 보도 점자블록 이탈 탐지` 또는 검토에서 방금 저장한 사건의 행을 클릭한다.
4. 보수 사건 상세 화면 오른쪽 `보수 현황` 카드에서 `보수 요청`을 클릭한다.
5. `보수 요청서 작성` 모달에서 다음을 입력한다.
   - 보수 담당자: `보수 담당자` 계정 선택
   - 우선순위와 파손 유형 확인
   - 외부 담당자에게 전달할 비고(선택)
6. `보수 요청하기`를 클릭하고 확인 단계에서 다시 요청을 전송한다.
7. 상태가 `REPAIR_IN_PROGRESS`로 바뀌는지 확인한다.

### 6.2 요청서 확인, 수정, 취소

1. `REPAIR_IN_PROGRESS` 사건에서 `요청서 확인`을 클릭한다.
2. 요청자, 보수 담당자, 우선순위, 파손 유형, 탐지 이미지, 비고를 확인한다.
3. 수정이 필요하면 모달의 수정 기능을 사용하고 `저장`을 클릭한다.
4. 요청을 취소하는 흐름은 상세 화면의 `요청 취소` → 확인 모달의 `요청 취소` 순서로 진행한다.
5. 취소 후 상태가 다시 `REQUESTED`로 돌아가 재요청할 수 있음을 설명한다.

### 6.3 보수 완료

1. `REPAIR_IN_PROGRESS` 사건에서 `보수 완료`를 클릭한다.
2. `보수 완료 처리` 모달에서 완료 일자를 입력한다.
3. 완료 메모를 입력한다(선택).
4. `다음`을 클릭해 확인 단계로 이동한다.
5. `확인`을 클릭한다.
6. 상태가 `REPAIR_COMPLETED`로 변경되고 완료 일자·완료 메모가 표시되는지 확인한다.
7. `완료 보고서 확인` → `내용 복사`로 보고서 텍스트를 클립보드에 복사할 수 있음을 보여준다.

## 7. 웹 시연: 로봇 상태 및 관제 결과 확인

앞 단계에서 수행한 로봇 운행·제어 결과가 웹에 반영되는지 확인한다.

1. 왼쪽 사이드바에서 `로디 운행`을 클릭한다.
2. `로봇 위치 현황` 지도에서 대상 로봇 마커를 선택한다.
3. `긴급 확인` 카드에서 오류, 연결 끊김, 배터리 부족 로봇을 확인한다.
4. `운행 상태`, `연결 상태`, `정렬 기준`을 선택하고 `검색`을 클릭한다.
5. 목록의 `상세 보기` 버튼을 클릭한다.
6. `실시간 위치 및 이동 경로` 지도에서 위치와 경로를 확인한다.
7. `최신 상태` 카드에서 배터리, 운행 상태, 통신 상태, 오류 메시지를 확인한다.
8. `명령 이력`에서 `START_PATROL`, `RETURN_HOME`, `EMERGENCY_STOP`의 상태가 `SUCCEEDED` 또는 처리 결과로 기록됐는지 확인한다.
9. 필요하면 `스테이션 복귀`, `순찰 시작`, `긴급 정지` 버튼을 눌러 웹 관제 명령도 시연한다.

MQTT telemetry는 `roady/{robotId}/telemetry`, 제어 명령은 `roady/{robotId}/command`로 전달된다. 실제 로봇이 연결되지 않은 시연에서는 initializer의 최신 상태 또는 MQTT mock publisher를 사용한다.

## 8. AI 서버 연동 상태 확인(선택)

1. `docker compose ps`에서 `roady-ai`가 healthy인지 확인한다.
2. `http://localhost:8000/health/ready`가 `{"status":"ready"}`인지 확인한다.
3. 파손 이미지 등록은 프론트의 파손 등록 흐름 또는 Spring API `POST /api/damages`에서 수행한다.
4. Spring이 이미지와 `analysisMetadata`를 Redis queue worker를 통해 AI 서버 `POST /analyze`로 전달한다.
5. AI 결과가 저장되면 사건 상태가 `AI_ANALYZED`로 바뀌고, 화면에서 AI 판독 요약을 확인한다.
6. 운영자 수동 재분석은 상세 화면의 재분석 동작 또는 `/api/damages/{damageId}/analysis-jobs`를 사용한다.

## 9. 시연 종료 및 초기화

시연 중 생성한 요청 상태를 보존하려면 컨테이너만 중지한다.

```bash
docker compose stop
```

다음 시연에서 데이터를 새로 만들려면 named volume까지 삭제한 뒤 다시 시작해야 한다. 이 명령은 DB 데이터와 Redis/MQTT persistence를 삭제하므로 운영 환경에서는 실행하지 않는다.

```bash
docker compose down -v
docker compose up -d --build
```

## 10. 장애 대응

| 증상 | 확인 위치 | 조치 |
| --- | --- | --- |
| 로그인 502 | frontend Nginx `/api` proxy, backend logs | backend health와 8080 연결 확인 |
| AI 분석이 계속 대기 | `docker compose logs ai backend` | AI readiness, worker enabled, Redis queue 확인 |
| 지도는 비어 있음 | 브라우저 네트워크, 좌표 필드 | 위치 데이터와 OSM tile 요청 확인 |
| 이미지가 안 보임 | `/api/damages/{id}/images/{imageId}/content` | damage_images 존재와 backend 응답 확인 |
| 로봇 위치 미갱신 | Mosquitto logs, topic | `roady/{robotId}/telemetry`, MQTT broker 주소 확인 |
