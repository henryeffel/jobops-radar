# ADR-0004: SQLAlchemy와 Alembic 사용

## 상태
승인됨

## 배경
Domain model과 schema 변경을 반복 가능하게 관리하고 SQLite와 PostgreSQL 사이의 DB 접근 경계를 유지해야 합니다.

## 결정
SQLAlchemy 2.0 ORM과 Alembic migration을 사용합니다.

## 결과
Model, session, migration 이력이 명시적으로 남고 DB 교체 가능성이 높아집니다. 반면 ORM 추상화가 query와 transaction 이해를 대신하지 않으며 migration을 직접 검토해야 합니다.

## 검토한 대안
- Raw SQL만 사용: 제어력은 높지만 현재 범위에서 반복 코드가 많습니다.
- Schema 자동 생성만 사용: 빠르지만 변경 이력과 운영 migration 경로가 없습니다.
