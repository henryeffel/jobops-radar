# JobOps Radar 작업 요약

> 이 문서는 Identity/Auth 구현 전 시점의 작업 기록입니다. 최신 상태는 루트 `README.md`와 `handoff.md`를 기준으로 확인합니다.

## 프로젝트 방향

JobOps Radar는 Python/FastAPI backend 직무를 목표로 하는 backend-only 포트폴리오 프로젝트입니다. 최종 DB 환경은 Docker 기반 PostgreSQL이며, Docker Desktop 설치 전까지 SQLite를 임시 로컬 환경으로 사용했습니다.

## 완료 작업

| 영역 | 상태 | 결과 |
| --- | --- | --- |
| 저장소 | 완료 | GitHub `origin`, `main`, `dev` workflow 구성 |
| API 기본 구조 | 완료 | FastAPI app, `/health`, `/docs`, JobPosting route |
| 프로젝트 문서 | 기반 완료 | README와 Carrot Identity Service 사례 연구에 범위·로드맵 기록 |
| 테스트 | 완료 | 당시 기준 40개 pytest로 설정·DB·model·schema·service·route 검증 |
| 설정 | 완료 | `pydantic-settings`, 선택적 `.env`, cached settings |
| DB 기반 | 완료 | SQLAlchemy 2.0 engine, session factory, Base, `get_db()` |
| 로컬 DB | 임시 | `sqlite:///./jobops.db` fallback |
| Domain 저장 | 초기 model 완료 | 공급자 중립 `JobPosting`과 연결된 `JobRequirement` |
| Persistence service | 완료 | 공고·요구사항 생성, 조회, 공고별 목록 |
| JobPosting API | 초기 기능 완료 | Create-or-get, identity 조회, 제한된 pagination |
| Migration | 당시 2개 완료 | `job_postings`, `job_requirements` 관리 |
| 운영 DB | 로컬 대기 | PostgreSQL Compose 설정 유지, Docker 미설치 |
| ADR | 진행 중 | 주요 결정과 trade-off 기록 |
| CI | 초기 workflow 완료 | GitHub Actions에서 설치·test·migration·compile 실행 |

## 당시 검증 상태

- pytest 40개가 통과했습니다.
- `/health`와 `/docs`를 확인했습니다.
- SQLite migration upgrade/check/downgrade를 통과했습니다.
- PostgreSQL offline migration SQL 생성을 확인했습니다.
- 공고 저장·중복 거부·identity 조회·pagination을 test했습니다.
- Pagination은 `created_at DESC, id DESC`, `limit` 1~100, 0 이상의 `offset`을 사용했습니다.
- 요구사항의 부모 연결, 유형, 중요도, 기본 source, 조회, 결정론적 목록을 test했습니다.
- 당시 Alembic head는 `6f3b6c2d8a91`이었습니다.

## 당시 미구현 범위

인증·사용자 model, 공고 수정·삭제, 요구사항 API, Saramin 연동, LLM 분석·점수, frontend, LangChain, vector DB는 구현하지 않은 상태였습니다.

## 당시 다음 단계

분석·LLM·Auth/OIDC를 추가하기 전에 검증된 service를 이용해 작은 nested JobRequirement 생성·목록 API를 노출하는 것이 목표였습니다.
