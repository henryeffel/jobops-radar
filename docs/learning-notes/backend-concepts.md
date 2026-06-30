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

## Interview Review Questions

- What is the difference between an engine, connection, and session?
- Why should configuration come from the environment?
- What does a health endpoint prove, and what does it not prove?
- How does FastAPI generate `/docs`?
- Why are schema migrations preferable to manual production table changes?
