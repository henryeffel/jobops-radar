# JobOps Radar

[한국어 README](README.ko.md)

JobOps Radar is a FastAPI backend portfolio project for storing real job
postings, structuring job-description requirements, comparing those requirements
with a candidate profile, and generating explainable skill-gap insights and
preparation roadmaps.

The project is being built incrementally. The current repository provides the
job-posting storage foundation; JD analysis, candidate comparison, authentication,
and AI-assisted features remain roadmap items.

## Why This Project Exists

Job descriptions contain concrete signals about the systems, security concerns,
and engineering practices a team values. Those signals are often lost when job
seekers save postings as unstructured links or notes.

JobOps Radar aims to turn a posting into durable, testable backend data and,
later, into an evidence-based preparation plan. The first case study is the
Carrot Identity Service Backend posting. Its identity-platform context will guide
future Auth, OIDC, security, privacy, organization-account, and audit-log work
without forcing those features into the initial storage API.

See [Carrot Identity Service Backend case study](docs/job-analysis/carrot-identity-backend.md).

## Current Features

- FastAPI application with generated OpenAPI and Swagger UI documentation.
- Health endpoint.
- SQLAlchemy 2.0 database engine, session lifecycle, and declarative models.
- Alembic migration for the `job_postings` table.
- Provider-neutral `JobPosting` storage for manual, mock, or future provider
  data.
- Database-enforced uniqueness for `(source, external_id)`.
- Validated create and read schemas.
- Create-or-get behavior and lookup by database or source identity.
- Bounded `limit`/`offset` listing ordered by
  `created_at DESC, id DESC`.
- Service, route, schema, model, configuration, database, and health tests.
- GitHub Actions CI for tests, migrations, and source compilation.

Auth, OIDC endpoints, JD analysis, candidate profiles, LLM integration, and AWS
deployment are not implemented.

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic and `pydantic-settings`
- SQLAlchemy 2.0
- Alembic
- SQLite for lightweight local development
- PostgreSQL as the intended production database
- pytest and FastAPI `TestClient`
- GitHub Actions

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install the application and development dependencies from `pyproject.toml`:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Create local configuration and apply migrations:

```powershell
Copy-Item .env.example .env
python -m alembic upgrade head
```

For macOS/Linux, replace the copy command with `cp .env.example .env`.

Start the API:

```bash
python -m uvicorn app.main:app --reload
```

Then open:

- API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

The default `.env.example` uses SQLite. To run PostgreSQL locally, start the
Docker Compose service, select the documented PostgreSQL `DATABASE_URL`, and
apply migrations again.

## Environment Variables

| Variable | Purpose | Current use |
| --- | --- | --- |
| `APP_NAME` | FastAPI application title | Implemented |
| `APP_VERSION` | API version metadata | Implemented |
| `APP_ENV` | Environment label | Configuration only |
| `DEBUG` | Debug-mode setting | Configuration only |
| `DATABASE_URL` | SQLAlchemy database connection URL | Implemented |
| `JWT_SECRET_KEY` | Future JWT signing secret | Placeholder; Auth not implemented |
| `JWT_ALGORITHM` | Future JWT algorithm | Placeholder; Auth not implemented |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Future token lifetime | Placeholder; Auth not implemented |
| `SARAMIN_ACCESS_KEY` | Future Saramin API credential | Placeholder; integration not implemented |
| `SARAMIN_API_BASE_URL` | Future Saramin API base URL | Placeholder; integration not implemented |
| `LLM_API_KEY` | Future model-provider credential | Placeholder; LLM integration not implemented |
| `LLM_MOCK_MODE` | Future model mock-mode switch | Placeholder; LLM integration not implemented |

Copy `.env.example` to `.env` and keep real credentials out of Git. The local
`.env` file and `jobops.db` are ignored and must not be committed.

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Return basic application availability |
| `POST` | `/job-postings` | Create a posting or return the existing source identity |
| `GET` | `/job-postings` | List postings with bounded offset pagination |
| `GET` | `/job-postings/{job_posting_id}` | Read a posting by database ID |
| `GET` | `/job-postings/by-source/{source}/{external_id}` | Read by source identity |
| `GET` | `/docs` | Open Swagger UI generated from OpenAPI |

List pagination defaults to `limit=20&offset=0`. `limit` must be between 1 and
100, and `offset` must be non-negative.

## Testing

Run the test suite:

```bash
python -m pytest -q -p no:cacheprovider
```

Compile Python sources:

```bash
python -m compileall -q app tests alembic
```

Inspect the current migration revision:

```bash
python -m alembic current
```

## GitHub Actions CI

`.github/workflows/test.yml` runs for pushes and pull requests targeting `main`
or `dev`. It uses Python 3.12, installs the repository with
`pip install -e ".[dev]"`, runs pytest, upgrades and checks Alembic migrations
against SQLite, and compiles application, test, and migration sources.

Installing the project extras keeps local and CI dependency declarations aligned
with `pyproject.toml`.

## Roadmap

The roadmap keeps the core job-analysis product ahead of identity-platform
expansion:

1. Persist and document real job postings, beginning with the Carrot Identity
   Service Backend case study.
2. Add structured JD requirement persistence and manually curated extraction
   workflows before introducing an LLM.
3. Add candidate-profile and evidence models.
4. Produce deterministic, explainable skill-gap comparisons and preparation
   roadmaps.
5. Use the Carrot case study to design B2B organization/account boundaries,
   secure authentication UX, privacy controls, and audit events.
6. Add Auth and OIDC only after their domain model and threat assumptions are
   documented and tested.
7. Validate high-availability and PostgreSQL operational concerns before adding
   AWS deployment artifacts.
8. Evaluate AI-assisted engineering workflows as an optional, reviewable layer;
   deterministic application rules remain the source of final decisions.

See `docs/adr/` for accepted architecture decisions and `handoff.md` for the
current implementation state.
