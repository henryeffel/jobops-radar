# JobOps Radar Work Summary

## Project Direction

JobOps Radar is a backend-only FastAPI portfolio project targeting Python/FastAPI
backend roles. The MVP deadline is 2026-07-24. PostgreSQL with Docker is the
intended final database environment; SQLite is temporary local infrastructure
while Docker Desktop installation is pending.

## Completed Work

| Area | Status | Result |
| --- | --- | --- |
| Repository | Complete | Git initialized with GitHub `origin`, `main`, and `dev` workflow |
| API skeleton | Complete | FastAPI app, `/health`, generated `/docs`, and JobPosting routes |
| Project documentation | Foundation complete | English/Korean READMEs and Carrot Identity Service case study define current scope and roadmap |
| Testing | Complete | pytest health, settings, DB, model, schema, service, and route tests |
| Configuration | Complete | Typed `pydantic-settings`, optional `.env`, cached settings |
| Database foundation | Complete | SQLAlchemy 2.0 engine, session factory, base, and `get_db()` |
| Local database | Temporary | SQLite fallback through `sqlite:///./jobops.db` |
| Domain storage | Initial model complete | Provider-neutral `JobPosting` with database uniqueness |
| Persistence service | Complete | Validated create/read schemas, create, identity lookup, duplicate translation, paginated listing |
| JobPosting API | Initial operations complete | Create-or-get, two identity lookups, and bounded list pagination |
| Migrations | Initial revision complete | Alembic creates and drops the `job_postings` table |
| Production database | Pending locally | PostgreSQL Compose definition retained; Docker not installed |
| Architecture records | Complete and ongoing | ADR index documents active decisions and trade-offs |
| Continuous integration | Initial workflow complete | GitHub Actions installs project dev extras, tests migrations, and compiles sources |

## Current Validation State

- Thirty pytest tests pass.
- `/health` returns `{"status": "ok"}`.
- `/docs` has been verified.
- SQLite migration upgrade/check/downgrade passes.
- PostgreSQL offline migration SQL generation passes.
- Mock `JobPosting` persistence and duplicate rejection are covered by tests.
- Service-level creation, identity retrieval, and duplicate handling are tested.
- `/docs` includes `GET /job-postings` and all existing JobPosting operations.
- Pagination is ordered by `created_at DESC, id DESC`; `limit` is bounded to
  1–100 and `offset` must be non-negative.

## Explicitly Not Implemented

- Authentication or user models
- JobPosting update and delete operations
- Saramin API integration
- LLM analysis or scoring
- Frontend
- LangChain or vector database

## Next Milestone

Add structured JD requirement persistence for manually curated case-study data,
without adding LLM extraction, authentication, or OIDC endpoints.
