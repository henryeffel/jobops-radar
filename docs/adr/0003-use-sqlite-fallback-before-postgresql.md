# ADR 0003: Use SQLite as a Temporary Local Fallback

## Status

Accepted, temporary

## Context

Docker Desktop is not installed, so local PostgreSQL is currently unavailable.
Database foundation work must continue without changing the production target.

## Decision

Use `sqlite:///./jobops.db` for temporary local development. Retain PostgreSQL
with Docker Compose as the default architecture and final deployment target.

## Consequences

### Positive

- Removes the immediate local infrastructure blocker.
- Supports SQLAlchemy, Alembic, and isolated connection tests.
- Requires no local database server.

### Negative / Trade-offs

- SQLite differs from PostgreSQL in typing, locking, concurrency, and SQL.
- SQLite tests cannot prove PostgreSQL transaction or index behavior.
- PostgreSQL integration testing is still required before deployment.

## Alternatives Considered

- Pause database work until Docker is installed.
- Install PostgreSQL directly on Windows.
- Change the final database to SQLite.

## Related Documents

- [Work summary](../work-summary.md)
- [Backend question map](../interview-prep/backend-question-map.md)
- `.env.example`
- `docker-compose.yml`
