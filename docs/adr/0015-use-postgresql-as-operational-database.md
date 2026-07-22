# ADR-0015: 운영 목표 관계형 데이터베이스로 PostgreSQL 사용

## 상태

승인됨

## 배경

JobOps Radar는 사용자, 채용공고, 요구사항, 프로필과 감사 로그처럼 관계와 정합성이 중요한 데이터를 다룹니다. 동시에 외부 채용공고 provider의 원본 payload와 분석 시점 snapshot처럼 구조가 변할 수 있는 데이터도 보존할 수 있어야 합니다.

프로젝트는 Python과 FastAPI를 사용하지만 이 선택이 특정 데이터베이스나 ORM을 자동으로 결정하지는 않습니다. 외부 LLM 호출 역시 PostgreSQL을 요구하지 않습니다. LLM 응답의 구조와 근거는 Pydantic schema와 애플리케이션 검증으로 관리하며, 데이터베이스의 JSON 타입을 schema validation의 대체재로 사용하지 않습니다.

ADR-0003은 환경 준비 전까지 SQLite를 로컬 fallback으로 허용했고, ADR-0004는 SQLAlchemy와 Alembic으로 데이터 접근과 migration 경계를 관리하기로 결정했습니다. 이제 운영 목표 관계형 데이터베이스와 선택 근거를 명확히 기록할 필요가 있습니다.

## 결정

운영 목표 관계형 데이터베이스로 PostgreSQL을 사용합니다. SQLite는 빠른 로컬 개발과 단위 테스트를 위한 fallback으로만 유지하며, SQLite 테스트 통과를 PostgreSQL 운영 호환성의 증거로 간주하지 않습니다.

데이터는 다음 원칙으로 모델링합니다.

- 사용자, 공고, 요구사항, 프로필과 감사 이벤트처럼 검색, 관계, 무결성에 필요한 데이터는 명시적인 컬럼, PK, FK, `NOT NULL`, `UNIQUE`와 관계형 테이블로 모델링합니다.
- 외부 원본 payload, 분석 snapshot과 provider별 부가정보처럼 구조 변경 가능성이 큰 데이터에만 JSONB 사용을 검토합니다.
- 자주 조회하거나 제약해야 하는 값을 JSONB에만 숨기지 않고 일반 컬럼 또는 정규화된 테이블로 승격합니다.
- LLM 응답은 Pydantic schema, evidence ID와 도메인 규칙 검증을 통과한 뒤에만 영속화 대상으로 취급합니다.
- SQLAlchemy는 모델과 session 경계를 제공하지만 실제 SQL, transaction과 실행 계획에 대한 이해를 대신하지 않습니다.
- 모든 schema 변경은 Alembic migration으로 관리하고 PostgreSQL 환경에서 직접 검증합니다.

## 선택 근거

PostgreSQL과 MySQL은 모두 현재 서비스의 핵심 관계형 요구사항을 충족할 수 있습니다. PostgreSQL을 선택한 이유는 다음과 같습니다.

- 정규화된 관계형 데이터와 가변적인 metadata를 하나의 데이터베이스에서 관리할 수 있습니다.
- JSONB 연산자와 GIN index 등 향후 원본 payload와 분석 snapshot을 조회할 때 사용할 수 있는 선택지가 풍부합니다.
- transaction, constraint, index와 복잡한 조회를 지원하며 SQLAlchemy 및 Alembic과 안정적으로 통합됩니다.
- 현재 프로젝트에 PostgreSQL 목표 구조와 migration 경계가 이미 마련되어 있어, 제품 요구 없이 데이터베이스를 교체하는 비용을 피할 수 있습니다.

JSONB 확장 가능성은 선택 근거 중 하나일 뿐이며, 실제 사용과 측정 없이 PostgreSQL이 MySQL보다 성능상 우월하다고 주장하지 않습니다.

## 결과와 trade-off

관계형 무결성을 유지하면서 provider별 원본과 분석 snapshot의 확장 가능성을 확보할 수 있습니다. SQLAlchemy를 통해 애플리케이션의 DB 접근 경계를 유지하고 Alembic으로 변경 이력을 재현할 수 있습니다.

반면 다음 비용과 제약을 수용합니다.

- SQLite와 PostgreSQL은 타입, constraint, transaction과 동시성 동작이 다르므로 PostgreSQL 통합 검증이 별도로 필요합니다.
- JSONB를 과도하게 사용하면 schema가 불명확해지고 관계형 조회와 제약조건이 약해질 수 있습니다.
- PostgreSQL 운영 경험이 MySQL 고유의 dialect, InnoDB 동작과 운영 경험을 그대로 증명하지는 않습니다.
- ORM 추상화만 사용하고 실제 SQL과 실행 계획을 확인하지 않으면 쿼리 작성 및 최적화 역량을 증명할 수 없습니다.
- 두 데이터베이스를 동시에 공식 지원하면 migration과 테스트 조합이 늘어나므로 현재 범위에서는 PostgreSQL만 운영 목표로 둡니다.

## 검증 의무

이 결정과 관계형 데이터베이스 활용 능력은 ADR만으로 증명하지 않습니다. 다음 결과를 코드, 테스트와 실험 문서로 남겨야 합니다.

1. 빈 PostgreSQL 데이터베이스에 전체 Alembic migration을 적용하고 model drift를 확인합니다.
2. 실제 공고 조회에 filter, sort와 pagination을 적용하고 ORM이 생성한 SQL을 확인합니다.
3. 충분한 테스트 데이터에서 `EXPLAIN ANALYZE`로 index 적용 전후의 scan, sort, row 수와 실행시간을 비교합니다.
4. 공고와 요구사항 일괄 저장 중 오류가 발생하면 전체 transaction이 rollback되는지 검증합니다.
5. 동시 중복 생성 요청을 데이터베이스 `UNIQUE` constraint가 최종 차단하는지 검증합니다.
6. 관계 loading 시 실제 SQL 횟수를 측정해 N+1 발생 여부와 loading 전략의 효과를 확인합니다.
7. connection pool 고갈, 끊어진 연결과 데이터베이스 장애가 API와 readiness에 어떻게 나타나는지 검증합니다.

측정 결과가 개선을 보이지 않으면 index나 최적화 성과를 추정해서 기록하지 않습니다.

## 검토한 대안

### SQLite만 사용

설치 없이 빠르게 개발할 수 있지만 운영 환경의 동시성, transaction, 타입과 실행 계획을 검증하기에 부족합니다.

### MySQL 사용

현재 요구사항을 충분히 구현할 수 있고 MySQL 중심 조직에 직접적인 경험을 제공하는 합리적인 대안입니다. 그러나 현재 프로젝트에는 MySQL을 요구하는 제품 또는 운영 제약이 없고, PostgreSQL 기반 목표와 migration을 교체할 만큼의 추가 제품 가치가 확인되지 않았습니다. 특정 채용공고에 맞추기 위해 검증된 기술 기반을 교체하지 않습니다.

### PostgreSQL과 MySQL 동시 지원

DB 이식성과 학습 범위를 확인할 수 있지만 dialect별 migration, constraint와 통합 테스트 비용이 현재 프로젝트 규모에 비해 큽니다. 실제 사용자 또는 운영 요구가 생길 때 재검토합니다.

### 문서형 데이터베이스 사용

가변 payload 저장에는 편리하지만 사용자, 공고, 요구사항과 분석 실행 사이의 관계, 참조 무결성과 transaction이 핵심인 현재 모델에는 관계형 데이터베이스가 더 적합합니다.

## 재검토 조건

- 배포 환경이나 조직 표준이 MySQL 등 다른 데이터베이스를 요구합니다.
- PostgreSQL JSONB 기능을 실제로 사용하지 않고 다른 운영상 이점도 확인되지 않습니다.
- 서로 다른 DB dialect를 공식 지원해야 하는 사용자 또는 제품 요구가 생깁니다.
- 데이터 접근 패턴이 관계형 모델보다 다른 저장소에 명확히 적합해집니다.

## 관련 문서

- [ADR-0003: PostgreSQL 이전 SQLite fallback 사용](0003-use-sqlite-fallback-before-postgresql.md)
- [ADR-0004: SQLAlchemy와 Alembic 사용](0004-use-sqlalchemy-and-alembic.md)
- [ADR-0014: 사용자 제공 공고 입력과 검증된 LLM fallback](0014-user-supplied-job-input-and-validated-llm-fallback.md)
- [Linux 운영과 관계형 DB 기본기 개발 계획](../project/linux-operations-and-relational-db-development.md)
- [시스템 구조](../architecture/system-overview.md)

