# Handoff

## Current state

- `README.md` now defines the product purpose, current implementation, local
  setup, environment variables, API surface, CI behavior, and roadmap.
- The Karrot Identity Service Backend posting is documented as the first case
  study under `docs/job-analysis/`. It guides future OIDC, B2B account,
  security/privacy, availability, authentication UX, and audit-log work without
  claiming those capabilities are implemented.
- Minimal FastAPI application initialized.
- `GET /health` returns `{"status": "ok"}`.
- Environment and optional `.env` settings use cached `pydantic-settings`.
- FastAPI title and version are sourced from application settings.
- Settings include placeholders for database, JWT, Saramin, and LLM configuration;
  no related integrations have been implemented.
- SQLite is the current local-development fallback through
  `DATABASE_URL=sqlite:///./jobops.db`.
- PostgreSQL remains the default configuration and intended production target;
  its local Docker Compose service is retained.
- Docker Desktop installation is pending, so local PostgreSQL is not available
  yet.
- SQLAlchemy 2.0 provides a shared engine, session factory, declarative base, and
  FastAPI `get_db()` dependency.
- Alembic is initialized and reads the same `DATABASE_URL` as the application.
- A provider-neutral `JobPosting` model stores mock/manual data now and can
  support Saramin later. The database enforces unique `(source, external_id)`
  pairs.
- `JobPostingCreate` and `JobPostingRead` define validated persistence DTOs.
  The job posting service creates records, retrieves them by source identity,
  and translates duplicate conflicts into `DuplicateJobPostingError`.
- FastAPI exposes `POST /job-postings`, `GET /job-postings`,
  `GET /job-postings/{job_posting_id}`, and
  `GET /job-postings/by-source/{source}/{external_id}`. Duplicate POSTs return
  the existing record without inserting another row.
- `GET /job-postings` uses bounded offset pagination. It defaults to
  `limit=20&offset=0`, accepts limits from 1 through 100 and non-negative
  offsets, and orders by `created_at DESC, id DESC`.
- The initial Alembic revision creates `job_postings` and works with SQLite;
  PostgreSQL offline SQL generation also passes.
- Saramin Open API approval is pending. No Saramin client, access key
  requirement, authentication, or user model has been added.
- Project-specific backend interview notes are available in
  `docs/interview-prep/`, with implemented and future topics labeled separately.
- Architecture decisions are indexed in `docs/adr/README.md`; add or supersede
  ADRs when a future task changes a consequential design decision.
- Daily progress for 2026-06-30 is summarized in
  `docs/daily-logs/2026-06-30.md`.
- GitHub Actions runs on pushes and pull requests targeting `main` or `dev`.
  CI installs the repository and development extras from `pyproject.toml` with
  `pip install -e ".[dev]"`, then runs tests, migrations, and compilation.

## Verification

- `python -m pytest -q -p no:cacheprovider`: 30 passed, including pagination
  defaults, limit/offset behavior, deterministic ordering, invalid query
  validation, route creation and lookups, `/health`, and OpenAPI paths.
- SQLite migration upgrade, `alembic check`, and downgrade passed.
- PostgreSQL offline migration SQL generation passed.
- Python source compilation passed.
- Docker Compose runtime validation was skipped because Docker was not installed
  in the implementation environment.

## Run locally

```bash
python -m venv .venv
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The active `DATABASE_URL` in `.env.example` uses SQLite. Do not commit the copied
`.env` file.

After Docker Desktop is installed, local PostgreSQL can be started with:

```bash
docker compose up -d
```

Then replace `DATABASE_URL` in `.env` with the documented PostgreSQL target and
run `alembic upgrade head` again.

Run tests:

```bash
python -m pytest -q -p no:cacheprovider
```

Tests use a new in-memory SQLite engine per test and do not require a filesystem
temp database. Do not pass a persistent or protected directory through
`--basetemp`; pytest may clean and recreate the directory it owns. Future tests
that genuinely need files should request pytest's `tmp_path` fixture without
hardcoding its parent. `.tmp_pytest/` remains ignored for local troubleshooting
artifacts.

## Next recommended task

Add structured JD requirement persistence for manually curated case-study data:
define the minimal model, migration, schemas, service, and tests without adding
LLM extraction or Auth/OIDC endpoints.

## Required session logging

After every future Codex task:

1. Update `handoff.md`.
2. Create or update `docs/session-logs/YYYY-MM-DD.md` for the actual session
   date.

Update these cumulative documents only when the task materially changes their
content:

- `docs/work-summary.md`
- `docs/learning-notes/backend-concepts.md`
- `docs/learning-notes/cs-dsa-concepts.md`

Every session entry must use the template in
`docs/session-logs/2026-06-29.md` and include goal, actual changes, files,
validation commands and results, backend concepts, CS/DSA concepts, design
decisions, issues or warnings, and the next small task. If no major DSA was used,
state that explicitly and document the closest relevant CS concept.
