# CS and DSA Concepts

## Request-Response Lifecycle

An HTTP client sends a method, path, headers, and optional body. The ASGI server
passes the request to FastAPI, routing selects the matching handler, dependencies
are resolved, and the result is serialized into an HTTP response. The current
`/health` path is a minimal example of this pipeline.

## Test Assertion

An assertion states an expected invariant, such as status code `200` or a JSON
payload equal to `{"status": "ok"}`. A useful test isolates one behavior and
fails with evidence when the invariant is broken.

## Configuration Separation

Code defines how the system behaves; configuration selects environment-specific
values. Separating them lets the same code run locally and in production while
changing database URLs and secrets externally.

## Database Connection Lifecycle

Database work follows an acquire-use-release lifecycle. Engines manage reusable
connections, sessions define units of work, and context managers or generator
dependencies guarantee cleanup. Correct cleanup prevents connection leaks and
resource exhaustion.

## SQLite Fallback Trade-Off

SQLite is easy to run because it is file-based and requires no server. It speeds
up local development while Docker is unavailable. PostgreSQL remains necessary
for production parity because concurrency, typing, constraints, and SQL behavior
can differ. Tests passing on SQLite do not prove identical PostgreSQL behavior.

## Memoization and Cached Settings

`lru_cache` stores a function result by argument key. Since `get_settings()` has
no arguments, it behaves like a lazily initialized shared settings object. Lookup
after initialization is effectively constant time for this use.

## Composite Identity and Invariants

An external posting ID is unique only within its source, so the ordered pair
`(source, external_id)` forms the business identity. A composite unique
constraint encodes that invariant in the database while allowing different
providers to reuse the same external ID.

## Check-Then-Insert Race

An application that checks for a row and then inserts it performs two separate
operations. Concurrent transactions can both observe "not found" before either
insert commits. The database unique constraint serializes the final invariant:
one insert succeeds and the conflicting insert fails. No major DSA was added;
this is a concurrency and data-integrity concept.

## Future Concepts

### Hashing

Hash tables can provide average-case constant-time membership lookup. They will
be relevant when normalizing skills or checking whether a user has a required
signal.

### Set Intersection

Intersecting user skills with job requirements can identify matches without
nested scans. For sets of sizes `n` and `m`, expected work is approximately
`O(min(n, m))` membership checks after set construction.

### Sorting

Ranked job results will require sorting deterministic scores. Comparison sorting
is generally `O(n log n)`. Stable tie-breaking rules should be explicit so the
same inputs produce the same order.

### Weighted Scoring

A deterministic fit score can combine normalized components:

`score = skill_weight * skill_match + experience_weight * experience_match + ...`

Weights, ranges, missing-value behavior, and caps must be documented and tested.
The LLM may extract structured signals, but it must not directly assign the final
fit score.
