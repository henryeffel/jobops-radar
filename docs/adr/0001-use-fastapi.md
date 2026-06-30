# ADR 0001: Use FastAPI

## Status

Accepted

## Context

JobOps Radar is a Python backend portfolio project that needs typed APIs, quick
iteration, and clear API documentation.

## Decision

Use FastAPI as the HTTP framework. Use its type-driven validation, dependency
system, OpenAPI schema, and Swagger UI at `/docs`.

## Consequences

### Positive

- Fits the target Python/FastAPI backend role.
- Produces interactive API documentation with little extra setup.
- Integrates directly with Pydantic settings and future schemas.

### Negative / Trade-offs

- Async performance is not automatic; blocking dependencies still require care.
- Framework convenience does not replace explicit service boundaries or tests.

## Alternatives Considered

- Flask: smaller core, but more manual validation and API documentation.
- Django REST Framework: mature and comprehensive, but heavier than this MVP.

## Related Documents

- [Backend concepts](../learning-notes/backend-concepts.md)
- [JobOps answer bank](../interview-prep/jobops-answer-bank.md)
- `app/main.py`
