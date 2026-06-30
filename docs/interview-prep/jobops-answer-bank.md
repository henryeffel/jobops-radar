# JobOps Radar Answer Bank

These answers are project-specific speaking notes, not scripts to memorize. State
what exists now first, then explain the next production step without presenting
planned work as complete.

## Why use FastAPI?

I chose FastAPI because JobOps Radar is an API-first Python backend and benefits
from typed request/response validation, dependency injection, and automatic
OpenAPI documentation. The current `/health` route and `/docs` already
demonstrate the basic contract. Pydantic integrates naturally with the typed
settings and future schemas. FastAPI also keeps the MVP small: I can add routers
and dependencies as behavior appears without adopting a large framework
structure prematurely.

The choice does not make blocking work automatically scalable. Database and
external client behavior still need deliberate sync/async decisions, timeouts,
pool sizing, and measurement.

## How are tests structured?

The suite currently has three focused areas:

- API tests use FastAPI's test client to verify `/health` status and payload.
- Settings tests verify defaults and environment-variable type conversion.
- Database foundation tests verify engine URL wiring, session creation, and a
  real temporary SQLite connection.

This is a small integration-oriented foundation. When deterministic scoring is
added, its rules should be pure unit tests with boundary and tie cases. Repository
and migration behavior should be tested against PostgreSQL in CI because SQLite
does not reproduce all PostgreSQL semantics. Tests must remain isolated and must
not depend on a developer's persistent `jobops.db`.

## Why use SQLite fallback now and PostgreSQL later?

Docker Desktop is not installed, so SQLite removes an infrastructure blocker and
lets me validate SQLAlchemy sessions and Alembic wiring locally. It is explicitly
a temporary development fallback, not a change in the production design.

PostgreSQL remains the target because the project will need stronger production
concurrency behavior, constraints, indexing tools, and realistic transaction
semantics. SQLite differs in typing, locking, and concurrent write behavior, so
I plan PostgreSQL integration tests before relying on those properties.

## Where would indexes be needed?

I would derive indexes from actual access paths after defining the model. The
first likely index is a unique composite key such as `(source, external_id)` to
support idempotent imports. Listing endpoints may need B-Tree indexes such as
`(status, posted_at DESC)` or filters involving company and import time.

I would inspect generated SQL and use PostgreSQL `EXPLAIN ANALYZE` before adding
covering or specialized indexes. Every extra index consumes storage and slows
writes, so I would not index every filterable column by default. Hash indexes are
unlikely to be the initial choice because B-Tree supports equality as well as
range and ordering queries.

## How would duplicate job postings be prevented?

The database should own the final invariant. I would normalize the provider name
and external posting ID, then add a unique constraint on that pair. Import logic
would use an atomic insert/upsert in a short transaction so retries are
idempotent.

A prior `SELECT` followed by `INSERT` is insufficient because two workers can
both observe absence and race. The unique constraint resolves that race even if
application checks fail. Payload changes for an existing external ID would
update allowed fields according to an explicit freshness rule.

## Why not use LLM direct scoring?

Direct LLM scoring is hard to reproduce, calibrate, explain, and regression-test.
The same profile and posting could receive different numbers after a prompt or
model change, which weakens user trust and makes interview claims about scoring
quality difficult to defend.

In JobOps Radar, the LLM or mock analyzer should only extract structured signals
from job text. Pydantic validation constrains that output, and deterministic code
computes the final weighted score. This makes weights, missing values, caps, and
tie-breaking explicit and testable. The mock mode also keeps tests and local
development independent of a paid external API.

## How would Redis caching be added later?

I would add Redis only after metrics show repeated expensive reads or external
requests. A cache-aside design could cache stable job-search results or reference
data using normalized, versioned keys and short TTLs. PostgreSQL would remain the
source of truth.

Reads would check Redis, fall back to the database or upstream service, and fill
the cache. Writes would commit to PostgreSQL first and then invalidate relevant
keys. Cache failures should degrade to the source system rather than fail core
reads. I would monitor hit rate, latency, stale-data tolerance, and memory before
tuning TTLs. Redis is intentionally excluded from v1.

## How would rate limiting be added later?

I would first identify the resource being protected: Saramin quota, LLM cost, or
application capacity. Limits should be stricter on import and generation routes
than on cheap reads. Before authentication, an edge or middleware limit could
use client IP with proxy headers configured safely; after authentication, a
user/API-client key is more meaningful.

A single instance could use an in-process limiter, but multiple instances need a
shared atomic store such as Redis. Token bucket is a good default because it
allows controlled bursts. Responses should return `429`, a retry signal, and
observable limit metrics. This remains optional until the relevant endpoints and
traffic exist.

## How would the service be refactored if it grows?

I would keep the v1 as a modular monolith. When route handlers begin mixing HTTP,
business rules, persistence, and upstream calls, I would separate:

- routers for HTTP validation and response mapping;
- services for use-case orchestration;
- repositories for SQLAlchemy queries;
- clients for Saramin and LLM boundaries;
- pure domain modules for normalization and deterministic scoring.

That applies SRP at real change boundaries and enables unit testing without
inventing interfaces for code that does not exist. I would split into
microservices only if independent ownership, deployment, or scaling needs
justify network and operational complexity.

## How would this project handle external API failures?

The Saramin client should set explicit connection and response timeouts, classify
errors, and retry only transient failures such as selected `5xx`, `429`, or
network errors. Retries should be bounded, use exponential backoff with jitter,
and respect `Retry-After`. Import writes must be idempotent so a retry cannot
create duplicate postings.

Permanent validation or authentication errors should fail fast. The API should
translate upstream failure into a controlled application error such as `502` or
`503` without exposing credentials or raw provider details. Structured logs and
metrics should include upstream latency, error category, retry count, and a
correlation ID. Existing imported data should remain usable when a fresh import
fails. A circuit breaker is a later option if sustained failures create retry
storms; it is unnecessary in the current skeleton.
