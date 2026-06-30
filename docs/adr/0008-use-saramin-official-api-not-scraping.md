# ADR 0008: Use the Saramin Official API, Not Scraping

## Status

Accepted, implementation pending

## Context

JobOps Radar needs real job posting metadata. Scraping unauthorized job boards is
fragile, creates compliance concerns, and expands maintenance scope.

## Decision

Integrate only with the Saramin official Job Search API for v1 metadata imports.
Do not scrape Saramin pages or JobKorea, Wanted, LinkedIn, or other job boards.

## Consequences

### Positive

- Uses a documented and authorized integration boundary.
- Reduces breakage from webpage layout changes.
- Keeps provider scope and maintenance manageable.

### Negative / Trade-offs

- Data is limited by Saramin's API fields, availability, and quotas.
- Upstream outages and API changes still require defensive handling.
- JD enrichment may require explicit manual input when the API lacks text.

## Alternatives Considered

- Scrape multiple job boards.
- Use unofficial aggregators.
- Use only manually entered postings.

## Related Documents

- [Backend question map](../interview-prep/backend-question-map.md)
- [JobOps answer bank](../interview-prep/jobops-answer-bank.md)
- [ADR 0002](0002-backend-first-mvp.md)
