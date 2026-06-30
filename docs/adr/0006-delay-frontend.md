# ADR 0006: Delay Frontend Development

## Status

Accepted

## Context

The portfolio targets backend roles, and the deadline requires strict scope
control. A frontend would add UI, state-management, and deployment work before
the backend workflow is proven.

## Decision

Do not build a frontend in v1. Use OpenAPI `/docs`, automated tests, and API
examples to demonstrate the backend.

## Consequences

### Positive

- Prevents scope creep.
- Keeps time focused on backend reliability and domain behavior.
- Avoids coupling an unstable API to an early UI.

### Negative / Trade-offs

- Non-technical users have no dedicated interface.
- Portfolio demonstrations rely more heavily on API documentation.

## Alternatives Considered

- Build a React or Next.js client alongside the API.
- Add a minimal server-rendered dashboard.

## Related Documents

- [ADR 0002](0002-backend-first-mvp.md)
- [Work summary](../work-summary.md)
- [Backend concepts](../learning-notes/backend-concepts.md)
