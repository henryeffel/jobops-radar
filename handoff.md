# Handoff

## Current state

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
- No migration revisions or database models exist yet.
- No authentication, database models, or Saramin integration has been added.

## Verification

- `python -m pytest -q`: 7 passed, including a real temporary SQLite connection.
- `python -m alembic upgrade head --sql`: passed with the SQLite URL in offline
  SQL mode.
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
pytest
```

If pytest fails on Windows with `PermissionError: [WinError 5] Access is denied`
for the system pytest temp directory, use a repository-local temp directory in
PowerShell:

```powershell
mkdir .tmp_pytest
$env:TMP = "$PWD\.tmp_pytest"
$env:TEMP = "$PWD\.tmp_pytest"
pytest
```

The `.tmp_pytest/` directory is ignored by Git.

## Next recommended task

Define the first small domain model and generate its initial Alembic revision.
Keep authentication separate, and replace the development-only JWT placeholder
before authentication is implemented or deployed.

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
