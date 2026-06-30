# ADR 0004: Use SQLAlchemy 2.0 and Alembic

## Status

Accepted

## Context

JobOps Radar needs database access that works with the SQLite fallback and the
PostgreSQL target, plus repeatable schema evolution.

## Decision

Use SQLAlchemy 2.0 style for engines, sessions, and ORM metadata. Use Alembic for
versioned schema migrations driven by the application's `DATABASE_URL`.

## Consequences

### Positive

- Provides explicit session and transaction boundaries.
- Supports both current and target database dialects.
- Makes schema changes reviewable, reproducible, and reversible.

### Negative / Trade-offs

- Adds ORM and migration concepts that must be maintained correctly.
- Cross-database support can hide dialect differences without PostgreSQL tests.

## Alternatives Considered

- Raw SQL without an ORM.
- SQLModel.
- Manual schema creation without migration history.

## Related Documents

- [Backend concepts](../learning-notes/backend-concepts.md)
- [ADR 0003](0003-use-sqlite-fallback-before-postgresql.md)
- `app/db/session.py`
- `alembic/env.py`
