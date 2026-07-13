# 아키텍처 결정 기록

ADR은 중요한 기술 선택의 배경, 결정, 결과를 짧게 기록합니다. 구현 코드만으로는 알기 어려운 판단 근거와 전환 조건을 보존하는 것이 목적입니다.

## 상태 정의

- `제안됨`: 검토 중이며 아직 최종 결정이 아닙니다.
- `승인됨`: 현재 프로젝트에 적용하는 결정입니다.
- `대체됨`: 이후 ADR이 이 결정을 대신합니다.
- `폐기됨`: 더 이상 적용하지 않습니다.

## 문서 목록

- [ADR-0001: FastAPI 사용](0001-use-fastapi.md)
- [ADR-0002: Backend-first MVP](0002-backend-first-mvp.md)
- [ADR-0003: PostgreSQL 이전 SQLite fallback 사용](0003-use-sqlite-fallback-before-postgresql.md)
- [ADR-0004: SQLAlchemy와 Alembic 사용](0004-use-sqlalchemy-and-alembic.md)
- [ADR-0005: 결정론적인 적합도 점수 사용](0005-use-deterministic-fit-scoring.md)
- [ADR-0006: Frontend 구현 연기](0006-delay-frontend.md)
- [ADR-0007: Session log와 학습 노트 사용](0007-use-session-logs-and-learning-notes.md)
- [ADR-0008: Scraping 대신 Saramin 공식 API 사용](0008-use-saramin-official-api-not-scraping.md)
- [ADR-0009: Microservices 대신 Modular Monolith 선택](0009-modular-monolith-over-microservices.md)
- [ADR-0010: Saramin API 의존성 분리](0010-decouple-saramin-api.md)
- [ADR-0011: 내부 인증에 PyJWT 사용](0011-pyjwt-for-internal-auth.md)
- [ADR-0012: OIDC 구현 범위 제한](0012-limit-oidc-scope.md)

## 작성 규칙

각 ADR에는 상태, 배경, 결정, 결과, 검토한 대안, 관련 문서를 기록합니다. 이미 승인된 기록은 직접 고치기보다 새로운 ADR에서 대체하는 방식을 우선합니다.
