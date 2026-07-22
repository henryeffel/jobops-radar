# PostgreSQL 공고 조회 실행 계획 실험

기준일: 2026-07-22

## 상태

측정 대기 — 현재 개발 환경에는 Docker, PostgreSQL server와 `psql`이 없고 `127.0.0.1:5432`도 열려 있지 않습니다. 기존 EC2를 PostgreSQL 실험 환경으로 사용하기로 했지만 현재 알려진 public IP의 22·80·443·8000 port가 모두 응답하지 않아 접속 정보를 확인해야 합니다. SQLite 실행 계획을 PostgreSQL 결과로 대신하지 않습니다.

## 목적

`GET /job-postings`의 실제 service statement를 PostgreSQL에서 실행하고, 데이터 분포와 `EXPLAIN ANALYZE`를 근거로 index 필요성과 컬럼 순서를 결정합니다.

측정 query는 다음 조건을 조합합니다.

```text
company_name 정확 일치
AND is_active boolean
ORDER BY expiration_date ASC NULLS LAST, id DESC
LIMIT 20 OFFSET 0
```

benchmark script는 API service와 같은 `build_job_postings_statement`를 사용하므로 별도의 유사 SQL을 측정하지 않습니다.

## 안전장치

- PostgreSQL dialect가 아니면 실행을 거부합니다.
- benchmark row는 `source=postgres-query-plan-benchmark`로 격리합니다.
- 기존 benchmark row가 있으면 seed를 중단하며 암묵적으로 덮어쓰지 않습니다.
- cleanup은 해당 source의 row만 삭제합니다.
- 실제 계획 측정 전에는 index migration을 작성하지 않습니다.

## 실행 절차

Docker 또는 별도 PostgreSQL 16 환경을 준비한 뒤 다음 순서로 실행합니다.

```powershell
docker compose up -d postgres
$env:DATABASE_URL='postgresql+psycopg://jobops:jobops@localhost:5432/jobops'
python -m alembic upgrade head
python -m scripts.postgres_query_plan seed --rows 50000
python -m scripts.postgres_query_plan explain --output docs/experiments/postgresql-query-plan-before.json
```

EC2를 사용할 때는 PostgreSQL 5432를 인터넷 전체에 공개하지 않습니다. application과 benchmark를 EC2 내부에서 실행하거나 SSH tunnel을 사용하며, Security Group의 SSH source도 작업자의 현재 IP로 제한합니다.

기준선에서 다음을 기록합니다.

- planning time과 execution time
- root plan node와 scan 방식
- filter로 제거된 row 수
- 예상 row와 실제 row 차이
- 별도 Sort node와 sort method
- shared buffer hit/read
- 선택된 index 이름

## index 후보 결정 규칙

현재 query만 보면 `(company_name, is_active, expiration_date, id)`가 후보가 될 수 있지만 아직 결정하지 않습니다. 회사명 cardinality, 활성 공고 비율, 마감일 `NULL` 비율과 baseline plan을 함께 확인합니다.

index를 적용할 근거가 확인되면 별도 Alembic migration을 작성하고 같은 데이터와 명령으로 after plan을 저장합니다. 개선이 없거나 쓰기·저장 비용이 더 크면 후보 index를 유지하지 않습니다.

## 정리

실험이 끝나면 benchmark row만 제거합니다.

```powershell
python -m scripts.postgres_query_plan cleanup
```

운영 또는 사용자 데이터베이스에서는 이 benchmark를 실행하지 않습니다.
