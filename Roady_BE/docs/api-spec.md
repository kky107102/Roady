# Roady API 명세서

## 1. 문서 개요

- 서비스명: Roady
- API 버전: v1
- 기본 경로: `/api`
- 데이터 형식: JSON
- 인증 방식: JWT Bearer Token
- Swagger UI: `/swagger-ui/index.html`
- OpenAPI JSON: `/v3/api-docs`

이 문서는 현재 백엔드 코드에 구현된 API와 서버 요구사항 명세를 함께 기준으로 작성한다. 각 API는 `구현됨`, `설계안`, `후속 확장` 상태로 구분한다. 제출 기준의 실제 구현 범위는 `구현됨` 항목이며, `설계안`은 다음 구현 대상, `후속 확장`은 완료 보고서·행정문서처럼 저장 구조나 화면 요구사항이 추가 확정되어야 하는 기능이다.

### 1.1 전체 API 목록

| 구분 | Method | URL | 상태 | 설명 |
| --- | --- | --- | --- | --- |
| 인증 | `POST` | `/api/auth/signup` | 구현됨 | 회원가입 |
| 인증 | `POST` | `/api/auth/login` | 구현됨 | 로그인 및 토큰 발급 |
| 인증 | `POST` | `/api/auth/refresh` | 구현됨 | Access Token 재발급 |
| 인증 | `POST` | `/api/auth/logout` | 구현됨 | Refresh Token 삭제 |
| 인증 | `GET` | `/api/auth/me` | 구현됨 | 내 정보 조회 |
| 사용자 | `GET` | `/api/users` | 구현됨 | 사용자 목록 조회 |
| 사용자 | `POST` | `/api/users` | 구현됨 | 사용자 생성 |
| 사용자 | `PATCH` | `/api/users/{userId}/role` | 구현됨 | 사용자 권한 변경 |
| 사용자 | `PATCH` | `/api/users/{userId}/active` | 구현됨 | 사용자 활성 상태 변경 |
| 사용자 | `PATCH` | `/api/users/{userId}/assigned-region` | 구현됨 | 사용자 담당 시군구 코드 변경 |
| 파손 | `POST` | `/api/damages` | 구현됨 | 파손 이미지와 위치 정보 저장 후 AI 분석 작업 자동 등록 |
| 파손 | `GET` | `/api/damages` | 구현됨 | 파손 목록 검색, 지역코드·기간 필터 및 페이지 조회 |
| 파손 | `GET` | `/api/damages/{damageId}` | 구현됨 | 파손 상세 조회 |
| 파손 | `PATCH` | `/api/damages/{damageId}/review` | 구현됨 | 관리자 검토 단계에서 파손 상태, 처리 우선순위, 판정 파손 유형, 비고 수정 |
| 파손 | `GET` | `/api/damages/{damageId}/images/{imageId}/content` | 구현됨 | 파손 이미지 바이너리 조회 |
| 파손 | `GET` | `/api/damages/map-markers` | 구현됨 | 지도 표시용 파손 마커 조회 |
| 대시보드 | `GET` | `/api/dashboard/damages/summary` | 구현됨 | 파손 전체·미배정·상태별 건수 조회 |
| 파손 | `GET` | `/api/damages/{damageId}/duplicates` | 설계안 | 동일/인접 위치 중복 후보 조회 |
| 파손 | `POST` | `/api/damages/{damageId}/reviews` | 후속 확장 | 점검 담당자 검토 의견 등록 |
| 파손 | `GET` | `/api/damages/{damageId}/reviews` | 후속 확장 | 점검 담당자 검토 의견 조회 |
| 로봇 | `POST` | `/api/robots` | 구현됨 | 로봇 등록 |
| 로봇 | `GET` | `/api/robots` | 구현됨 | 로봇 목록 및 현재 상태 조회 |
| 로봇 | `GET` | `/api/robots/{robotId}` | 구현됨 | 로봇 상세 조회 |
| 로봇 | `PATCH` | `/api/robots/{robotId}` | 구현됨 | 로봇 정보 수정 |
| 로봇 | `PATCH` | `/api/robots/{robotId}/active` | 구현됨 | 로봇 활성 상태 변경 |
| 로봇 상태 | `POST` | `/api/robots/{robotId}/status-logs` | 구현됨 | 로봇 위치, 배터리, 운행 상태 등록 |
| 로봇 상태 | `GET` | `/api/robots/{robotId}/status-logs/latest` | 구현됨 | 로봇 최신 상태 조회 |
| 로봇 상태 | `GET` | `/api/robots/{robotId}/status-logs` | 구현됨 | 로봇 상태 로그 조회 |
| 로봇 명령 | `POST` | `/api/robots/{robotId}/commands` | 구현됨 | 로봇 제어 명령 생성 |
| 로봇 명령 | `GET` | `/api/robots/{robotId}/commands` | 구현됨 | 로봇 제어 명령 이력 조회 |
| 로봇 명령 | `GET` | `/api/robots/{robotId}/commands/pending` | 구현됨 | 로봇 미처리 명령 조회 |
| 로봇 명령 | `PATCH` | `/api/robots/{robotId}/commands/{commandId}/status` | 구현됨 | 로봇 제어 명령 상태 변경 |
| 로봇 경로 | `POST` | `/api/robot-routes` | 구현됨 | 점검 경로 생성 |
| 로봇 경로 | `GET` | `/api/robot-routes` | 구현됨 | 점검 경로 목록 조회 |
| 로봇 경로 | `GET` | `/api/robot-routes/{routeId}` | 구현됨 | 점검 경로 상세 조회 |
| 로봇 경로 | `PUT` | `/api/robot-routes/{routeId}` | 구현됨 | 점검 경로 수정 |
| 로봇 경로 | `DELETE` | `/api/robot-routes/{routeId}` | 구현됨 | 점검 경로 삭제 |
| 로봇 경로 | `POST` | `/api/robot-routes/{routeId}/dispatch` | 설계안 | 점검 경로 로봇 전송 |
| 로봇 경로 | `GET` | `/api/robot-routes/{routeId}/actual-path` | 설계안 | 실제 이동 경로 조회 |
| AI 분석 | `POST` | `/api/damages/{damageId}/analysis-jobs` | 구현됨 | 저장된 파손 이미지 수동 재분석 작업 생성 |
| AI 분석 | `GET` | `/api/damages/{damageId}/analysis-jobs` | 구현됨 | 파손별 AI 분석 작업 목록 조회 |
| AI 분석 | `GET` | `/api/damage-ai-analysis-results/{analysisResultId}` | 구현됨 | AI 분석 결과 단건 조회 |
| AI 분석 | `POST` | `/api/damages/{damageId}/ai-analysis` | 설계안 | AI 분석 요청 |
| AI 분석 | `GET` | `/api/damages/{damageId}/ai-analysis` | 설계안 | AI 분석 결과 조회 |
| AI 분석 | `POST` | `/api/damages/{damageId}/ai-analysis/retry` | 설계안 | AI 분석 재시도 |
| AI 분석 | `PATCH` | `/api/damages/{damageId}/ai-analysis` | 설계안 | AI 분석 결과 수정 |
| AI 분석 | `POST` | `/api/damages/{damageId}/ai-analysis/confirm` | 설계안 | AI 분석 결과 확정 |
| 처리 상태 | `PATCH` | `/api/damages/{damageId}/review` | 구현됨 | 관리자 검토 단계에서 파손 처리 상태, 우선순위, 판정 파손 유형, 비고 수정 |
| 보수 배정 | `POST` | `/api/repair-assignments` | 설계안 | 보수 담당자와 예정일 배정, 파손 상태 변경, 요청 이력 저장 |
| 보수 배정 | `GET` | `/api/repair-assignments` | 설계안 | 보수 배정 목록 조회 |
| 보수 배정 | `GET` | `/api/repair-assignments/{assignmentId}` | 설계안 | 보수 배정 상세 조회 |
| 보수 배정 | `PATCH` | `/api/repair-assignments/{assignmentId}` | 설계안 | 보수 담당자, 예정일, 메모 수정 |
| 보수 배정 | `PATCH` | `/api/repair-assignments/{assignmentId}/start` | 설계안 | 보수 작업 시작 처리 |
| 보수 배정 | `PATCH` | `/api/repair-assignments/{assignmentId}/cancel` | 설계안 | 보수 요청 또는 예정 건 취소 처리 |
| 보수 요청 이력 | `GET` | `/api/repair-assignments/{assignmentId}/request-histories` | 설계안 | 보수 요청/배정/취소 이력 조회 |
| 보수 결과 | `POST` | `/api/repair-results` | 후속 확장 | 보수 결과 등록 |
| 보수 결과 | `GET` | `/api/repair-results/{resultId}` | 후속 확장 | 보수 결과 상세 조회 |
| 보수 결과 | `GET` | `/api/damages/{damageId}/repair-result` | 후속 확장 | 파손별 보수 결과 조회 |
| 통계 | `GET` | `/api/statistics/damages/time-series` | 구현됨 | 기간별 파손 통계 조회 |
| 통계 | `GET` | `/api/statistics/damages/by-repair-priority` | 구현됨 | 보수 우선순위별 파손 통계 조회 |
| 통계 | `GET` | `/api/statistics/damages/by-status` | 구현됨 | 처리 상태별 통계 조회 |
| 통계 | `GET` | `/api/statistics/repair/completion-rate` | 구현됨 | 보수 완료율 조회 |
| 통계 | `GET` | `/api/statistics/export` | 설계안 | 통계 CSV/Excel 다운로드 |
| 행정문서 | `POST` | `/api/documents` | 설계안 | 행정문서 초안 생성 |
| 행정문서 | `GET` | `/api/documents` | 설계안 | 행정문서 목록 조회 |
| 행정문서 | `GET` | `/api/documents/{documentId}` | 설계안 | 행정문서 상세 조회 |
| 행정문서 | `PATCH` | `/api/documents/{documentId}` | 설계안 | 행정문서 초안 수정 |
| 행정문서 | `GET` | `/api/documents/{documentId}/download` | 설계안 | 행정문서 파일 다운로드 |
| 감사 로그 | `GET` | `/api/audit-logs` | 설계안 | 주요 작업 이력 조회 |

## 2. API 구성 원칙

### 2.1 현재 구현 도메인

| 구분 | 경로 | 설명 |
| --- | --- | --- |
| 인증 | `/api/auth` | 로그인, 토큰 재발급, 로그아웃, 내 정보 조회 |
| 사용자 관리 | `/api/users` | 사용자 목록 조회, 생성, 권한 변경, 활성 상태 변경 |
| 도로 파손 | `/api/damages` | 파손 정보 등록, 목록 검색, 지도 마커, 상세 및 이미지 조회 |
| 대시보드 | `/api/dashboard/damages` | 파손 전체·미배정·상태별 건수 조회 |

### 2.2 권한 구성

| 권한 | 설명 |
| --- | --- |
| `ADMIN` | 관리자 |
| `INSPECTOR` | 점검 담당자 |
| `REPAIRER` | 보수 담당자 |
| `VIEWER` | 조회 사용자 |

현재 구현 기준 권한 규칙은 다음과 같다.

| 대상 | 인증 필요 | 권한 |
| --- | --- | --- |
| `POST /api/auth/signup` | 아니오 | 전체 허용. 기본 `VIEWER` 생성 |
| `POST /api/auth/login` | 아니오 | 전체 허용 |
| `POST /api/auth/refresh` | 아니오 | 전체 허용 |
| `/api/users/**` | 예 | `ADMIN` |
| 그 외 `/api/**` | 예 | 로그인 사용자 |
| Swagger/OpenAPI | 아니오 | 전체 허용 |

### 2.3 인증 헤더

로그인 또는 토큰 재발급 API에서 받은 `accessToken`을 다음 형식으로 전달한다.

```http
Authorization: Bearer {accessToken}
```

### 2.4 날짜/시간 형식

- 요청/응답의 날짜와 시간은 ISO-8601 형식을 사용한다.
- 예시: `2026-07-22T14:30:00`

### 2.5 공통 에러 응답

일반 예외와 검증 실패는 다음 형식으로 반환된다.

```json
{
  "timestamp": "2026-07-22T14:30:00",
  "status": 400,
  "message": "요청 값이 올바르지 않습니다.",
  "errors": [
    "password: size must be between 8 and 100"
  ]
}
```

인증 실패와 권한 실패는 현재 구현상 다음처럼 `message`만 포함하는 JSON을 반환한다.

```json
{
  "message": "로그인이 필요합니다."
}
```

### 2.6 주요 상태 코드

| 상태 코드 | 의미 |
| --- | --- |
| `200 OK` | 요청 성공 |
| `201 Created` | 리소스 생성 성공 |
| `400 Bad Request` | 요청 값 오류, 유효하지 않은 토큰, 존재하지 않는 리소스 등 |
| `401 Unauthorized` | 인증 실패 또는 인증 정보 없음 |
| `403 Forbidden` | 권한 없음 또는 비활성 계정 |

## 3. 인증 API

### 3.1 회원가입

일반 사용자가 계정을 생성한다. 가입한 사용자는 기본 `VIEWER` 권한으로 생성된다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/api/auth/signup` |
| 인증 | 불필요 |
| Content-Type | `application/json` |

#### Request Body

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `username` | string | 예 | 빈 값 불가 | 사용자 아이디 |
| `password` | string | 예 | 8~100자 | 비밀번호 |
| `email` | string | 예 | 이메일 형식 | 이메일 |
| `name` | string | 예 | 빈 값 불가 | 이름 |

```json
{
  "username": "viewer01",
  "password": "password123",
  "email": "viewer01@example.com",
  "name": "조회 사용자"
}
```

#### Response `201 Created`

```json
{
  "id": 5,
  "username": "viewer01",
  "email": "viewer01@example.com",
  "name": "조회 사용자",
  "role": "VIEWER",
  "active": true,
  "createdAt": "2026-07-27T13:45:00"
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 요청 값 검증 실패, 중복 username/email |

### 3.2 로그인

사용자명과 비밀번호로 로그인하고 access token과 refresh token을 발급한다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/api/auth/login` |
| 인증 | 불필요 |
| Content-Type | `application/json` |

#### Request Body

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `username` | string | 예 | 빈 값 불가 | 사용자 아이디 |
| `password` | string | 예 | 빈 값 불가 | 비밀번호 |

```json
{
  "username": "admin",
  "password": "password123"
}
```

#### Response `200 OK`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `tokenType` | string | 토큰 타입. 현재 `Bearer` |
| `accessToken` | string | API 인증용 JWT |
| `refreshToken` | string | access token 재발급용 JWT |
| `expiresInSeconds` | number | access token 만료 시간. 기본 1800초 |

```json
{
  "tokenType": "Bearer",
  "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9...",
  "expiresInSeconds": 1800
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 요청 값 검증 실패 |
| `401` | 아이디 또는 비밀번호 불일치 |
| `403` | 비활성 계정 |

### 3.3 토큰 재발급

refresh token으로 새 access token을 발급한다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/api/auth/refresh` |
| 인증 | 불필요 |
| Content-Type | `application/json` |

#### Request Body

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `refreshToken` | string | 예 | 빈 값 불가 | 로그인 또는 이전 재발급에서 받은 refresh token |

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9..."
}
```

#### Response `200 OK`

```json
{
  "tokenType": "Bearer",
  "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9...",
  "expiresInSeconds": 1800
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | refresh token이 비어 있음, 유효하지 않음, 저장된 토큰과 불일치, 활성 사용자를 찾을 수 없음 |

### 3.4 로그아웃

refresh token을 삭제하여 재발급을 막는다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/api/auth/logout` |
| 인증 | 필요 |
| Content-Type | `application/json` |

#### Request Body

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `refreshToken` | string | 예 | 빈 값 불가 | 삭제할 refresh token |

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9..."
}
```

#### Response `200 OK`

응답 본문 없음.

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | refresh token이 비어 있음 또는 유효하지 않음 |
| `401` | access token 없음 또는 인증 실패 |

### 3.5 내 정보 조회

현재 로그인한 사용자의 기본 정보를 조회한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/api/auth/me` |
| 인증 | 필요 |

#### Response `200 OK`

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 사용자 ID |
| `username` | string | 사용자 아이디 |
| `role` | string | 사용자 권한 |

```json
{
  "id": 1,
  "username": "admin",
  "role": "ADMIN"
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `401` | access token 없음 또는 인증 실패 |

## 4. 사용자 관리 API

사용자 생성·수정 API는 `ADMIN` 권한이 필요하다. 사용자 목록 조회는 보수 담당자 선택을 위해 `ADMIN`, `INSPECTOR`가 사용할 수 있다.

### 4.1 사용자 목록 조회

등록된 사용자 목록을 조회한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/api/users?role=REPAIRER&active=true` |
| 인증 | 필요 |
| 권한 | `ADMIN`, `INSPECTOR` |

#### Query Parameter

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `role` | string | 아니오 | `ADMIN`, `INSPECTOR`, `REPAIRER`, `VIEWER` 중 하나 |
| `active` | boolean | 아니오 | 계정 활성 여부 |

#### Response `200 OK`

```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "name": "관리자",
    "assignedRegionCode": "41550",
    "role": "ADMIN",
    "active": true,
    "createdAt": "2026-07-22T14:30:00"
  }
]
```

#### UserResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 사용자 ID |
| `username` | string | 사용자 아이디 |
| `email` | string | 이메일 |
| `name` | string | 이름 |
| `assignedRegionCode` | string, null | 담당 시군구 코드. 미배정이면 `null` |
| `role` | string | 사용자 권한 |
| `active` | boolean | 계정 활성 여부 |
| `createdAt` | string | 생성 일시 |

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `401` | 인증 실패 |
| `403` | `ADMIN`, `INSPECTOR` 권한 없음 |

### 4.2 사용자 생성

새 사용자를 생성한다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/api/users` |
| 인증 | 필요 |
| 권한 | `ADMIN` |
| Content-Type | `application/json` |

#### Request Body

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `username` | string | 예 | 빈 값 불가 | 사용자 아이디 |
| `password` | string | 예 | 8~100자 | 비밀번호 |
| `email` | string | 예 | 이메일 형식 | 이메일 |
| `name` | string | 예 | 빈 값 불가 | 이름 |
| `role` | string | 예 | `ADMIN`, `INSPECTOR`, `REPAIRER`, `VIEWER` | 사용자 권한 |

```json
{
  "username": "inspector01",
  "password": "password123",
  "email": "inspector01@example.com",
  "name": "점검 담당자",
  "role": "INSPECTOR"
}
```

#### Response `200 OK`

```json
{
  "id": 2,
  "username": "inspector01",
  "email": "inspector01@example.com",
  "name": "점검 담당자",
  "assignedRegionCode": null,
  "role": "INSPECTOR",
  "active": true,
  "createdAt": "2026-07-22T14:30:00"
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 요청 값 검증 실패, 중복 username/email |
| `401` | 인증 실패 |
| `403` | 관리자 권한 없음 |

### 4.3 사용자 권한 변경

특정 사용자의 권한을 변경한다.

| 항목 | 내용 |
| --- | --- |
| Method | `PATCH` |
| URL | `/api/users/{userId}/role` |
| 인증 | 필요 |
| 권한 | `ADMIN` |
| Content-Type | `application/json` |

#### Path Parameter

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `userId` | number | 사용자 ID |

#### Request Body

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `role` | string | 예 | `ADMIN`, `INSPECTOR`, `REPAIRER`, `VIEWER` | 변경할 권한 |

```json
{
  "role": "REPAIRER"
}
```

#### Response `200 OK`

```json
{
  "id": 2,
  "username": "inspector01",
  "email": "inspector01@example.com",
  "name": "점검 담당자",
  "assignedRegionCode": null,
  "role": "REPAIRER",
  "active": true,
  "createdAt": "2026-07-22T14:30:00"
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 요청 값 검증 실패, 존재하지 않는 사용자 |
| `401` | 인증 실패 |
| `403` | 관리자 권한 없음 |

### 4.4 사용자 활성 상태 변경

특정 사용자의 계정 활성 여부를 변경한다.

| 항목 | 내용 |
| --- | --- |
| Method | `PATCH` |
| URL | `/api/users/{userId}/active` |
| 인증 | 필요 |
| 권한 | `ADMIN` |
| Content-Type | `application/json` |

#### Path Parameter

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `userId` | number | 사용자 ID |

#### Request Body

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `active` | boolean | 예 | null 불가 | 활성 여부 |

```json
{
  "active": false
}
```

#### Response `200 OK`

```json
{
  "id": 2,
  "username": "inspector01",
  "email": "inspector01@example.com",
  "name": "점검 담당자",
  "assignedRegionCode": null,
  "role": "REPAIRER",
  "active": false,
  "createdAt": "2026-07-22T14:30:00"
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 요청 값 검증 실패, 존재하지 않는 사용자 |
| `401` | 인증 실패 |
| `403` | 관리자 권한 없음 |

### 4.5 사용자 담당 시군구 코드 변경

특정 사용자의 담당 시군구 코드를 변경한다. 코드는 별도 시군구 코드 테이블이나 외부 행정구역 코드 데이터와 조인해 해석한다.

| 항목 | 내용 |
| --- | --- |
| Method | `PATCH` |
| URL | `/api/users/{userId}/assigned-region` |
| 인증 | 필요 |
| 권한 | `ADMIN` |
| Content-Type | `application/json` |

#### Path Parameter

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `userId` | number | 사용자 ID |

#### Request Body

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `assignedRegionCode` | string, null | 아니오 | 최대 10자 | 담당 시군구 코드. `null` 또는 빈 값이면 담당구를 해제한다. |

```json
{
  "assignedRegionCode": "41550"
}
```

#### Response `200 OK`

```json
{
  "id": 2,
  "username": "inspector01",
  "email": "inspector01@example.com",
  "name": "점검 담당자",
  "assignedRegionCode": "41550",
  "role": "INSPECTOR",
  "active": true,
  "createdAt": "2026-07-22T14:30:00"
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 요청 값 검증 실패, 존재하지 않는 사용자 |
| `401` | 인증 실패 |
| `403` | 관리자 권한 없음 |

## 5. 도로 파손 API

도로 파손 API는 로그인한 사용자가 사용할 수 있다. 등록 API의 `reportedBy`는 요청 사용자의 ID로 자동 설정된다.

### 5.1 도로 파손 등록

도로 파손 정보와 이미지를 등록한다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/api/damages` |
| 인증 | 필요 |
| Content-Type | `multipart/form-data` |

#### Form Data

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `robotId` | number | 아니오 | 존재하는 로봇 ID | 파손을 촬영한 로봇 ID |
| `assignedTo` | number | 아니오 | 존재하는 사용자 ID | 처리 담당 사용자 ID |
| `description` | string | 아니오 | - | 파손 설명 |
| `latitude` | decimal | 아니오 | DB 기준 `DECIMAL(10,7)` | 위도 |
| `longitude` | decimal | 아니오 | DB 기준 `DECIMAL(10,7)` | 경도 |
| `capturedAt` | string | 아니오 | ISO-8601 | 촬영 일시 |
| `images` | file[] | 예 | 1~50개, `image/*`, 빈 파일 불가 | 파손 이미지 목록 |

#### Request Example

```bash
curl -X POST "http://localhost:8080/api/damages" \
  -H "Authorization: Bearer {accessToken}" \
  -F "robotId=1" \
  -F "description=도로 균열 감지" \
  -F "latitude=37.5665000" \
  -F "longitude=126.9780000" \
  -F "capturedAt=2026-07-22T14:30:00" \
  -F "images=@damage-1.jpg" \
  -F "images=@damage-2.jpg"
```

#### Response `201 Created`

```json
{
  "id": 1,
  "robotId": 1,
  "reportedBy": 2,
  "assignedTo": null,
  "assignedToName": null,
  "repairerId": null,
  "repairerName": null,
  "description": "도로 균열 감지",
  "addressName": "경기 안성시 죽산면 죽산리 343-1",
  "roadAddressName": "경기 안성시 죽산초교길 69-4",
  "regionCode": "41550",
  "region1DepthName": "경기",
  "region2DepthName": "안성시",
  "region3DepthName": "죽산면",
  "geocodedAt": "2026-07-22T14:30:01",
  "latitude": 37.5665000,
  "longitude": 126.9780000,
  "capturedAt": "2026-07-22T14:30:00",
  "currentStatus": "COLLECTED",
  "processingPriority": null,
  "reviewDamageType": null,
  "reviewNote": null,
  "repairRequestedAt": null,
  "repairRequestNote": null,
  "repairCompletedAt": null,
  "repairCompletionNote": null,
  "imageCount": 2,
  "images": [
    {
      "id": 1,
      "damageId": 1,
      "sortOrder": 1,
      "originalFilename": "damage-1.jpg",
      "contentType": "image/jpeg",
      "sizeBytes": 123456,
      "createdAt": "2026-07-22T14:30:01"
    }
  ],
  "createdAt": "2026-07-22T14:30:01",
  "updatedAt": "2026-07-22T14:30:01"
}
```

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 이미지 없음, 이미지 50개 초과, 빈 파일, 이미지가 아닌 파일, 존재하지 않는 `robotId` 또는 `assignedTo` |
| `401` | 인증 실패 |

### 5.2 도로 파손 목록 조회

등록된 도로 파손 목록을 검색하고 페이지 단위로 조회한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/api/damages` |
| 인증 | 필요 |

#### Query Parameter

| 필드 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `from` | string | 아니오 | 없음 | 등록 일시 시작값. 해당 일시를 포함한다. |
| `to` | string | 아니오 | 없음 | 등록 일시 종료값. 해당 일시를 포함하지 않는다. |
| `status` | string | 아니오 | 없음 | 파손 처리 상태 |
| `robotId` | number | 아니오 | 없음 | 촬영 로봇 ID |
| `assignedTo` | number | 아니오 | 없음 | 처리 담당 사용자 ID |
| `regionCode` | string | 아니오 | 없음 | 시군구 코드. `damages.region_code`와 정확히 일치하는 파손만 조회 |
| `keyword` | string | 아니오 | 없음 | 사건번호 또는 주소 키워드. 숫자만 있으면 사건번호(`id`)와도 매칭하고, 주소 필드도 부분 검색 |
| `page` | number | 아니오 | `0` | 0부터 시작하는 페이지 번호 |
| `size` | number | 아니오 | `20` | 페이지 크기. 1 이상 100 이하 |

#### Response `200 OK`

```json
{
  "content": [
    {
      "id": 1,
      "robotId": 1,
      "assignedTo": null,
      "description": "도로 균열 감지",
      "addressName": "경기 안성시 죽산면 죽산리 343-1",
      "roadAddressName": "경기 안성시 죽산초교길 69-4",
      "regionCode": "41550",
      "region1DepthName": "경기",
      "region2DepthName": "안성시",
      "region3DepthName": "죽산면",
      "geocodedAt": "2026-07-22T14:30:01",
      "latitude": 37.5665000,
      "longitude": 126.9780000,
      "capturedAt": "2026-07-22T14:30:00",
      "currentStatus": "COLLECTED",
      "processingPriority": null,
      "reviewDamageType": null,
      "reviewNote": null,
      "imageCount": 2,
      "createdAt": "2026-07-22T14:30:01"
    }
  ],
  "page": 0,
  "size": 20,
  "totalElements": 1,
  "totalPages": 1
}
```

#### DamageSearchResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `content` | array | 현재 페이지의 파손 목록 |
| `content[].id` | number | 파손 ID |
| `content[].robotId` | number, null | 촬영 로봇 ID |
| `content[].assignedTo` | number, null | 처리 담당 사용자 ID |
| `content[].description` | string, null | 파손 설명 |
| `content[].addressName` | string, null | 카카오 좌표 변환으로 얻은 지번 주소 |
| `content[].roadAddressName` | string, null | 카카오 좌표 변환으로 얻은 도로명 주소 |
| `content[].regionCode` | string, null | 카카오 행정구역 좌표 변환으로 얻은 시군구 코드 |
| `content[].region1DepthName` | string, null | 시도명 |
| `content[].region2DepthName` | string, null | 시군구명 |
| `content[].region3DepthName` | string, null | 읍면동명 |
| `content[].geocodedAt` | string, null | 주소/행정구역 변환 일시 |
| `content[].latitude` | decimal, null | 위도 |
| `content[].longitude` | decimal, null | 경도 |
| `content[].capturedAt` | string, null | 촬영 일시 |
| `content[].currentStatus` | string | 현재 처리 상태 |
| `content[].processingPriority` | string, null | 관리자가 수정한 처리 우선순위. `LOW`, `NORMAL`, `HIGH`, `URGENT` |
| `content[].reviewDamageType` | string, null | 관리자가 판정한 파손 유형. `LARGE_MISSING`, `SMALL_MISSING`, `WEAR`, `CRACK`, `OTHER` |
| `content[].reviewNote` | string, null | 관리자 판정 비고. 공백은 `null`로 저장하며 최대 1,000자 |
| `content[].imageCount` | number | 연결된 이미지 수 |
| `content[].createdAt` | string | 생성 일시 |
| `page` | number | 현재 페이지 번호 |
| `size` | number | 페이지 크기 |
| `totalElements` | number | 검색 조건에 해당하는 전체 데이터 수 |
| `totalPages` | number | 전체 페이지 수 |

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 잘못된 기간, 처리 상태, 페이지 번호 또는 페이지 크기 |
| `401` | 인증 실패 |

### 5.3 대시보드 파손 요약 조회

검색 조건에 해당하는 전체 파손 수, 미배정 수, 처리 상태별 수를 조회한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/api/dashboard/damages/summary` |
| 인증 | 필요 |

#### Query Parameter

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `from` | string | 아니오 | 등록 일시 시작값. 해당 일시를 포함한다. |
| `to` | string | 아니오 | 등록 일시 종료값. 해당 일시를 포함하지 않는다. |
| `status` | string | 아니오 | 파손 처리 상태 |
| `robotId` | number | 아니오 | 촬영 로봇 ID |
| `assignedTo` | number | 아니오 | 처리 담당 사용자 ID |
| `regionCode` | string | 아니오 | 시군구 코드. `damages.region_code`와 정확히 일치하는 파손만 집계 |

#### Response `200 OK`

```json
{
  "total": 123,
  "unassigned": 12,
  "statusCounts": {
    "COLLECTED": 20,
    "AI_ANALYZING": 12,
    "AI_ANALYZED": 23,
    "REQUESTED": 18,
    "REPAIR_IN_PROGRESS": 8,
    "REPAIR_COMPLETED": 27,
    "CANCELED": 5
  }
}
```

데이터가 없는 처리 상태도 `statusCounts`에 값 `0`으로 포함한다.

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 잘못된 기간 또는 처리 상태 |
| `401` | 인증 실패 |

### 5.4 지도 마커 조회

현재 지도 화면 범위에 표시할 파손 좌표와 현재 처리 상태를 조회한다. 위도 또는 경도가 없는 파손은 결과에서 제외한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/api/damages/map-markers` |
| 인증 | 필요 |

#### Query Parameter

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `from` | string | 아니오 | 등록 일시 시작값. 해당 일시를 포함한다. |
| `to` | string | 아니오 | 등록 일시 종료값. 해당 일시를 포함하지 않는다. |
| `status` | string | 아니오 | 파손 처리 상태 |
| `robotId` | number | 아니오 | 촬영 로봇 ID |
| `assignedTo` | number | 아니오 | 처리 담당 사용자 ID |
| `regionCode` | string | 아니오 | 시군구 코드. `damages.region_code`와 정확히 일치하는 파손만 조회 |
| `south` | decimal | 예 | 지도 남쪽 경계 위도. `-90` 이상이며 `north`보다 작아야 한다. |
| `north` | decimal | 예 | 지도 북쪽 경계 위도. `90` 이하여야 한다. |
| `west` | decimal | 예 | 지도 서쪽 경계 경도. `-180` 이상이며 `east`보다 작아야 한다. |
| `east` | decimal | 예 | 지도 동쪽 경계 경도. `180` 이하여야 한다. |

프론트엔드는 최초 지도 로딩 및 `moveend`, `zoomend` 시 현재 화면 경계를 전달한다. 지도 이동 중인 요청은 취소하고 짧은 debounce를 적용한다.

#### Response `200 OK`

```json
[
  {
    "id": 1,
    "latitude": 37.5665,
    "longitude": 126.978,
    "currentStatus": "AI_ANALYZED"
  }
]
```

#### DamageMapMarkerResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 파손 ID |
| `latitude` | decimal | 위도 |
| `longitude` | decimal | 경도 |
| `currentStatus` | string | 현재 처리 상태 |

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 지도 경계 누락, 잘못된 좌표 범위, 잘못된 기간 또는 처리 상태 |
| `401` | 인증 실패 |

### 5.5 도로 파손 상세 조회

특정 도로 파손의 상세 정보와 이미지 메타데이터를 조회한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/api/damages/{damageId}` |
| 인증 | 필요 |

#### Path Parameter

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `damageId` | number | 파손 ID |

#### Response `200 OK`

```json
{
  "id": 1,
  "robotId": 1,
  "reportedBy": 2,
  "assignedTo": null,
  "assignedToName": null,
  "repairerId": 9,
  "repairerName": "김보수",
  "description": "도로 균열 감지",
  "addressName": "경기 안성시 죽산면 죽산리 343-1",
  "roadAddressName": "경기 안성시 죽산초교길 69-4",
  "regionCode": "41550",
  "region1DepthName": "경기",
  "region2DepthName": "안성시",
  "region3DepthName": "죽산면",
  "geocodedAt": "2026-07-22T14:30:01",
  "latitude": 37.5665000,
  "longitude": 126.9780000,
  "capturedAt": "2026-07-22T14:30:00",
  "currentStatus": "COLLECTED",
  "processingPriority": null,
  "reviewDamageType": null,
  "reviewNote": null,
  "repairRequestedAt": "2026-08-04T10:00:00",
  "repairRequestNote": "현장 교체 요청",
  "repairCompletedAt": null,
  "repairCompletionNote": null,
  "imageCount": 2,
  "images": [
    {
      "id": 1,
      "damageId": 1,
      "sortOrder": 1,
      "originalFilename": "damage-1.jpg",
      "contentType": "image/jpeg",
      "sizeBytes": 123456,
      "createdAt": "2026-07-22T14:30:01"
    }
  ],
  "createdAt": "2026-07-22T14:30:01",
  "updatedAt": "2026-07-22T14:30:01"
}
```

`GET /api/damages/{damageId}`와 검토·보수 상태 전환 응답은 `assignedToName`, `repairerId`, `repairerName`, `repairRequestedAt`, `repairRequestNote`, `repairCompletedAt`, `repairCompletionNote`를 포함한다. 담당자가 없으면 해당 ID와 이름은 모두 `null`이다. `repairCompletedAt`은 `YYYY-MM-DD`, 요청 시각은 ISO-8601 일시 형식이다.

#### DamageImageResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 이미지 ID |
| `damageId` | number | 파손 ID |
| `sortOrder` | number | 이미지 정렬 순서. 1부터 시작 |
| `originalFilename` | string | 원본 파일명 |
| `contentType` | string | 이미지 MIME 타입 |
| `sizeBytes` | number | 파일 크기 |
| `createdAt` | string | 생성 일시 |

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 존재하지 않는 파손 ID |
| `401` | 인증 실패 |

### 5.6 도로 파손 이미지 조회

특정 파손에 연결된 이미지 바이너리를 조회한다.

| 항목 | 내용 |
| --- | --- |
| Method | `GET` |
| URL | `/api/damages/{damageId}/images/{imageId}/content` |
| 인증 | 필요 |

#### Path Parameter

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `damageId` | number | 파손 ID |
| `imageId` | number | 이미지 ID |

#### Response `200 OK`

- Body: 이미지 바이너리
- `Content-Type`: 저장된 이미지 MIME 타입
- `Content-Length`: 이미지 크기
- `Content-Disposition`: `inline; filename="{originalFilename}"`

#### Error

| 상태 코드 | 발생 상황 |
| --- | --- |
| `400` | 존재하지 않는 파손 ID 또는 이미지 ID |
| `401` | 인증 실패 |

## 6. 요구사항 기반 전체 API 구성안

요구사항 명세 기준으로 서버 API는 다음 도메인으로 구성한다. 실제 구현 여부는 1.1의 상태 컬럼과 각 도메인 상세 표를 기준으로 판단한다.

| 도메인 | 기본 경로 | 요구사항 |
| --- | --- | --- |
| 인증/권한 | `/api/auth`, `/api/users`, `/api/audit-logs` | FR-AUTH |
| 로봇 관제 | `/api/robots` | FR-ROBOT |
| 로봇 경로 | `/api/robot-routes` | FR-ROBOT |
| 파손 데이터 | `/api/damages` | FR-DAMAGE, FR-MAP, FR-DETAIL |
| AI 분석 | `/api/damages/{damageId}/analysis-jobs`, `/api/damage-ai-analysis-results` | FR-AI |
| 처리 상태 | `/api/damages/{damageId}/review` | FR-STATUS |
| 보수 요청/배정 | `/api/repair-assignments`, `/api/repair-assignments/{assignmentId}/request-histories` | FR-STATUS |
| 보수 결과 | `/api/repair-results` | FR-STATUS 후속 확장 |
| 통계 | `/api/statistics` | FR-STAT |
| 행정문서 | `/api/documents` | FR-DOC |

### 6.1 권한 매트릭스

| 기능 | ADMIN | INSPECTOR | REPAIRER | VIEWER | ROBOT/DEVICE |
| --- | --- | --- | --- | --- | --- |
| 로그인/토큰 재발급 | 예 | 예 | 예 | 예 | 별도 장치 인증 필요 |
| 사용자 관리 | 예 | 아니오 | 아니오 | 아니오 | 아니오 |
| 로봇 등록/수정/삭제 | 예 | 아니오 | 아니오 | 아니오 | 아니오 |
| 로봇 상태 로그 등록 | 예 | 예 | 아니오 | 아니오 | 추후 장치 인증 |
| 로봇 제어 명령 | 예 | 예 | 아니오 | 아니오 | 추후 장치 인증 |
| 로봇 관제 조회 | 예 | 예 | 아니오 | 조회 가능 | 아니오 |
| 경로 생성/전송 | 예 | 예 | 아니오 | 아니오 | 수신 |
| 파손 등록 | 예 | 예 | 아니오 | 아니오 | 예 |
| 파손 목록/상세 조회 | 예 | 예 | 예 | 조회 가능 | 아니오 |
| AI 분석 요청/수정/확정 | 예 | 예 | 아니오 | 아니오 | 아니오 |
| 처리 상태 변경 | 예 | 예 | 예 | 아니오 | 아니오 |
| 보수 배정 | 예 | 예 | 아니오 | 아니오 | 아니오 |
| 보수 결과 등록 | 예 | 아니오 | 예 | 아니오 | 아니오 |
| 통계 조회/다운로드 | 예 | 예 | 예 | 조회 가능 | 아니오 |
| 행정문서 생성/수정/다운로드 | 예 | 예 | 예 | 아니오 | 아니오 |

장치 인증은 현재 코드에 구현되어 있지 않다. 추후 로봇 또는 IoT 장치가 직접 API를 호출한다면 `X-Device-Token` 또는 장치용 JWT를 별도로 설계한다.

### 6.2 공통 검색 조건

파손 목록, 대시보드 요약, 지도 마커 API는 동일한 검색 조건을 공유한다. 기간 조건은 서버에 파손 데이터가 등록된 `createdAt`을 기준으로 한다. 지도 마커 API는 현재 화면 범위를 나타내는 `south`, `north`, `west`, `east`를 추가로 요구한다.

| Query | 타입 | 설명 |
| --- | --- | --- |
| `from` | string | 조회 시작 일시. ISO 8601 형식이며 해당 일시를 포함한다. |
| `to` | string | 조회 종료 일시. ISO 8601 형식이며 해당 일시를 포함하지 않는다. |
| `status` | string | 파손 처리 상태 |
| `robotId` | number | 로봇 ID |
| `assignedTo` | number | 처리 담당 사용자 ID. `damages.assigned_to`가 참조하는 `users.id` |
| `regionCode` | string | 시군구 코드. `damages.region_code`와 정확히 일치하는 파손만 조회 |

`page`, `size`, `keyword`는 목록 검색 API에서만 사용한다. `keyword`는 사건번호 또는 주소 키워드 검색에 사용한다. `severity`는 현재 데이터 모델에 없으므로 1차 대시보드 API의 검색 조건에서 제외한다.

## 7. 로봇 관제 API 설계

### 7.1 로봇 관리

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 로봇 등록 | `POST` | `/api/robots` | `ADMIN` | 로봇 기본 정보와 담당자를 등록한다. |
| 로봇 목록 조회 | `GET` | `/api/robots` | `ADMIN`, `INSPECTOR`, `VIEWER` | 로봇 목록과 현재 상태 요약을 조회한다. |
| 로봇 상세 조회 | `GET` | `/api/robots/{robotId}` | `ADMIN`, `INSPECTOR`, `VIEWER` | 로봇 기본 정보, 최근 위치, 배터리, 통신 상태를 조회한다. |
| 로봇 정보 수정 | `PATCH` | `/api/robots/{robotId}` | `ADMIN` | 이름, 담당자, 활성 여부를 수정한다. |
| 로봇 비활성화 | `PATCH` | `/api/robots/{robotId}/active` | `ADMIN` | 로봇 사용 여부를 변경한다. |

#### RobotResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 로봇 ID |
| `userId` | number | 담당 사용자 ID |
| `name` | string | 로봇 이름 |
| `serialNumber` | string | 장치 시리얼 번호 |
| `status` | string | `STANDBY`, `MOVING`, `INSPECTING`, `CHARGING`, `STOPPED`, `ERROR` |
| `active` | boolean | 활성 여부 |
| `latestStatus` | object | 최근 상태 로그 요약 |
| `createdAt` | string | 생성 일시 |
| `updatedAt` | string | 수정 일시 |

### 7.2 로봇 상태 로그

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 상태 로그 등록 | `POST` | `/api/robots/{robotId}/status-logs` | `ADMIN`, `INSPECTOR` | 로봇 위치, 배터리, 운행 상태, 통신 상태, 오류 정보를 등록한다. |
| 최근 상태 조회 | `GET` | `/api/robots/{robotId}/status-logs/latest` | `ADMIN`, `INSPECTOR`, `VIEWER` | 지도 표시용 최신 상태를 조회한다. |
| 상태 로그 목록 조회 | `GET` | `/api/robots/{robotId}/status-logs` | `ADMIN`, `INSPECTOR` | 최근 위치, 배터리 상태, 오류 이력을 조회한다. |

장치 인증은 아직 구현하지 않는다. 로봇 또는 IoT 장치가 직접 상태 로그를 전송하는 방식은 추후 `X-Device-Token` 또는 장치용 JWT 기반으로 별도 설계한다.

#### CreateRobotStatusLogRequest

```json
{
  "latitude": 37.5665,
  "longitude": 126.978,
  "batteryLevel": 72,
  "operationStatus": "INSPECTING",
  "connectionStatus": "CONNECTED",
  "errorCode": null,
  "errorMessage": null,
  "recordedAt": "2026-07-22T14:30:00"
}
```

#### RobotStatusLogResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 상태 로그 ID |
| `robotId` | number | 로봇 ID |
| `latitude` | number | 위도 |
| `longitude` | number | 경도 |
| `batteryLevel` | number | 배터리 잔량. 0~100 |
| `operationStatus` | string | `STANDBY`, `MOVING`, `INSPECTING`, `CHARGING`, `STOPPED`, `ERROR` |
| `connectionStatus` | string | `CONNECTED`, `DISCONNECTED` |
| `errorCode` | string, null | 오류 코드 |
| `errorMessage` | string, null | 오류 메시지 |
| `recordedAt` | string | 상태 기록 일시 |

### 7.3 로봇 제어 명령

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 제어 명령 생성 | `POST` | `/api/robots/{robotId}/commands` | `ADMIN`, `INSPECTOR` | 관제 서버가 로봇에 수행할 명령을 생성한다. |
| 제어 명령 이력 조회 | `GET` | `/api/robots/{robotId}/commands` | `ADMIN`, `INSPECTOR` | 로봇별 명령 생성 이력을 조회한다. |
| 미처리 명령 조회 | `GET` | `/api/robots/{robotId}/commands/pending` | `ADMIN`, `INSPECTOR` | 아직 처리되지 않은 명령을 오래된 순서로 조회한다. |
| 명령 상태 변경 | `PATCH` | `/api/robots/{robotId}/commands/{commandId}/status` | `ADMIN`, `INSPECTOR` | 명령 처리 상태와 결과 메시지를 갱신한다. |

#### CreateRobotCommandRequest

```json
{
  "commandType": "START_PATROL"
}
```

#### UpdateRobotCommandStatusRequest

```json
{
  "commandStatus": "SUCCEEDED",
  "resultMessage": "순찰을 시작했습니다."
}
```

#### RobotCommandResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 명령 ID |
| `robotId` | number | 명령 대상 로봇 ID |
| `requestedBy` | number | 명령 요청 사용자 ID |
| `commandType` | string | 명령 종류 |
| `commandStatus` | string | `PENDING`, `IN_PROGRESS`, `SUCCEEDED`, `FAILED`, `CANCELED` |
| `resultMessage` | string, null | 명령 처리 결과 메시지 |
| `requestedAt` | string | 명령 요청 일시 |
| `completedAt` | string, null | 명령 완료 일시. `SUCCEEDED`, `FAILED`, `CANCELED` 상태에서 기록 |

#### RobotCommandType

| 명령 | 설명 |
| --- | --- |
| `START_PATROL` | 순찰 시작 |
| `STOP_PATROL` | 순찰 종료 및 정지 |
| `EMERGENCY_STOP` | 즉시 긴급 정지 |
| `RETURN_HOME` | 스테이션 복귀 |
| `GET_STATUS` | 현재 상태 요청 |

#### RobotCommandStatus

| 상태 | 설명 |
| --- | --- |
| `PENDING` | 명령 생성 후 처리 대기 |
| `IN_PROGRESS` | 로봇이 명령 처리 중 |
| `SUCCEEDED` | 명령 처리 성공 |
| `FAILED` | 명령 처리 실패 |
| `CANCELED` | 명령 취소 |

허용 상태 전이는 `PENDING -> IN_PROGRESS`, `PENDING -> CANCELED`, `IN_PROGRESS -> SUCCEEDED`, `IN_PROGRESS -> FAILED`, `IN_PROGRESS -> CANCELED`이다.

### 7.4 로봇 MQTT 및 WebSocket 연동

MQTT 브로커 연결은 `MQTT_ENABLED`, `MQTT_BROKER_IP`, `MQTT_BROKER_PORT` 환경변수로 설정한다. 메시지 QoS는 `1`이며 명령 메시지는 retained 메시지로 저장하지 않는다.

| 방향 | MQTT 토픽 | 설명 |
| --- | --- | --- |
| 로봇 → 서버 | `roady/{robotId}/telemetry` | 위치, 배터리, 운행 및 연결 상태 수신 |
| 서버 → 로봇 | `roady/{robotId}/command` | DB에 저장된 제어 명령 발행 |
| 로봇 → 서버 | `roady/{robotId}/command/ack` | 명령 접수 및 처리 결과 수신 |

#### Telemetry Message

```json
{
  "latitude": 37.501,
  "longitude": 127.039,
  "batteryLevel": 82,
  "operationStatus": "MOVING",
  "connectionStatus": "CONNECTED",
  "errorCode": null,
  "errorMessage": null,
  "recordedAt": "2026-07-29T14:30:00"
}
```

서버는 토픽에서 양의 정수 `robotId`를 추출하고 Payload를 검증한다. 정상 메시지는 Redis의 `roady:robots:{robotId}:location`에 최신 값으로 저장한 뒤 다음 STOMP 토픽으로 발행한다.

| STOMP 토픽 | 설명 |
| --- | --- |
| `/topic/robots/location` | 모든 로봇의 실시간 위치 |
| `/topic/robots/{robotId}/location` | 특정 로봇의 실시간 위치 |

STOMP 연결 endpoint는 `/ws`다. 발행 데이터는 `robotId`, 좌표, 배터리, 운행 상태, 연결 상태, 오류 정보, `recordedAt`, `receivedAt`을 포함한다.

#### RobotCommandMessage

```json
{
  "commandId": 15,
  "commandType": "START_PATROL",
  "requestedAt": "2026-07-29T14:30:00"
}
```

명령은 DB 트랜잭션 커밋이 완료된 후 발행한다. `commandId`는 ACK와 DB 명령을 연결하는 식별자다.

#### RobotCommandAckMessage

```json
{
  "commandId": 15,
  "commandStatus": "IN_PROGRESS",
  "resultMessage": "Command accepted"
}
```

로봇이 보낼 수 있는 ACK 상태는 `IN_PROGRESS`, `SUCCEEDED`, `FAILED`다. 토픽의 `robotId`와 Payload의 `commandId`가 가리키는 DB 명령이 일치해야 한다. QoS 1 중복 전달로 현재 상태와 동일한 ACK가 다시 들어오면 추가 DB 갱신 없이 성공 처리한다.

## 8. 로봇 경로 API 설계

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 경로 생성 | `POST` | `/api/robot-routes` | `ADMIN`, `INSPECTOR` | 시작 지점, 도착 지점, 경유 지점을 기반으로 점검 경로를 생성한다. |
| 경로 목록 조회 | `GET` | `/api/robot-routes` | `ADMIN`, `INSPECTOR`, `VIEWER` | 로봇별 또는 상태별 경로를 조회한다. |
| 경로 상세 조회 | `GET` | `/api/robot-routes/{routeId}` | `ADMIN`, `INSPECTOR`, `VIEWER` | 경로와 경로점 목록을 조회한다. |
| 경로 수정 | `PUT` | `/api/robot-routes/{routeId}` | `ADMIN`, `INSPECTOR` | 경로명, 경로점, 상태를 수정한다. |
| 경로 삭제 | `DELETE` | `/api/robot-routes/{routeId}` | `ADMIN`, `INSPECTOR` | 전송 전 또는 미사용 경로를 삭제한다. |
| 경로 로봇 전송 | `POST` | `/api/robot-routes/{routeId}/dispatch` | `ADMIN`, `INSPECTOR` | 생성된 경로를 로봇에 전송한다. |
| 실제 이동 경로 조회 | `GET` | `/api/robot-routes/{routeId}/actual-path` | `ADMIN`, `INSPECTOR`, `VIEWER` | 상태 로그 기반 실제 이동 좌표를 조회한다. |

#### CreateRobotRouteRequest

```json
{
  "robotId": 1,
  "name": "서초구 보행로 1구역",
  "points": [
    {
      "pointOrder": 1,
      "latitude": 37.5665,
      "longitude": 126.978,
      "pointType": "START"
    },
    {
      "pointOrder": 2,
      "latitude": 37.5651,
      "longitude": 126.9792,
      "pointType": "DESTINATION"
    }
  ]
}
```

#### UpdateRobotRouteRequest

```json
{
  "name": "서초구 보행로 1구역 수정",
  "routeStatus": "CREATED",
  "points": [
    {
      "pointOrder": 1,
      "latitude": 37.5665,
      "longitude": 126.978,
      "pointType": "START"
    },
    {
      "pointOrder": 2,
      "latitude": 37.5658,
      "longitude": 126.9786,
      "pointType": "WAYPOINT"
    },
    {
      "pointOrder": 3,
      "latitude": 37.5651,
      "longitude": 126.9792,
      "pointType": "DESTINATION"
    }
  ]
}
```

#### RobotRouteResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 경로 ID |
| `robotId` | number | 경로 대상 로봇 ID |
| `createdBy` | number | 경로 생성 사용자 ID |
| `name` | string | 경로명 |
| `routeStatus` | string | `CREATED`, `DISPATCHED`, `COMPLETED`, `CANCELED` |
| `points` | array | 경로점 목록. 상세 조회/생성/수정 응답에 포함 |
| `createdAt` | string | 생성 일시 |
| `updatedAt` | string | 수정 일시 |

#### RobotRoutePoint

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 경로점 ID |
| `routeId` | number | 경로 ID |
| `pointOrder` | number | 경로점 순서. 경로 안에서 중복 불가 |
| `latitude` | number | 위도 |
| `longitude` | number | 경도 |
| `pointType` | string | `START`, `WAYPOINT`, `DESTINATION` |
| `createdAt` | string | 생성 일시 |

경로점은 최소 2개 이상이어야 하며, `START`와 `DESTINATION`은 각각 정확히 1개씩 포함되어야 한다. 경로 삭제는 `CREATED` 상태에서만 가능하다.

## 9. 파손 데이터 및 대시보드 API

대시보드 구성을 위한 목록 검색, 요약 집계, 지도 마커 조회 기능은 구현 완료되었다. 목록 검색은 사건번호·주소 키워드와 시군구 코드 필터를 지원한다. AI 심각도, 중복 및 지연 판정은 9.4의 후속 확장 범위로 구분한다.

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 파손 등록 | `POST` | `/api/damages` | `ADMIN`, `INSPECTOR`, `ROBOT/DEVICE` | 이미지, 위치, 촬영 일시, 장치 정보를 저장하고 AI 분석 작업을 자동 등록한다. |
| 파손 목록 검색 | `GET` | `/api/damages` | `ADMIN`, `INSPECTOR`, `REPAIRER`, `VIEWER` | 기간, 처리 상태, 로봇, 담당자, 시군구 코드, 사건번호·주소 키워드로 검색하고 페이지 단위로 조회한다. |
| 대시보드 파손 요약 | `GET` | `/api/dashboard/damages/summary` | `ADMIN`, `INSPECTOR`, `REPAIRER`, `VIEWER` | 검색 조건에 해당하는 전체 건수, 미배정 건수, 상태별 건수를 조회한다. |
| 지도 마커 조회 | `GET` | `/api/damages/map-markers` | `ADMIN`, `INSPECTOR`, `REPAIRER`, `VIEWER` | 지도 표시용 좌표와 상태 요약을 조회한다. |
| 파손 상세 조회 | `GET` | `/api/damages/{damageId}` | `ADMIN`, `INSPECTOR`, `REPAIRER`, `VIEWER` | 파손 기본 정보, 현재 상태, 관리자 처리 우선순위, 첨부 이미지 메타데이터를 조회한다. |
| 파손 이미지 조회 | `GET` | `/api/damages/{damageId}/images/{imageId}/content` | 로그인 사용자 | 이미지 바이너리를 조회한다. |

### 9.1 파손 목록 검색

#### 요청

```http
GET /api/damages?from=2026-07-01T00:00:00&to=2026-08-01T00:00:00&status=AI_ANALYZED&robotId=1&assignedTo=5&regionCode=41550&keyword=죽산&page=0&size=20
```

| Query | 필수 | 기본값 | 제약 |
| --- | --- | --- | --- |
| `from` | 아니오 | 없음 | `createdAt >= from` |
| `to` | 아니오 | 없음 | `createdAt < to`, `from`보다 커야 한다. |
| `status` | 아니오 | 없음 | 정의된 파손 처리 상태 중 하나 |
| `robotId` | 아니오 | 없음 | 로봇 ID |
| `assignedTo` | 아니오 | 없음 | 처리 담당 사용자 ID |
| `regionCode` | 아니오 | 없음 | 시군구 코드. `damages.region_code`와 정확히 일치 |
| `keyword` | 아니오 | 없음 | 사건번호 또는 주소 키워드. 숫자만 있으면 사건번호(`id`)와도 매칭 |
| `page` | 아니오 | `0` | 0 이상의 정수 |
| `size` | 아니오 | `20` | 1 이상 100 이하의 정수 |

결과는 `createdAt DESC, id DESC` 순서로 정렬한다.

#### DamageSearchResponse

```json
{
  "content": [
    {
      "id": 1,
      "robotId": 1,
      "assignedTo": 5,
      "description": "점자블록 균열",
      "addressName": "경기 안성시 죽산면 죽산리 343-1",
      "roadAddressName": "경기 안성시 죽산초교길 69-4",
      "regionCode": "41550",
      "region1DepthName": "경기",
      "region2DepthName": "안성시",
      "region3DepthName": "죽산면",
      "geocodedAt": "2026-07-22T14:30:01",
      "latitude": 37.5665,
      "longitude": 126.978,
      "capturedAt": "2026-07-22T14:30:00",
      "currentStatus": "AI_ANALYZED",
      "processingPriority": "URGENT",
      "reviewDamageType": "CRACK",
      "reviewNote": "현장 확인 필요",
      "imageCount": 2,
      "damageScore": 82,
      "damageType": "CRACK",
      "repairRequired": true,
      "repairPriority": "URGENT",
      "confidenceScore": 0.91,
      "createdAt": "2026-07-22T14:30:01"
    }
  ],
  "page": 0,
  "size": 20,
  "totalElements": 1,
  "totalPages": 1
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `content` | array | 현재 페이지의 파손 목록 |
| `content[].id` | number | 파손 ID |
| `content[].robotId` | number, null | 파손을 수집한 로봇 ID |
| `content[].assignedTo` | number, null | 처리 담당 사용자 ID. 미배정이면 `null` |
| `content[].description` | string, null | 파손 설명 |
| `content[].addressName` | string, null | 카카오 좌표 변환으로 얻은 지번 주소 |
| `content[].roadAddressName` | string, null | 카카오 좌표 변환으로 얻은 도로명 주소 |
| `content[].regionCode` | string, null | 카카오 행정구역 좌표 변환으로 얻은 시군구 코드 |
| `content[].region1DepthName` | string, null | 시도명 |
| `content[].region2DepthName` | string, null | 시군구명 |
| `content[].region3DepthName` | string, null | 읍면동명 |
| `content[].geocodedAt` | string, null | 주소/행정구역 변환 일시 |
| `content[].latitude` | number, null | 위도 |
| `content[].longitude` | number, null | 경도 |
| `content[].capturedAt` | string, null | 촬영 일시 |
| `content[].currentStatus` | string | 현재 파손 처리 상태 |
| `content[].processingPriority` | string, null | 관리자가 수정한 처리 우선순위. `LOW`, `NORMAL`, `HIGH`, `URGENT` |
| `content[].reviewDamageType` | string, null | 관리자가 판정한 파손 유형. `LARGE_MISSING`, `SMALL_MISSING`, `WEAR`, `CRACK`, `OTHER` |
| `content[].reviewNote` | string, null | 관리자 판정 비고. 공백은 `null`로 저장하며 최대 1,000자 |
| `content[].imageCount` | number | 등록된 이미지 수 |
| `content[].damageScore` | number, null | 최신 성공 AI 분석의 파손 점수 |
| `content[].damageType` | string, null | 최신 성공 AI 분석의 파손 유형. `LARGE_MISSING`, `SMALL_MISSING`, `WEAR`, `CRACK` |
| `content[].repairRequired` | boolean, null | 최신 성공 AI 분석의 보수 필요 여부 |
| `content[].repairPriority` | string, null | 최신 성공 AI 분석의 보수 우선순위 |
| `content[].confidenceScore` | number, null | 최신 성공 AI 분석의 신뢰도 |
| `content[].createdAt` | string | 서버 등록 일시 |
| `page` | number | 현재 페이지 번호. 0부터 시작 |
| `size` | number | 요청한 페이지 크기 |
| `totalElements` | number | 검색 조건에 해당하는 전체 데이터 수 |
| `totalPages` | number | 전체 페이지 수. 결과가 없으면 0 |

AI 분석 필드는 `analysisStatus`가 `SUCCESS`인 결과 중 `createdAt DESC, id DESC` 기준 최신 한 건을 반환한다. 성공한 분석 결과가 없으면 `damageScore`, `damageType`, `repairRequired`, `repairPriority`, `confidenceScore`는 모두 `null`이다.

`severity`, `duplicateSuspected`, `delayed`는 현재 목록 응답에 포함하지 않는다. `severity` 대신 AI 분석 결과에 저장된 `damageScore`를 파손 정도로 사용한다.

### 9.2 대시보드 파손 요약

목록 API와 같은 `from`, `to`, `status`, `robotId`, `assignedTo`, `regionCode` 조건을 사용한다. `page`, `size`, `keyword`는 받지 않는다.

#### 요청

```http
GET /api/dashboard/damages/summary?from=2026-07-01T00:00:00&to=2026-08-01T00:00:00&robotId=1&regionCode=41550
```

#### DamageDashboardSummaryResponse

```json
{
  "total": 123,
  "unassigned": 12,
  "statusCounts": {
    "COLLECTED": 20,
    "AI_ANALYZING": 12,
    "AI_ANALYZED": 23,
    "REQUESTED": 18,
    "REPAIR_IN_PROGRESS": 8,
    "REPAIR_COMPLETED": 27,
    "CANCELED": 5
  }
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `total` | number | 검색 조건에 해당하는 전체 파손 수 |
| `unassigned` | number | 검색 결과 중 `assignedTo`가 `null`인 파손 수 |
| `statusCounts` | object | 처리 상태별 파손 수. 데이터가 없는 상태도 값 `0`으로 포함한다. |

`status` 조건이 전달되면 `total`, `unassigned`, `statusCounts` 모두 해당 상태로 필터링된 결과를 반환한다.

### 9.3 지도 마커 조회

목록 API와 같은 `from`, `to`, `status`, `robotId`, `assignedTo`, `regionCode` 조건을 사용한다. `page`, `size`, `keyword`는 받지 않으며, 현재 지도 화면 범위를 나타내는 `south`, `north`, `west`, `east`는 필수다. 위도 또는 경도가 없거나 화면 범위 밖에 있는 파손은 결과에서 제외한다.

#### 요청

```http
GET /api/damages/map-markers?south=37.45&north=37.62&west=126.80&east=127.10&from=2026-07-01T00:00:00&to=2026-08-01T00:00:00&status=AI_ANALYZED&regionCode=41550
```

프론트엔드는 최초 지도 로딩 및 `moveend`, `zoomend` 시 현재 화면 경계를 전달한다. 지도 이동 중인 요청은 취소하고 약 300ms debounce를 적용한다.

#### DamageMapMarkerResponse

```json
[
  {
    "id": 1,
    "latitude": 37.5665,
    "longitude": 126.978,
    "currentStatus": "AI_ANALYZED"
  }
]
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 파손 ID |
| `latitude` | number | 위도 |
| `longitude` | number | 경도 |
| `currentStatus` | string | 현재 파손 처리 상태 |

### 9.4 후속 확장 범위

중복 후보, 검토 의견, 주소 및 행정구역 검색, AI 분석 기반 심각도 검색, 처리 지연 여부는 1차 대시보드 API 범위에서 제외한다. 각 기능에 필요한 데이터 모델과 판정 규칙을 먼저 정의한 뒤 별도 API로 추가한다.

## 10. AI 분석 API

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| AI 분석 작업 생성 | `POST` | `/api/damages/{damageId}/analysis-jobs` | `ADMIN`, `INSPECTOR` | 저장된 파손 이미지를 수동으로 재분석 큐에 등록한다. 최초 분석은 파손 등록 시 자동 생성된다. |
| 파손별 AI 분석 작업 목록 조회 | `GET` | `/api/damages/{damageId}/analysis-jobs` | 로그인 사용자 | 특정 파손의 AI 분석 작업과 결과 목록을 조회한다. |
| AI 분석 결과 단건 조회 | `GET` | `/api/damage-ai-analysis-results/{analysisResultId}` | 로그인 사용자 | AI 분석 결과 한 건을 조회한다. |
| AI 분석 요청 | `POST` | `/api/damages/{damageId}/ai-analysis` | `ADMIN`, `INSPECTOR` | 동기식 또는 대표 분석 요청 API. 후속 설계안 |
| 대표 AI 분석 결과 조회 | `GET` | `/api/damages/{damageId}/ai-analysis` | 로그인 사용자 | 최신 또는 확정 AI 분석 결과 조회. 후속 설계안 |
| AI 분석 재시도 | `POST` | `/api/damages/{damageId}/ai-analysis/retry` | `ADMIN`, `INSPECTOR` | 실패한 분석을 재시도한다. 후속 설계안 |
| AI 분석 결과 수정 | `PATCH` | `/api/damages/{damageId}/ai-analysis` | `ADMIN`, `INSPECTOR` | 담당자가 AI 분석 결과를 수정한다. 후속 설계안 |
| AI 분석 결과 확정 | `POST` | `/api/damages/{damageId}/ai-analysis/confirm` | `ADMIN`, `INSPECTOR` | 검토 완료 처리한다. 후속 설계안 |

#### AiAnalysisResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 분석 결과 ID |
| `damageId` | number | 파손 ID |
| `damaged` | boolean | 파손 여부 |
| `damageScore` | number | 파손 점수. 0~100 |
| `damageType` | string, null | 파손 유형. `LARGE_MISSING`, `SMALL_MISSING`, `WEAR`, `CRACK` |
| `repairRequired` | boolean, null | 보수 필요 여부 |
| `repairPriority` | string, null | `LOW`, `NORMAL`, `HIGH`, `URGENT` |
| `confidenceScore` | number, null | 분석 신뢰도. 0~1 |
| `analysisStatus` | string | `QUEUED`, `PROCESSING`, `SUCCESS`, `FAILED` |
| `rawResult` | string, null | AI 분석 원문 응답 |
| `analyzedAt` | string, null | 분석 일시 |
| `createdAt` | string | 분석 작업 생성 일시 |

### 10.1 비동기 이미지 분석 처리 흐름

이미지 분석 작업의 큐와 상태는 Spring이 관리한다. AI 서버는 Redis와 RDB에 직접 연결하지 않고, Spring 워커가 전달한 요청 한 건을 동기 방식으로 처리한다.

```text
POST /api/damages
  -> 파손 정보와 이미지 저장
  -> Spring이 damage_ai_analysis_results에 QUEUED 작업 생성
  -> 파손 상태를 AI_ANALYZING으로 전환
  -> Redis Queue 등록
  -> Spring Worker가 작업 소비 및 PROCESSING 전환
  -> AI Server POST /analyze 호출
  -> 성공 시 결과 컬럼과 raw_result 저장, SUCCESS 및 AI_ANALYZED 전환
  -> 실패 시 오류 원문을 raw_result에 저장, FAILED 및 COLLECTED 전환 후 Dead Letter Queue 등록
```

`POST /api/damages`가 성공하면 이미지 저장과 AI 분석 작업 등록이 모두 완료되며 응답의 `currentStatus`는 `AI_ANALYZING`이다. `POST /api/damages/{damageId}/analysis-jobs`는 운영자가 수동 재분석을 요청할 때 사용한다.

### 10.2 내부 AI 서버 이미지 분석 API

Spring 워커 전용 내부 API다. 프론트엔드와 로봇은 이 API를 직접 호출하지 않는다. Docker Compose 환경에서 Spring은 `http://ai:8000/analyze`를 사용한다.

| 항목 | 내용 |
| --- | --- |
| Method | `POST` |
| URL | `/analyze` |
| 호출 주체 | Spring AI 분석 워커 |
| Content-Type | `multipart/form-data` |
| 응답 Content-Type | `application/json` |

#### Form Data

| 필드 | 타입 | 필수 | 제약 | 설명 |
| --- | --- | --- | --- | --- |
| `damageId` | string | 예 | 양의 정수 형식 | Spring 파손 ID |
| `images` | file[] | 예 | 1~50개, 파일당 최대 20MB, 요청 전체 최대 200MB | 저장된 파손 이미지 목록 |
| `latitude` | string | 아니오 | 빈 문자열 허용 | 촬영 위도. v1 분석에는 사용하지 않음 |
| `longitude` | string | 아니오 | 빈 문자열 허용 | 촬영 경도. v1 분석에는 사용하지 않음 |
| `capturedAt` | string | 아니오 | 빈 문자열 허용 | 촬영 일시. v1 분석에는 사용하지 않음 |

```bash
curl -X POST "http://localhost:8000/analyze" \
  -F "damageId=1" \
  -F "latitude=37.5665000" \
  -F "longitude=126.9780000" \
  -F "capturedAt=2026-08-06T13:50:00" \
  -F "images=@damage-1.jpg" \
  -F "images=@damage-2.jpg"
```

#### Response `200 OK`

최상위 필드는 `damage_ai_analysis_results`의 구조화된 컬럼에 대응한다. `analysis_detail`은 판정 근거와 이미지별 결과이며, Spring은 응답 전체 JSON을 `raw_result`에 함께 보존한다.

```json
{
  "damaged": true,
  "damage_score": 45,
  "damage_type": null,
  "repair_required": true,
  "repair_priority": "NORMAL",
  "confidence_score": 0.8432,
  "analysis_detail": {
    "schema_version": "1.0",
    "model": {
      "name": "yolo26s-seg-server-v1",
      "weights": "yolo26s_seg_v1_best.pt",
      "weights_sha256": "97bf493309ebc45135b21b686235b5a421eeed6346596877498b2d9f9de0966f",
      "classes": {
        "0": "tactile_block",
        "1": "damage"
      }
    },
    "aggregation": {
      "image_count": 2,
      "selected_image_index": 1,
      "strategy": "max_damage_score"
    },
    "damage_ratio": 0.0859,
    "damage_ratio_percent": 8.59,
    "estimated_severity": "moderate",
    "estimated_severity_label": "보통 추정",
    "review_required": true,
    "review_reasons": [
      "damage_mask_quality_below_target"
    ],
    "advisory_only": true,
    "regions": {
      "tactile_block": {
        "confidence": 0.91,
        "pixels": 125000
      },
      "damage": {
        "confidence": 0.8432,
        "pixels": 10738
      }
    },
    "quality": {
      "positive_damage_dice": 0.083,
      "damage_f2": 0.8261,
      "ratio_mae_pp": 6.085,
      "severity_macro_f1": 0.2187
    },
    "images": [
      {
        "index": 0,
        "filename": "damage-1.jpg",
        "damaged": false,
        "damage_score": 0,
        "damage_ratio": 0.0,
        "damage_ratio_percent": 0.0,
        "estimated_severity": "normal",
        "confidence_score": null,
        "review_required": true
      },
      {
        "index": 1,
        "filename": "damage-2.jpg",
        "damaged": true,
        "damage_score": 45,
        "damage_ratio": 0.0859,
        "damage_ratio_percent": 8.59,
        "estimated_severity": "moderate",
        "confidence_score": 0.8432,
        "review_required": true
      }
    ],
    "inference_ms": 72.4
  }
}
```

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `damaged` | boolean | `damage_score > 0` 여부 |
| `damage_score` | number | 파손 비율을 0~100으로 변환한 점수 |
| `damage_type` | null | 현재 모델은 파손 유형을 분류하지 않으므로 항상 `null` |
| `repair_required` | boolean | 심각도 `moderate`, `severe`이면 `true` |
| `repair_priority` | string, null | `LOW`, `NORMAL`, `HIGH`. 정상은 `null`이며 v1은 `URGENT`를 자동 결정하지 않음 |
| `confidence_score` | number, null | 대표 이미지의 파손 마스크 confidence. 파손이 없으면 `null` |
| `analysis_detail` | object | 모델, 집계, 영역, 품질, 검토 사유, 이미지별 분석 결과 |

여러 이미지가 전달되면 `damage_score`, 파손 비율, confidence 순으로 가장 큰 이미지를 대표 결과로 선택한다.

#### 파손 점수 및 보수 정책

| 파손 비율 | `damage_score` | 심각도 | `repair_required` | `repair_priority` |
| --- | ---: | --- | --- | --- |
| 0.5% 미만 | 0 | `normal` | `false` | `null` |
| 0.5% 이상 5% 미만 | 1~30 선형 변환 | `minor` | `false` | `LOW` |
| 5% 이상 15% 미만 | 31~70 선형 변환 | `moderate` | `true` | `NORMAL` |
| 15% 이상 | 71~100 선형 변환 | `severe` | `true` | `HIGH` |

#### Error

| 상태 코드 | 발생 상황 | Spring 처리 |
| --- | --- | --- |
| `413` | 개별 이미지 또는 전체 요청 용량 초과 | 분석 결과 `FAILED`, 오류 원문 저장, Dead Letter Queue 등록 |
| `415` | 빈 파일 또는 디코딩할 수 없는 이미지 | 분석 결과 `FAILED`, 오류 원문 저장, Dead Letter Queue 등록 |
| `422` | 잘못된 `damageId`, 이미지 개수 오류, 점자블록 미검출 등 분석 입력 오류 | 분석 결과 `FAILED`, 오류 원문 저장, Dead Letter Queue 등록 |
| `500` | 모델 추론 중 내부 오류 | 분석 결과 `FAILED`, 오류 원문 저장, Dead Letter Queue 등록 |
| `503` | 모델 로딩이 완료되지 않은 상태에서 readiness 또는 모델 정보 요청 | Compose health check 실패 및 Spring 시작 대기 |

### 10.3 내부 AI 서버 상태 API

| Method | URL | 정상 응답 | 설명 |
| --- | --- | --- | --- |
| `GET` | `/health/live` | `200 {"status":"ok"}` | FastAPI 프로세스 생존 확인 |
| `GET` | `/health/ready` | `200 {"status":"ready"}` | 모델 검증, 로딩, 워밍업 완료 확인 |
| `GET` | `/model-info` | `200` | 모델명, 가중치, SHA-256, 클래스, device, imgsz 확인 |

## 11. 처리 상태 및 보수 API 설계

### 11.1 처리 상태

| 상태 | 설명 |
| --- | --- |
| `COLLECTED` | 수집 완료 |
| `AI_ANALYZING` | AI 분석중 |
| `AI_ANALYZED` | AI 분석완료 |
| `REQUESTED` | 검토 완료(요청 전) |
| `REPAIR_IN_PROGRESS` | 보수 중 |
| `REPAIR_COMPLETED` | 보수 완료 |
| `CANCELED` | 취소 |

권장 상태 전이는 다음과 같다.

```text
COLLECTED -> AI_ANALYZING -> AI_ANALYZED -> REQUESTED -> REPAIR_IN_PROGRESS -> REPAIR_COMPLETED
COLLECTED -> CANCELED
AI_ANALYZING -> CANCELED
AI_ANALYZED -> CANCELED
REQUESTED -> CANCELED
REPAIR_IN_PROGRESS -> REQUESTED
```

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 관리자 검토 수정 | `PATCH` | `/api/damages/{damageId}/review` | `ADMIN`, `INSPECTOR` | 검토 단계에서 처리 상태, 관리자 처리 우선순위, 판정 파손 유형, 비고를 수정한다. 변경 이력은 저장하지 않는다. |

#### UpdateDamageReviewRequest

```json
{
  "status": "REQUESTED",
  "processingPriority": "HIGH",
  "reviewDamageType": "LARGE_MISSING",
  "reviewNote": "현장 확인 필요"
}
```

`status`는 필수이며 검토 단계에서 사용하는 `AI_ANALYZED`, `REQUESTED`, `CANCELED`만 허용한다. `REQUESTED`로 판정할 때는 `processingPriority`와 `reviewDamageType`이 필수다. `processingPriority`는 `LOW`, `NORMAL`, `HIGH`, `URGENT`만 허용한다. `reviewDamageType`은 `LARGE_MISSING`, `SMALL_MISSING`, `WEAR`, `CRACK`, `OTHER`만 허용한다. `reviewNote`는 선택 입력이고 공백 문자열은 `null`로 저장하며 최대 1,000자까지 허용한다.

판정을 되돌릴 때는 `status`를 `AI_ANALYZED`로 전달한다. 이때 `processingPriority`, `reviewDamageType`, `reviewNote`는 모두 `null`로 초기화한다. 보수 불필요 또는 오탐 판정은 `status`를 `CANCELED`로 변경하며, 이때도 관리자 판정 필드는 모두 `null`로 초기화한다.

#### UpdateDamageReviewResponse

성공 응답은 최신 상세 조회 응답과 같은 형태이며, 아래 필드를 반드시 포함한다.

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `currentStatus` | string | 변경된 현재 처리 상태 |
| `processingPriority` | string, null | 관리자 처리 우선순위 |
| `reviewDamageType` | string, null | 관리자 판정 파손 유형 |
| `reviewNote` | string, null | 관리자 판정 비고 |

### 11.2 보수 요청 및 배정

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 보수 진행 전환 | `POST` | `/api/damages/{damageId}/repair-request` | `ADMIN`, `INSPECTOR` | 검토 완료(`REQUESTED`) 파손을 보수 진행 중(`REPAIR_IN_PROGRESS`)으로 변경하고 우선순위, 파손 유형, 보수 담당자와 요청 메모를 저장한다. |
| 보수 요청서 수정 | `PATCH` | `/api/damages/{damageId}/repair-request` | `ADMIN`, `INSPECTOR` | 보수 진행 중 상태를 유지하면서 요청서 필드를 수정하고 수정 이력을 저장한다. |
| 보수 완료 처리 | `PATCH` | `/api/damages/{damageId}/repair-complete` | `ADMIN`, `INSPECTOR` | 보수 진행 중(`REPAIR_IN_PROGRESS`) 파손을 보수 완료(`REPAIR_COMPLETED`)로 변경하고 완료 일자와 메모를 저장한다. |
| 보수 요청 취소 | `PATCH` | `/api/damages/{damageId}/repair-cancel` | `ADMIN`, `INSPECTOR` | 보수 진행 중(`REPAIR_IN_PROGRESS`) 파손을 검토 완료(`REQUESTED`)로 되돌리고 취소 이력을 저장해 재요청 가능하게 한다. |
| 보수 요청/배정 등록 | `POST` | `/api/repair-assignments` | `ADMIN`, `INSPECTOR` | 파손 건에 보수 담당자를 배정하고 상태를 `REPAIR_IN_PROGRESS`로 변경하며 보수 요청 이력을 저장한다. |
| 보수 배정 목록 조회 | `GET` | `/api/repair-assignments` | `ADMIN`, `INSPECTOR`, `REPAIRER` | 담당자, 기간, 상태 기준으로 배정 목록을 조회한다. |
| 보수 배정 상세 조회 | `GET` | `/api/repair-assignments/{assignmentId}` | `ADMIN`, `INSPECTOR`, `REPAIRER` | 배정 상세 정보를 조회한다. |
| 보수 배정 수정 | `PATCH` | `/api/repair-assignments/{assignmentId}` | `ADMIN`, `INSPECTOR` | 담당자, 예정일, 메모를 수정한다. |
| 보수 작업 시작 | `PATCH` | `/api/repair-assignments/{assignmentId}/start` | `ADMIN`, `REPAIRER` | 배정된 보수 건의 파손 상태를 `REPAIR_IN_PROGRESS`로 변경한다. |
| 보수 요청 취소 | `PATCH` | `/api/repair-assignments/{assignmentId}/cancel` | `ADMIN`, `INSPECTOR` | 보수 요청 또는 예정 건의 파손 상태를 `CANCELED`로 변경하고 취소 이력을 저장한다. |
| 보수 요청 이력 조회 | `GET` | `/api/repair-assignments/{assignmentId}/request-histories` | `ADMIN`, `INSPECTOR`, `REPAIRER` | 보수 요청/배정/취소 시 저장된 이력을 조회한다. |

보수 요청/배정은 `damages.current_status`가 `REQUESTED`인 파손에 대해 수행한다. 등록 시 `repair_assignments`에 담당자와 예정일을 저장하고, `damages.assigned_to`와 `damages.current_status`를 함께 갱신한다. 관리자 검토 이력은 저장하지 않지만, 보수 요청/배정 이력은 `repair_request_histories`에 저장한다.

#### CreateDamageRepairRequest

검토 완료 파손을 보수 진행 상태로 전환하면서 보수 요청 정보를 저장한다.

```json
{
  "processingPriority": "HIGH",
  "reviewDamageType": "CRACK",
  "repairerId": 9,
  "note": "현장 교체 요청"
}
```

`processingPriority`는 `LOW`, `NORMAL`, `HIGH`, `URGENT`, `reviewDamageType`은 `LARGE_MISSING`, `SMALL_MISSING`, `WEAR`, `CRACK`, `OTHER`만 허용한다. 생략하면 기존 검토 값을 유지한다. `repairerId`는 `REPAIRER` 역할 사용자만 허용하며 미지정 시 `null`이다. `note`는 선택 입력이고 공백 문자열은 `null`로 저장하며 최대 1,000자까지 허용한다. 상태 변경과 `repair_request_histories` 이력 저장은 하나의 트랜잭션으로 실행한다.

#### UpdateDamageRepairRequest

`PATCH /api/damages/{damageId}/repair-request`는 `REPAIR_IN_PROGRESS` 상태에서 `processingPriority`, `reviewDamageType`, `repairerId`, `note`를 수정한다. 요청 본문은 `CreateDamageRepairRequest`와 같고 상태는 유지된다. 수정 이력은 변경 전·후 상태를 모두 `REPAIR_IN_PROGRESS`로 기록한다.

#### CompleteDamageRepairRequest

```json
{
  "completedAt": "2026-08-04",
  "note": "파손 블록 교체 완료"
}
```

`completedAt`은 필수이며 미래 날짜를 허용하지 않는다. 서버 처리 시각인 `updatedAt`과 별도로 `damages.repair_completed_at`에 저장하고, `note`는 `damages.repair_completion_note`와 이력에 함께 저장한다.

#### CancelDamageRepairRequest

```json
{
  "note": "담당자 재배정 필요"
}
```

취소하면 현재 보수 담당자와 완료 정보를 초기화하지만, `repair_request_histories`의 취소 이력은 유지한다. 이후 동일 파손에 다시 보수 요청할 수 있다.

성공 응답은 최신 `DamageSummaryResponse`이며 다음 보수 관리 필드를 포함한다.

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `assignedToName` | string, null | 일반 처리 담당자 이름 |
| `repairerId` | number, null | 보수 담당자 ID |
| `repairerName` | string, null | 보수 담당자 이름 |
| `repairRequestedAt` | string, null | 최근 보수 요청 시각 |
| `repairRequestNote` | string, null | 최근 보수 요청 또는 수정 메모 |
| `repairCompletedAt` | string, null | 보수 완료 일자. `YYYY-MM-DD` |
| `repairCompletionNote` | string, null | 보수 완료 메모 |

상태 전환 규칙은 다음과 같다.

```text
POST /api/damages/{damageId}/repair-request: REQUESTED -> REPAIR_IN_PROGRESS
PATCH /api/damages/{damageId}/repair-request: REPAIR_IN_PROGRESS -> REPAIR_IN_PROGRESS
PATCH /api/damages/{damageId}/repair-complete: REPAIR_IN_PROGRESS -> REPAIR_COMPLETED
PATCH /api/damages/{damageId}/repair-cancel: REPAIR_IN_PROGRESS -> REQUESTED
```

#### CreateRepairAssignmentRequest

```json
{
  "damageId": 1,
  "repairerId": 5,
  "scheduledDate": "2026-07-30",
  "note": "보행량이 적은 오전 시간대 작업 권장"
}
```

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `damageId` | number | 예 | `REQUESTED` 상태인 파손 ID |
| `repairerId` | number | 예 | 배정할 보수 담당자 ID |
| `scheduledDate` | string | 아니오 | 보수 예정일. `YYYY-MM-DD` |
| `note` | string | 아니오 | 보수 요청 또는 배정 메모 |

처리 규칙은 다음과 같다.

```text
damages.current_status: REQUESTED -> REPAIR_IN_PROGRESS
damages.assigned_to: repairerId로 갱신
repair_assignments: 보수 배정 정보 저장
repair_request_histories: beforeStatus, afterStatus, requestedBy, repairerId, note 저장
```

처리 결과는 `RepairAssignmentResponse`를 반환한다.

```json
{
  "id": 10,
  "damageId": 1,
  "repairerId": 5,
  "assignedBy": 2,
  "scheduledDate": "2026-07-30",
  "note": "보행량이 적은 오전 시간대 작업 권장",
  "damageStatus": "REPAIR_IN_PROGRESS",
  "createdAt": "2026-07-29T10:00:00",
  "updatedAt": "2026-07-29T10:00:00"
}
```

#### RepairRequestHistoryResponse

```json
[
  {
    "id": 1,
    "damageId": 1,
    "repairAssignmentId": 10,
    "requestedBy": 2,
    "repairerId": 5,
    "beforeStatus": "REQUESTED",
    "afterStatus": "REPAIR_IN_PROGRESS",
    "note": "보행량이 적은 오전 시간대 작업 권장",
    "requestedAt": "2026-07-29T10:00:00"
  }
]
```

#### UpdateRepairAssignmentRequest

```json
{
  "repairerId": 6,
  "scheduledDate": "2026-07-31",
  "note": "담당자 일정 변경"
}
```

`repairerId`, `scheduledDate`, `note`는 필요한 필드만 전달할 수 있다. 담당자가 변경되면 `damages.assigned_to`도 함께 갱신한다.

#### StartRepairAssignmentRequest

보수 작업 시작 API는 별도 Body 없이 호출한다. 성공 시 `damages.current_status`를 `REPAIR_IN_PROGRESS`로 변경하고 `RepairAssignmentResponse`를 반환한다.

#### CancelRepairAssignmentRequest

```json
{
  "reason": "현장 확인 결과 보수 불필요"
}
```

취소는 `REQUESTED` 또는 `REPAIR_IN_PROGRESS` 상태에서 허용한다. 성공 시 `damages.current_status`를 `CANCELED`로 변경하고, `repair_request_histories.note`에 취소 사유를 저장한다.

### 11.3 보수 결과 후속 확장

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 보수 결과 등록 | `POST` | `/api/repair-results` | `ADMIN`, `REPAIRER` | 보수 완료 이미지와 결과 내용을 등록한다. |
| 보수 결과 조회 | `GET` | `/api/repair-results/{resultId}` | 로그인 사용자 | 보수 결과 상세를 조회한다. |
| 파손별 보수 결과 조회 | `GET` | `/api/damages/{damageId}/repair-result` | 로그인 사용자 | 특정 파손의 보수 결과를 조회한다. |

#### CreateRepairResultRequest

`multipart/form-data`를 사용한다.

| 필드 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `damageId` | number | 예 | 파손 ID |
| `resultContent` | string | 예 | 보수 결과 내용 |
| `completedAt` | string | 예 | 완료 일시 |
| `images` | file[] | 아니오 | 보수 완료 이미지 |

## 12. 통계 API 설계

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 기간별 통계 | `GET` | `/api/statistics/damages/time-series` | 로그인 사용자 | 일별, 주별, 월별, 연도별 파손 발생 건수를 조회한다. |
| 처리 상태별 통계 | `GET` | `/api/statistics/damages/by-status` | 로그인 사용자 | 처리 상태별 건수를 조회한다. |
| 보수 우선순위별 통계 | `GET` | `/api/statistics/damages/by-repair-priority` | 로그인 사용자 | 최신 성공 AI 분석 결과의 보수 우선순위별 건수를 조회한다. |
| 보수 완료율 조회 | `GET` | `/api/statistics/repair/completion-rate` | 로그인 사용자 | 전체 파손 대비 보수 완료율을 조회한다. |

파손 데이터에는 시군구 코드를 저장하지만, 지역별 통계 API는 아직 제공하지 않는다. 별도 `severity` 대신 AI 분석 결과의 `repairPriority`를 사용한다. 통계 다운로드는 조회 API 구현 이후 별도 작업으로 확장한다.

### 12.1 공통 조회 조건

| Query | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| `from` | string | 예 | 조회 시작 일시. ISO 8601 형식이며 해당 일시를 포함한다. |
| `to` | string | 예 | 조회 종료 일시. ISO 8601 형식이며 해당 일시를 포함하지 않는다. `from`보다 커야 한다. |

집계 대상은 `from <= createdAt < to`를 만족하는 파손이다.

### 12.2 기간별 통계

`unit`은 필수이며 `DAY`, `WEEK`, `MONTH`, `YEAR` 중 하나다. `WEEK`는 월요일을 시작일로 사용한다. 조회 범위 내 데이터가 없는 기간도 건수 `0`, 완료율 `0.00`으로 반환한다.

#### 요청

```http
GET /api/statistics/damages/time-series?from=2026-07-01T00:00:00&to=2026-08-01T00:00:00&unit=DAY
```

#### TimeSeriesStatisticsResponse

```json
{
  "unit": "DAY",
  "items": [
    {
      "period": "2026-07-01",
      "totalCount": 3,
      "repairCompletedCount": 1,
      "repairCompletionRate": 33.33
    }
  ]
}
```

`repairCompletedCount`는 현재 상태가 `REPAIR_COMPLETED`인 파손 수다. `repairCompletionRate`는 같은 기간의 `repairCompletedCount / totalCount * 100`이며 소수점 둘째 자리까지 반환한다.

### 12.3 처리 상태별 통계

#### 요청

```http
GET /api/statistics/damages/by-status?from=2026-07-01T00:00:00&to=2026-08-01T00:00:00
```

#### DamageStatusStatisticsResponse

```json
{
  "totalCount": 38,
  "counts": {
    "COLLECTED": 5,
    "AI_ANALYZING": 4,
    "AI_ANALYZED": 4,
    "REQUESTED": 4,
    "REPAIR_IN_PROGRESS": 2,
    "REPAIR_COMPLETED": 12,
    "CANCELED": 4
  }
}
```

정의된 모든 처리 상태를 포함하며 데이터가 없는 상태의 값은 `0`이다.

### 12.4 보수 우선순위별 통계

#### 요청

```http
GET /api/statistics/damages/by-repair-priority?from=2026-07-01T00:00:00&to=2026-08-01T00:00:00
```

#### RepairPriorityStatisticsResponse

```json
{
  "totalCount": 38,
  "classifiedCount": 30,
  "unclassifiedCount": 8,
  "counts": {
    "LOW": 5,
    "NORMAL": 12,
    "HIGH": 8,
    "URGENT": 5
  }
}
```

각 파손에 연결된 `SUCCESS` 분석 결과 중 `createdAt DESC, id DESC` 기준 최신 한 건을 사용한다. 성공한 분석 결과가 없거나 우선순위 값이 정의되지 않은 파손은 `unclassifiedCount`에 포함한다. 대시보드 긴급/고위험 건수는 `counts.URGENT`를 사용한다.

### 12.5 보수 완료율

#### 요청

```http
GET /api/statistics/repair/completion-rate?from=2026-07-01T00:00:00&to=2026-08-01T00:00:00
```

#### RepairCompletionRateResponse

```json
{
  "totalCount": 38,
  "completedCount": 12,
  "canceledCount": 4,
  "completionRate": 31.58
}
```

`completedCount`는 현재 상태가 `REPAIR_COMPLETED`, `canceledCount`는 `CANCELED`인 파손 수다. `completionRate`는 `completedCount / totalCount * 100`이며 소수점 둘째 자리까지 반환한다. 보수 결과 도메인이 구현되면 완료 시점 기반 통계로 확장한다.

## 13. 행정문서 API 설계

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 문서 초안 생성 | `POST` | `/api/documents` | `ADMIN`, `INSPECTOR`, `REPAIRER` | 선택한 파손 데이터로 문서 초안을 생성한다. |
| 문서 목록 조회 | `GET` | `/api/documents` | `ADMIN`, `INSPECTOR`, `REPAIRER` | 이전에 생성한 문서 목록을 조회한다. |
| 문서 상세 조회 | `GET` | `/api/documents/{documentId}` | `ADMIN`, `INSPECTOR`, `REPAIRER` | 문서 내용과 연결 파손 데이터를 조회한다. |
| 문서 초안 수정 | `PATCH` | `/api/documents/{documentId}` | `ADMIN`, `INSPECTOR`, `REPAIRER` | 생성된 초안 내용을 수정한다. |
| 문서 다운로드 | `GET` | `/api/documents/{documentId}/download` | `ADMIN`, `INSPECTOR`, `REPAIRER` | PDF 또는 HWP 형식으로 다운로드한다. |

#### CreateDocumentRequest

```json
{
  "documentType": "REPAIR_REQUEST",
  "damageIds": [1, 2, 3],
  "title": "서초구 점자블록 보수 요청서",
  "departmentName": "도로관리과",
  "managerName": "홍길동"
}
```

#### DocumentResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 문서 ID |
| `documentType` | string | `INSPECTION_REPORT`, `REPAIR_REQUEST`, `REPAIR_COMPLETION_REPORT` |
| `title` | string | 문서 제목 |
| `content` | string | 초안 내용 |
| `draft` | boolean | 검토 필요 초안 여부 |
| `createdBy` | number | 생성자 ID |
| `createdAt` | string | 생성 일시 |
| `updatedAt` | string | 수정 일시 |

## 14. 감사 로그 API 설계

FR-AUTH-19, FR-AUTH-20 요구사항을 위해 주요 작업 이력을 별도 API로 조회할 수 있게 한다.

| 기능 | Method | URL | 권한 | 설명 |
| --- | --- | --- | --- | --- |
| 감사 로그 조회 | `GET` | `/api/audit-logs` | `ADMIN` | 로그인, 로그아웃, 사용자 관리, 상태 변경, 문서 생성 등 주요 작업 기록을 조회한다. |

#### AuditLogResponse

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| `id` | number | 로그 ID |
| `actorId` | number | 수행 사용자 ID |
| `action` | string | 작업 유형 |
| `targetType` | string | 대상 도메인 |
| `targetId` | number | 대상 ID |
| `success` | boolean | 성공 여부 |
| `message` | string | 상세 메시지 |
| `createdAt` | string | 기록 일시 |

## 15. 구현 우선순위

요구사항의 필수 항목과 현재 구현 상태를 기준으로 다음 순서로 구현하는 것을 권장한다.

| 순서 | 범위 | 이유 |
| --- | --- | --- |
| 1 | 인증/사용자 관리 보완 | 모든 API의 권한 기반이 된다. |
| 2 | 파손 데이터 검색/상세 확장 | 현재 구현된 핵심 도메인이며 지도/AI/상태 관리의 기준 데이터다. |
| 3 | 로봇 상태 로그와 지도 마커 | 로봇 관제와 지도 표시 요구사항의 최소 기능이다. |
| 4 | AI 분석 결과 저장/수정/확정 | 파손 정도, 보수 필요성, 우선순위 판단에 필요하다. |
| 5 | 보수 관리 확장 | 파손 접수 이후 보수 배정, 완료 보고서, 첨부 이미지까지 업무 흐름을 확장한다. |
| 6 | 통계와 문서 생성 | 누적 데이터 기반의 관리 기능이다. |
| 7 | 감사 로그 | 운영 추적성과 보안 요구사항을 보완한다. |
