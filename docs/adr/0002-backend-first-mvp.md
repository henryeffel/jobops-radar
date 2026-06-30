# ADR 0002: Build a Backend-First MVP

## Status

Accepted

## Context

The MVP must be deployable before 2026-07-24 and is intended to demonstrate
Python backend skills. Expanding backend and UI scope together would threaten
delivery.

## Decision

Complete and deploy the backend workflow before adding any user interface.
Prioritize API contracts, persistence, integrations, scoring, tests, and
operations.

## Consequences

### Positive

- Keeps effort aligned with the target backend role.
- Reduces scope and makes backend behavior independently testable.
- Improves the chance of delivering a coherent deployed MVP.

### Negative / Trade-offs

- The MVP has no polished end-user interface.
- API behavior must be demonstrated through `/docs`, tests, and examples.

## Alternatives Considered

- Build frontend and backend in parallel.
- Create a thin UI before core persistence and scoring are stable.

## Related Documents

- [Work summary](../work-summary.md)
- [ADR 0006](0006-delay-frontend.md)
- [Session logs](../session-logs/2026-06-29.md)
