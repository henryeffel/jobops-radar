# Linux 운영과 관계형 DB 기본기 개발 계획

기준일: 2026-07-21

## 목적

이 작업의 목표는 JobOps에 억지로 새로운 제품 기능을 추가하는 것이 아닙니다. 현재 로컬 PC에서 실행되는 서비스를 Linux 환경에서 상태를 확인하고 복구할 수 있는 서비스로 발전시키고, 기존 공고 저장 기능을 통해 관계형 DB 설계·조회·인덱스·트랜잭션 기본기를 검증하는 것입니다.

```text
현재
내 PC에서 Python 명령으로 실행되는 서비스

목표
Linux 서버에서 자동으로 실행되고,
DB나 외부 API에 문제가 생겨도 상태를 구분하고 복구할 수 있는 서비스
```

이 개발은 다음 두 시나리오를 해결합니다.

1. 서버, DB 또는 외부 LLM에 장애가 발생했을 때 문제 위치를 확인하고 복구한다.
2. 저장된 공고가 많아졌을 때 실제 조회 패턴에 맞는 쿼리와 인덱스를 적용한다.

## 전체 목표 구조

```text
사용자
→ Nginx :80/443
→ Uvicorn 127.0.0.1:8000
→ FastAPI
→ PostgreSQL
→ 외부 LLM API
```

Docker는 이번 필수 범위에 포함하지 않습니다. Ubuntu EC2, Python virtual environment, systemd와 Nginx를 이용한 비컨테이너 배포를 우선 검증합니다.

# Part 1. Linux 운영

## 1. Liveness와 readiness 분리

현재 `/health`는 FastAPI process가 응답한다는 사실만 확인합니다. 이를 다음 두 endpoint로 분리합니다.

```text
GET /health/live
GET /health/ready
```

### `GET /health/live`

Python process가 HTTP 요청에 응답할 수 있는지만 확인합니다.

```json
{
  "status": "alive"
}
```

DB가 중단되어도 liveness는 `200`이어야 합니다. DB 장애 때문에 systemd가 정상 FastAPI process를 반복 재시작하게 만들지 않습니다.

### `GET /health/ready`

애플리케이션이 DB 의존 기능을 처리할 준비가 됐는지 확인합니다.

```sql
SELECT 1;
```

정상 응답:

```json
{
  "status": "ready",
  "checks": {
    "database": "ok"
  }
}
```

DB 연결 실패 시 HTTP `503`:

```json
{
  "status": "not_ready",
  "checks": {
    "database": "failed"
  }
}
```

외부 LLM은 fallback 경로가 있으므로 readiness dependency에 포함하지 않습니다.

## 2. 요청 추적과 운영 로그

각 HTTP 요청에 request ID를 부여하고 응답 header와 완료 로그에 포함합니다.

```text
요청에 X-Request-ID가 있음 → 안전한 형식이면 재사용
요청에 X-Request-ID가 없음 → 서버가 UUID 생성
응답 → X-Request-ID header 반환
```

계약은 다음과 같습니다.

- 외부 request ID는 ASCII 영문 대·소문자, 숫자, `.`, `_`, `-`만 허용합니다.
- 길이는 1~128자입니다.
- 값이 없거나 형식·길이가 잘못되면 요청을 거부하지 않고 UUID4로 교체합니다.
- 정상적으로 생성된 모든 HTTP 응답에 `X-Request-ID`를 반환합니다.
- CORS 응답에서 `X-Request-ID`를 expose하여 frontend가 읽을 수 있게 합니다.
- 완료 로그의 `path`에는 query string을 포함하지 않습니다.

최소 HTTP 완료 로그:

```json
{
  "event": "http_request_completed",
  "request_id": "abc-123",
  "method": "POST",
  "path": "/job-analyses",
  "status_code": 200,
  "elapsed_ms": 20152
}
```

LLM fallback 로그:

```json
{
  "event": "llm_fallback",
  "request_id": "abc-123",
  "reason": "provider_timeout"
}
```

로그에 기록하지 않는 정보:

- 비밀번호
- JWT와 API key
- 이력서 원문
- 채용공고 원문
- LLM prompt와 raw response 전체

## 3. systemd 운영

`deploy/systemd/jobops.service`를 추가하여 다음을 검증합니다.

- EC2 재부팅 후 JobOps 자동 시작
- Uvicorn 비정상 종료 시 자동 재시작
- `.env` 환경변수 주입
- 일반 Linux 사용자 권한으로 실행
- `journalctl -u jobops` 로그 확인

## 4. Nginx reverse proxy

`deploy/nginx/jobops.conf`를 추가합니다.

```text
외부 사용자
→ Nginx 80/443
→ Uvicorn 127.0.0.1:8000
```

Nginx는 다음 역할을 담당합니다.

- 외부 HTTP·HTTPS 요청 수신
- Uvicorn port의 외부 직접 노출 방지
- frontend 정적 파일 제공
- reverse proxy
- 요청 크기와 timeout 제한
- access·error log

## 5. 장애 실험

### FastAPI process 종료

```text
Uvicorn process 종료
→ systemd가 자동 재시작
→ /health/live 정상 복구
```

### DB 중단

```text
PostgreSQL 중지
→ /health/live = 200
→ /health/ready = 503
→ PostgreSQL 시작
→ /health/ready = 200
```

### 외부 LLM timeout

```text
LLM 응답 지연
→ provider timeout
→ deterministic fallback
→ 분석 API = 200
→ fallback reason log 확인
```

| 장애 | 사용자 영향 | 탐지 | 복구 |
| --- | --- | --- | --- |
| FastAPI 종료 | 일시적 접속 실패 | liveness | systemd 자동 재시작 |
| DB 종료 | DB 기능 사용 불가 | readiness 503 | DB 재시작 |
| LLM timeout | 기본 분석 제공 | fallback log | 자동 fallback |

# Part 2. 관계형 DB 기본기

## 1. 실제 조회 기능

저장된 공고를 다음 조건으로 조회할 수 있게 확장합니다.

```text
GET /job-postings
?company_name=Example
&is_active=true
&sort=expiration_date
&limit=20
&offset=0
```

검증할 내용:

- 회사명 filter
- 활성 공고 filter
- 마감일 정렬
- pagination
- 잘못된 query parameter validation
- N+1 query 방지

## 2. 실제 SQL과 실행 계획

ORM이 생성하는 SQL과 동등한 query를 확인합니다.

```sql
SELECT *
FROM job_postings
WHERE is_active = true
  AND company_name = 'Example'
ORDER BY expiration_date
LIMIT 20;
```

테스트 데이터를 충분히 준비한 뒤 `EXPLAIN ANALYZE`로 다음을 확인합니다.

- sequential scan 여부
- 예상 row와 실제 row
- 별도 sort 발생 여부
- 실행 시간

## 3. 조회 패턴 기반 복합 인덱스

실제 query와 실행 계획을 확인한 뒤 Alembic migration으로 인덱스를 추가합니다.

초기 후보:

```sql
CREATE INDEX ix_job_postings_active_expiration
ON job_postings (is_active, expiration_date);
```

인덱스를 먼저 정답으로 가정하지 않습니다. 데이터 분포와 query 조건을 기준으로 적용 전후 실행 계획을 비교하고 실제 측정값만 문서에 기록합니다.

## 4. 트랜잭션 rollback

공고와 요구사항의 일괄 저장을 하나의 transaction으로 처리합니다.

```text
공고 저장 성공
→ 요구사항 1 저장 성공
→ 요구사항 2 저장 실패
→ 공고와 모든 요구사항 rollback
```

테스트에서 다음을 검증합니다.

- 중간 오류 후 공고가 남지 않음
- 부분 저장된 요구사항이 없음
- 같은 session을 재사용할 수 있도록 rollback됨
- constraint 오류가 적절한 service·HTTP 오류로 변환됨

## 5. 정규화 설명

현재 모델의 다음 관계를 실제 근거로 설명합니다.

```text
job_postings 1 ─── N job_requirements
```

공고 요구사항을 별도 table로 분리한 이유:

- 요구사항 단위 조회
- 필수·우대 조건 filter
- 중복 데이터 감소
- foreign key 기반 참조 무결성
- 요구사항 조회용 index 적용

`raw_payload` JSON은 정규화 대상 데이터를 대체하기 위한 것이 아니라 외부 원본을 보존하기 위한 필드로 구분합니다.

# 작업 티켓

## Ticket 1: Health check 분리

- [x] `GET /health/live` 추가
- [x] `GET /health/ready` 추가
- [x] DB `SELECT 1` 확인
- [x] DB 오류 시 readiness `503`
- [x] 정상·장애 테스트
- [x] 기존 `/health` 호환 유지

## Ticket 2: Request tracing

- [x] `X-Request-ID` 입력 지원
- [x] request ID가 없거나 안전하지 않으면 UUID 생성
- [x] response header에 `X-Request-ID` 반환
- [x] method, path, status, elapsed time JSON 로그
- [x] LLM fallback reason과 request ID 연결
- [x] 민감정보 미포함 테스트

## Ticket 3: 공고 조회 query

- [x] `company_name` 정확 일치 filter
- [x] `is_active` filter
- [x] `expiration_date` 오름차순·`NULLS LAST` sort
- [x] filter·sort 이후 pagination
- [x] route·service 테스트

## Ticket 4: 복합 인덱스

- [x] 실제 조회 패턴 정의
- [x] PostgreSQL 전용 benchmark seed·측정 도구 작성
- [ ] PostgreSQL에 성능 검증용 test data 생성
- [ ] 인덱스 적용 전 실행 계획 측정
- [ ] 측정 근거에 따른 Alembic migration 작성
- [ ] 적용 후 실행 계획 측정
- [ ] 비교 결과 문서화

## Ticket 5: Transaction rollback

- [x] 공고와 요구사항 일괄 저장 service
- [x] DB constraint와 예상치 못한 중간 실패 재현
- [x] 공고와 모든 요구사항 전체 rollback 검증
- [x] rollback 후 같은 session 재사용 검증
- [x] constraint 오류를 안정적인 service 오류로 변환

## Ticket 6: Linux 배포 파일

- `deploy/systemd/jobops.service`
- `deploy/nginx/jobops.conf`
- `deploy/README.md`
- 환경변수와 migration 절차
- 배포·rollback·로그 확인 절차

# 오늘 할 일 — 2026-07-22

오늘은 전체 Linux 배포를 한 번에 시도하지 않습니다. 로컬에서 검증 가능한 **Ticket 1: Health check 분리**만 완료하는 것을 1차 목표로 합니다.

## 오늘의 목표

> `/health/live`와 `/health/ready`를 구현하고, DB 연결 실패 시 `live=200`, `ready=503`이 되는 것을 자동화 테스트로 검증한다.

## 작업 순서

1. 현재 [app/main.py](../../app/main.py)의 `/health` 구현과 DB session 구성을 다시 확인합니다.
2. health endpoint를 별도 router 또는 명확한 작은 module로 분리합니다.
3. `GET /health/live`를 구현합니다.
4. `GET /health/ready`에서 SQLAlchemy `SELECT 1`을 실행합니다.
5. DB 정상 상태에서 `live=200`, `ready=200` 테스트를 작성합니다.
6. DB dependency 또는 readiness check를 교체하여 DB 실패를 재현합니다.
7. DB 실패 상태에서 `live=200`, `ready=503` 테스트를 작성합니다.
8. readiness 오류 응답에 내부 DB URL, 계정, exception 원문이 노출되지 않는지 확인합니다.
9. 기존 전체 pytest를 실행합니다.
10. API 문서와 해당 날짜 session log에 결과를 기록합니다.

## 오늘 완료 조건

- [x] `GET /health/live`가 `200`과 `{"status":"alive"}`를 반환한다.
- [x] DB 정상 시 `GET /health/ready`가 `200`을 반환한다.
- [x] DB 장애 시 `GET /health/ready`가 `503`을 반환한다.
- [x] DB 장애 중에도 `GET /health/live`는 `200`을 반환한다.
- [x] readiness 응답과 로그에 DB credential이나 내부 exception이 노출되지 않는다.
- [x] Swagger에서 두 endpoint의 의미를 구분할 수 있다.
- [x] 기존 backend 회귀 테스트가 모두 통과한다.
- [x] 구현 결과가 문서와 session log에 기록된다.

## 추가 완료 작업

Ticket 1 health check, Ticket 2 request tracing, Ticket 3 공고 조회와 Ticket 5 transaction rollback을 완료했습니다. Ticket 4 index는 실제 PostgreSQL query plan과 데이터 분포를 확보한 뒤 적용합니다.

Ticket 4의 query와 재현 도구는 준비됐지만 현재 개발 환경에는 Docker·PostgreSQL server·`psql`이 없고 5432 port도 열려 있지 않아 실제 측정은 대기 상태입니다. [PostgreSQL 공고 조회 실행 계획 실험](../experiments/postgresql-query-plan.md)에 환경 확인 결과와 실행 절차를 기록했습니다.

기존 Ubuntu EC2를 대체 실행 환경으로 선택했지만 마지막 확인에서는 알려진 public IP의 SSH 22번 port가 timeout됐고 80·443·8000도 접근되지 않았습니다. AWS 콘솔에서 인스턴스 실행 상태, 현재 public IP와 SSH Security Group을 확인한 뒤 재개합니다. SSH key나 DB credential은 문서에 기록하지 않습니다.

# 이후 권장 순서

```text
로컬 개발
1. health/live·ready
2. request ID와 구조화 로그
3. 공고 filter·sort·pagination
4. transaction rollback 테스트
5. index migration과 실행 계획

EC2 작업
6. systemd
7. Nginx
8. PostgreSQL 연결과 migration
9. 장애 실험
10. 결과 문서화
```

# 전체 완료 조건

- EC2 재부팅 후 JobOps가 자동 시작됩니다.
- Nginx를 통해 외부에서 frontend와 API에 접근할 수 있습니다.
- Uvicorn port는 외부에 직접 노출되지 않습니다.
- liveness와 readiness가 process 장애와 DB 장애를 구분합니다.
- LLM 장애에도 분석 API가 fallback 결과를 반환합니다.
- request ID로 HTTP 요청과 fallback 로그를 추적할 수 있습니다.
- PostgreSQL migration과 핵심 사용자 흐름이 성공합니다.
- 공고 조회 query와 pagination이 구현됩니다.
- transaction 중간 실패 시 전체 rollback됩니다.
- 실제 실행 계획을 기준으로 인덱스 적용 효과를 설명할 수 있습니다.
- 장애 재현, 진단과 복구 절차가 저장소 문서에 남아 있습니다.

# 포트폴리오에서 설명할 결과

전체 작업이 끝난 뒤 다음과 같이 설명할 수 있어야 합니다.

> Ubuntu EC2에 FastAPI 서비스를 배포하고 Nginx reverse proxy, systemd 자동 재시작, liveness·readiness health check와 요청 추적 로그를 구성했습니다. DB 장애와 외부 LLM 장애를 구분하고, LLM 장애 시 fallback을 제공해 서비스 가용성을 유지했습니다. 또한 실제 공고 조회 패턴을 기준으로 PostgreSQL 실행 계획과 복합 인덱스를 비교하고, 공고·요구사항 일괄 저장의 transaction rollback을 검증했습니다.

## 관련 문서

- [Swagger backend MVP 상태](mvp-status.md)
- [1차 통합 MVP 후기 및 개선 방향](first-integrated-mvp-retrospective.md)
- [지원 의사결정부터 지원 관리까지의 제품 로드맵](decision-to-application-roadmap.md)
- [시스템 구조](../architecture/system-overview.md)
- [리스크 목록](risk-register.md)
