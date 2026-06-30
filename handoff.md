# Handoff

## Current state

- Minimal FastAPI application initialized.
- `GET /health` returns `{"status": "ok"}`.
- Environment-based settings use `pydantic-settings`.
- Local PostgreSQL is configured through Docker Compose.
- No authentication, database models, or Saramin integration has been added.

## Verification

- `python -m pytest -q`: 1 passed.
- Python source compilation passed.
- Docker Compose runtime validation was skipped because Docker was not installed
  in the implementation environment.

## Run locally

```bash
python -m venv .venv
pip install -e ".[dev]"
docker compose up -d
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

## Next recommended task

Add the database session infrastructure and migration tooling (SQLAlchemy 2.x and
Alembic) without creating domain models yet.
