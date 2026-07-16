# GitLab 커밋 메시지 규칙

## 1. 기본 형식

```text
type(scope): 작업 내용
```

- `type`: 어떤 종류의 작업인지 표시한다.
- `scope`: 작업한 영역을 표시한다.
- `작업 내용`: 실제로 변경한 내용을 작성한다.

## 2. Type 종류

| Type | 사용 상황 |
|---|---|
| `feat` | 새로운 기능 추가 |
| `fix` | 오류 또는 버그 수정 |
| `refactor` | 기능 변화 없이 코드 구조 개선 |
| `docs` | README, 기획서 등 문서 수정 |
| `test` | 테스트 코드 작성 및 수정 |
| `style` | 들여쓰기, 공백, 주석 등 코드 형식 수정 |
| `chore` | 설정, 패키지, 폴더 구조 등 기타 작업 |
| `perf` | 성능 개선 |
| `merge` | 브랜치 병합 |

## 3. Scope 예시

```text
ai
hardware
embedded
server
frontend
database
docs
common
```

프로젝트 상황에 맞게 필요한 항목만 사용한다.

## 4. 작성 예시

```text
feat(ai): 점자블록 파손 탐지 모델 추가
feat(hardware): 카메라 촬영 기능 구현
fix(embedded): 센서 데이터 수신 오류 수정
fix(server): 이미지 업로드 실패 문제 수정
refactor(ai): 이미지 전처리 코드 분리
docs(plan): 프로젝트 기획서 내용 수정
docs(readme): 실행 방법 추가
chore(common): 프로젝트 폴더 구조 정리
```

## 5. 작성 규칙

- 작성자 이름은 커밋 메시지에 넣지 않는다.
- 한 커밋에는 하나의 작업만 포함한다.
- `수정`, `업데이트`처럼 모호한 표현만 사용하지 않는다.
- 무엇을 변경했는지 구체적으로 작성한다.
- 메시지 마지막에는 마침표를 붙이지 않는다.
- 커밋 메시지는 한국어로 통일한다.

### 잘못된 예시

```text
강하린_코드수정
경연_업데이트
feat: 수정
작업 완료
최종 수정
진짜 최종 수정
```

### 올바른 예시

```text
feat(ai): 점자블록 객체 탐지 기능 추가
fix(server): 탐지 결과 저장 오류 수정
docs(readme): Jetson 실행 방법 추가
```

## 6. 평가 자료 업로드 시 커밋 메시지

평가용 주간 진행사항과 학습 기록은 아래 형식으로 업로드한다.

```text
chore: upload weekly progress and learning logs (번호)
```

번호는 평가 자료 업로드 순서에 맞게 작성한다.

