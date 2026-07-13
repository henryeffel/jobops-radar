# ADR-0003: PostgreSQL 이전 SQLite fallback 사용

## 상태
승인됨

## 배경
운영 목표 DB는 PostgreSQL이지만 로컬 Docker 환경이 준비되지 않아 개발이 멈출 위험이 있었습니다.

## 결정
SQLAlchemy와 Alembic 경계를 유지하면서 로컬 개발과 test에는 SQLite를 허용합니다. PostgreSQL을 최종 목표로 유지합니다.

## 결과
외부 환경 없이 개발할 수 있지만 PostgreSQL 전용 타입, constraint, query plan 차이는 별도로 검증해야 합니다. SQLite 통과를 운영 호환성 증거로 간주하지 않습니다.

## 전환 조건
Docker 또는 관리형 PostgreSQL 환경을 확보하면 migration과 통합 test를 PostgreSQL에서도 실행합니다.
