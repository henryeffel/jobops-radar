# Backend Concepts

## FastAPI App Instance

`FastAPI()` creates the application object used by the ASGI server. It owns route
registration, application metadata, dependency wiring, and OpenAPI generation.
JobOps Radar currently creates one app instance in `app/main.py`.

## Route Handler

A route handler is a Python function registered for an HTTP method and path.
FastAPI converts its return value into an HTTP response and uses type hints to
support validation and documentation.

## Health Check Endpoint

`GET /health` provides a small availability signal. The current endpoint checks
that the application can receive and answer requests; it does not yet probe the
database or external services. Keeping this distinction clear prevents a shallow
health check from being mistaken for full dependency readiness.

## Swagger and OpenAPI Documentation

FastAPI derives an OpenAPI schema from routes and type information. Swagger UI
at `/docs` renders that schema as interactive API documentation. This reduces
manual documentation drift but does not replace endpoint tests.

## Environment-Based Configuration

`pydantic-settings` loads configuration from environment variables and an
optional `.env`, validates types, and exposes a typed settings object. This keeps
deployment-specific values and secrets out of application logic. The cached
`get_settings()` function avoids rebuilding settings repeatedly.

## Database Session

A SQLAlchemy session represents a unit of database work. It tracks ORM objects,
coordinates queries and changes, and controls transaction boundaries. The
`get_db()` generator ensures a request receives a session that is closed after
use.

## SQLAlchemy Engine and Session Factory

The engine owns dialect and connection-pool behavior for a database URL. It does
not represent one permanent connection. `SessionLocal` is a configured factory
that creates individual sessions bound to that engine.

## Alembic Migration Foundation

Alembic versions database schema changes. Its environment imports SQLAlchemy
metadata and uses the same `DATABASE_URL` as the application. The foundation is
ready, but no revision exists because there are no models yet.

## Pytest API and Database Testing

FastAPI's test client sends HTTP-style requests to the application without
starting a separate server. Assertions verify response status and payload.
Database foundation tests verify URL wiring, session creation, and a real
temporary SQLite connection without requiring PostgreSQL.

## SQLAlchemy 2.0 Mapped Model

`JobPosting` uses `Mapped[...]` annotations and `mapped_column()` so Python types
and database columns are explicit. Required identity/display fields are
non-nullable, while provider-dependent metadata is optional. The model is
provider-neutral: `source="mock"` works before any external API integration.

## Database-Level Unique Constraint

The named unique constraint on `(source, external_id)` makes posting identity a
database invariant. It rejects duplicates even if concurrent code performs the
same import. A Python-side existence check alone cannot close that race.

## Portable JSON Payload

SQLAlchemy's generic `JSON` type stores unmodified provider or mock fields without
prematurely modeling every attribute. It maps to SQLite's JSON-capable storage
now and PostgreSQL JSON later. PostgreSQL-specific `JSONB` features are deferred
to preserve portability.

## Model Metadata Discovery

Each mapped model registers its table with `Base.metadata`. Alembic calls
`load_models()` before assigning `target_metadata`, ensuring autogenerate sees
`job_postings`. `alembic check` confirms the migration and model metadata do not
currently differ.

## Pydantic Persistence Schemas

`JobPostingCreate` validates and bounds external input before it reaches
SQLAlchemy. `JobPostingRead` enables `from_attributes`, converting a mapped ORM
instance into a stable response-ready data shape. These DTOs keep API/input
concerns separate from persistence state such as generated IDs and timestamps.

## Service Transaction Boundary

The job posting service owns the small create transaction: it checks identity,
adds the model, commits, rolls back on integrity failure, and refreshes generated
values. Keeping this sequence in one function prevents future route handlers
from duplicating database lifecycle code.

## Duplicate Error Translation

The service converts a known uniqueness conflict into
`DuplicateJobPostingError`. The custom exception does not depend on FastAPI, so
the API route can return the existing resource while service tests remain
framework-independent. Another client contract could translate the same
exception to HTTP `409 Conflict` without changing persistence code.

## APIRouter and HTTP Boundary

The JobPosting `APIRouter` groups related paths under `/job-postings` and is
registered once by the FastAPI app. Route handlers validate HTTP input, call the
service, translate missing data to `404`, and serialize `JobPostingRead`. They do
not contain SQLAlchemy query construction.

## FastAPI Database Dependency

Routes request a SQLAlchemy `Session` through `Depends(get_db)`. FastAPI resolves
the generator dependency per request and closes the session afterward. Route
tests replace only this dependency, allowing the real app and router to run
against an isolated in-memory SQLite engine.

## Create-or-Get HTTP Semantics

`POST /job-postings` returns `201 Created` when it inserts a row. If the same
source identity already exists, it returns that existing resource with `200 OK`
and the identical response schema. The database remains the final uniqueness
authority.

## OpenAPI Route Verification

FastAPI generates `/docs` from registered route metadata. The route test checks
the OpenAPI `paths` object directly, preventing a router-registration omission
from silently removing endpoints from documentation.

## Interview Review Questions

- What is the difference between an engine, connection, and session?
- Why should configuration come from the environment?
- What does a health endpoint prove, and what does it not prove?
- How does FastAPI generate `/docs`?
- Why are schema migrations preferable to manual production table changes?
- Why must duplicate prevention be enforced by the database?
- How does Alembic discover SQLAlchemy models?
- Why should a service exception remain independent from HTTP?
- Who owns commit and rollback in the current create workflow?
- How does dependency override isolate API tests from the local database?
- Why does duplicate POST return `200` while a new insert returns `201`?
