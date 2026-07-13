# Backend Interview Question Map

This map connects common backend interview areas to concrete JobOps Radar
decisions. It distinguishes demonstrated work from planned discussion so an
interview answer does not claim unimplemented experience. Statuses reflect the
repository after the internal Identity/Auth and AuditLog slice was added.

## Status Legend

- **Implemented**: present in the repository and testable now.
- **Planned**: relevant to the MVP or a clear next production step.
- **Optional later**: useful only after scale or operational evidence justifies
  the added complexity.
- **Out of scope for v1**: intentionally excluded from the backend MVP.

## Database / Indexing

### Why this group matters

Indexes and schema design determine whether reads remain predictable as data
grows. They also impose write, storage, and maintenance costs, so the correct
answer starts from query patterns rather than adding indexes speculatively.

### JobOps Radar connection

Imported postings will need identity lookup, filtering, and time-based ordering.
User-job fit data may later require joins and composite lookup paths.
PostgreSQL's default B-Tree indexes fit equality, range, and ordering queries.
Hash indexes support equality only and are unlikely to be the first choice.

| Interview topic | Project-specific angle | Status |
| --- | --- | --- |
| B-Tree vs Hash index | The unique `(source, external_id)` identity and current lookup indexes use B-Tree; consider Hash only after an equality-only workload is measured | Partially implemented |
| Covering index | A composite index with included display columns could avoid heap reads for a proven hot listing query, but should follow `EXPLAIN ANALYZE` evidence | Optional later |
| Normalization vs denormalization | Normalize stable entities and relationships first; duplicate selected display fields only if measured read pressure justifies consistency costs | Planned |
| N+1 query problem | Use explicit eager loading or projection for related company/skill data once relationships exist; confirm query counts in integration tests | Planned |

`JobPosting`, `JobRequirement`, `User`, and `AuditLog` models now exist. Unique
and lookup indexes cover known identity and relationship queries, but production
index claims still require PostgreSQL query-plan evidence.

## Transactions / Concurrency

### Why this group matters

Concurrent imports can race, produce duplicates, or overwrite newer state.
Transactions define atomic boundaries; isolation and locking determine what
concurrent work can observe and modify.

### JobOps Radar connection

The first concrete concurrency risk is importing the same Saramin posting more
than once. A database unique constraint must enforce identity, while idempotent
upsert logic handles retries. Application-only "check then insert" logic is not
safe under concurrent workers.

| Interview topic | Project-specific angle | Status |
| --- | --- | --- |
| Isolation, Repeatable Read, MVCC | PostgreSQL MVCC provides consistent snapshots; default Read Committed is likely sufficient for simple imports, with stronger isolation chosen only for a demonstrated invariant | Planned |
| Concurrency control and locking | Let uniqueness constraints arbitrate duplicate imports; keep transactions short and avoid broad explicit locks | Planned |
| Optimistic vs pessimistic lock | Optimistic version checks fit rare profile/roadmap conflicts; row locks fit short, high-contention critical sections only | Optional later |
| Duplicate prevention | A unique provider/external-ID constraint arbitrates duplicates; the service catches conflicts and returns the existing record | Implemented locally |

SQLite cannot validate PostgreSQL's full MVCC and locking behavior. Concurrency
claims require PostgreSQL integration tests after Docker is available.

## API Design

### Why this group matters

Stable request and response contracts let clients distinguish success,
validation failures, missing resources, upstream failures, and retryable errors.

### JobOps Radar connection

The API will expose imported job metadata, enrichment inputs, deterministic fit
scores, and generated portfolio artifacts. Responses should use typed Pydantic
schemas, correct status codes, consistent error bodies, and pagination metadata.

| Interview topic | Project-specific angle | Status |
| --- | --- | --- |
| REST response design | Resource schemas, `201`, `404`, `409`, `422`, and a deliberately uniform `401` login failure are exercised by route tests | Partially implemented |
| External API failure mapping | Apply timeouts and bounded retries internally; expose a controlled `502`/`503` rather than leaking Saramin client details | Planned |
| API documentation | FastAPI-generated OpenAPI and Swagger UI at `/docs` document current routes | Implemented |

Internal authentication responses are now implemented for register, login, and
current-user lookup. Authorization roles, organization membership, token
revocation, and OIDC remain outside the demonstrated scope.

## Testing

### Why this group matters

Tests provide different confidence at different costs. Unit tests isolate rules
quickly; integration tests verify framework, database, and external boundaries.
A healthy suite needs both rather than treating the labels as interchangeable.

### JobOps Radar connection

Current tests cover health, settings, engine/session wiring, posting and
requirement behavior, Identity/Auth success and failure paths, JWT validation,
and security audit events using isolated SQLite databases. Future deterministic
scoring needs focused unit tests, while repositories and migrations still need
PostgreSQL integration tests.

| Interview topic | Project-specific angle | Status |
| --- | --- | --- |
| Unit vs integration test | Pure scoring and normalization functions belong in unit tests; API, repository, and migration behavior need integration tests | Partially implemented |
| Test isolation | Temporary SQLite avoids shared local state, but cannot replace PostgreSQL compatibility tests | Implemented locally; PostgreSQL planned |
| CI test execution | GitHub Actions runs tests, SQLite migration checks, and source compilation; a PostgreSQL service container remains planned | Partially implemented |

## Caching / Rate Limiting

### Why this group matters

Caching reduces latency and upstream load but introduces staleness and
invalidation problems. Rate limiting protects capacity and respects upstream
quotas. Both require explicit keys, ownership, and failure behavior.

### JobOps Radar connection

Repeated read-heavy job searches or reference data could eventually benefit from
cache-aside Redis caching. Saramin import endpoints may need quota-aware rate
limits. Neither is justified in the current single-process MVP.

| Interview topic | Project-specific angle | Status |
| --- | --- | --- |
| Redis cache and consistency | Cache derived/read results with TTL and versioned keys; keep PostgreSQL as source of truth and invalidate after writes | Optional later |
| Rate limiting | Apply per-client or per-user token-bucket limits to expensive imports and generation endpoints; coordinate limits in Redis only when multiple instances exist | Optional later |
| Cache failure behavior | Treat cache as an optimization: fall back to the database and observe errors without corrupting source data | Optional later |

Redis is intentionally not part of v1.

## Scaling / Operations

### Why this group matters

Production engineering requires evidence-driven diagnosis, safe delivery, and
repeatable incident handling. Scaling the wrong layer before measuring it adds
cost without improving reliability.

### JobOps Radar connection

Likely bottlenecks include slow external API calls, LLM analysis latency, missing
database indexes, connection-pool pressure, and CPU-heavy scoring batches.
Metrics should separate those stages before any scaling decision.

| Interview topic | Project-specific angle | Status |
| --- | --- | --- |
| Server bottleneck diagnosis | Measure latency percentiles, throughput, error rate, CPU/memory, DB queries/pool, and upstream timing before changing architecture | Planned |
| CI/CD | Test on pull requests, build one artifact, run migrations safely, deploy, perform a health check, and support rollback | Planned |
| Incident response | Detect, contain, communicate, restore, then write a blameless review with corrective actions | Optional later |
| MSA | Keep a modular monolith for v1; split only when ownership, scaling, or deployment boundaries become real | Out of scope for v1 |

## Architecture / Refactoring

### Why this group matters

Clear responsibilities reduce coupling and make business rules independently
testable. Refactoring should respond to concrete pressure, not create layers
before behavior exists.

### JobOps Radar connection

As routes grow, HTTP concerns should stay in routers, orchestration in services,
persistence in repositories, external calls in clients, and deterministic
scoring in a pure domain module.

| Interview topic | Project-specific angle | Status |
| --- | --- | --- |
| Service refactoring and SRP | Identity and Audit use router/service/repository boundaries; older posting code retains its existing layered structure | Partially implemented |
| Dependency inversion | A provider protocol isolates fixture ingestion from the pending Saramin implementation; analyzer interfaces remain future work | Partially implemented |
| MSA boundary decisions | Preserve internal module boundaries first; do not introduce network boundaries for portfolio optics | Out of scope for v1 |

The application now uses service and repository boundaries where identity,
audit, and persistence responsibilities justify them. It does not add layers to
pure functions or create network boundaries for appearance.
