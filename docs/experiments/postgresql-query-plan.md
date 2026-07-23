# PostgreSQL 공고 조회 실행 계획 실험

기준일: 2026-07-22

## 상태

측정 완료 — Ubuntu 26.04 EC2의 PostgreSQL 18.4에서 migration을 적용하고 5만 건 baseline과 index 적용 후 실행 계획을 비교했습니다. PostgreSQL은 `localhost`와 Unix socket으로만 접근하며 5432를 외부에 공개하지 않았습니다.

## 측정 결과

| 항목 | index 적용 전 | index 적용 후 |
| --- | ---: | ---: |
| 실행 시간 | 10.480ms | 0.148ms |
| scan | Seq Scan | Index Scan |
| 별도 sort | top-N heapsort | 없음 |
| 반환 전에 검사·제거한 행 | 50,000행 중 47,500행 제거 | 필요한 20행에서 종료 |
| shared block | hit 1,357 | hit 20, read 3 |

측정 환경에서는 약 70.8배 빨라졌습니다. 절대 시간과 개선 폭은 데이터 분포와 cache 상태에 따라 달라지므로 production 전체 성능을 대표하지 않습니다.

적용한 index는 `ix_job_postings_company_active_expiration_id`이며 컬럼 순서는 `(company_name, is_active, expiration_date ASC, id DESC)`입니다. 회사명과 활성 상태 filter를 index condition으로 처리하고, 마감일과 ID 정렬 순서를 그대로 만족해 별도 sort를 제거했습니다.

실험이 끝난 뒤 `source=postgres-query-plan-benchmark`인 5만 행만 삭제하고 `VACUUM (ANALYZE) job_postings`를 실행했습니다. 전후 JSON 원본은 EC2의 권한 제한 경로 `/home/ubuntu/jobops-benchmarks/`에 보관했습니다.

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
