# Roady 외부 서비스 정보

Roady가 서비스 기능을 제공하기 위해 연동하는 외부 서비스는 Kakao Local API와 OpenStreetMap이다. 비밀 키는 문서나 Git 저장소에 기록하지 않고 환경 변수로 주입한다.

## 1. 외부 서비스 사용 현황

| 서비스 | 사용 목적 | 가입 및 키 | 설정 위치 |
| --- | --- | --- | --- |
| Kakao Local API | 파손 좌표를 주소와 행정구역 정보로 변환 | Kakao Developers 가입 및 REST API 키 필요 | `Roady_BE/.env` |
| OpenStreetMap | Leaflet 지도 화면에 지도 타일 제공 | 가입 및 API 키 불필요 | `Roady_FE/src/components/common/CommonMap.vue` |

## 2. Kakao Local API

### 2.1 사용 목적

파손 신고에 포함된 위도와 경도를 주소명, 도로명 주소 및 행정구역 코드로 변환한다.

사용 endpoint:

- `https://dapi.kakao.com/v2/local/geo/coord2address.json`
- `https://dapi.kakao.com/v2/local/geo/coord2regioncode.json`

### 2.2 가입 및 설정

1. `https://developers.kakao.com`에 가입하고 애플리케이션을 생성한다.
2. 애플리케이션 키에서 REST API 키를 확인한다.
3. `Roady_BE/.env`에 다음 환경 변수를 설정한다.

```dotenv
ROADY_KAKAO_GEOCODING_ENABLED=true
ROADY_KAKAO_REST_API_KEY=<Kakao REST API 키>
```

선택 설정:

```dotenv
ROADY_KAKAO_COORD2_ADDRESS_URL=https://dapi.kakao.com/v2/local/geo/coord2address.json
ROADY_KAKAO_COORD2_REGION_CODE_URL=https://dapi.kakao.com/v2/local/geo/coord2regioncode.json
ROADY_KAKAO_GEOCODING_REQUEST_TIMEOUT=3s
```

REST API 키는 `Authorization: KakaoAK <REST_API_KEY>` 헤더로 전달된다. 키가 없거나 `ROADY_KAKAO_GEOCODING_ENABLED=false`이면 역지오코딩만 수행하지 않으며 파손 등록과 AI 분석 기능은 정상 동작한다.

## 3. OpenStreetMap

프론트엔드는 Leaflet을 통해 다음 OpenStreetMap 타일을 사용한다.

```text
https://tile.openstreetmap.org/{z}/{x}/{y}.png
```

- 별도의 회원가입이나 API 키가 필요하지 않다.
- 지도 화면에 `OpenStreetMap contributors` 저작자 표시를 유지한다.
- 서비스 운영 시 OpenStreetMap 타일 사용 정책과 요청량 제한을 준수한다.
