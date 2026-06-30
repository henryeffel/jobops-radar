# Architecture Decision Records

ADRs preserve why JobOps Radar chose a direction, including trade-offs and
rejected alternatives. `Accepted` means the decision is active; it does not
necessarily mean every related feature is implemented.

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](0001-use-fastapi.md) | Accepted | Use FastAPI for the Python backend |
| [0002](0002-backend-first-mvp.md) | Accepted | Deliver a backend-first MVP |
| [0003](0003-use-sqlite-fallback-before-postgresql.md) | Accepted, temporary | Use SQLite locally until PostgreSQL is available |
| [0004](0004-use-sqlalchemy-and-alembic.md) | Accepted | Use SQLAlchemy 2.0 and Alembic |
| [0005](0005-use-deterministic-fit-scoring.md) | Accepted, implementation pending | Compute fit scores deterministically |
| [0006](0006-delay-frontend.md) | Accepted | Delay frontend development |
| [0007](0007-use-session-logs-and-learning-notes.md) | Accepted | Preserve session and learning records |
| [0008](0008-use-saramin-official-api-not-scraping.md) | Accepted, implementation pending | Use Saramin's official API, not scraping |

## Usage

- Add a new numbered ADR when a decision has meaningful long-term trade-offs.
- Do not rewrite an accepted ADR to hide history. Supersede it with a new ADR and
  link both records.
- Update status when a decision is deprecated or superseded.
- Link implementation pull requests, tests, and learning notes when available.
