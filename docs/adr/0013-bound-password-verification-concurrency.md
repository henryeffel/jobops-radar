# ADR-0013: Bound concurrent password verification

## Status

Accepted

## Context

A normal-login k6 baseline on one small EC2 instance caused repeated Linux OOM
kills. Kernel logs showed the JobOps Python process at approximately 685 MB RSS
before a kill. Clients observed EOF errors, and systemd repeatedly restarted the
process while sustained login traffic continued.

Argon2 verification is intentionally memory intensive. Allowing the server's
thread pool to run an unbounded number of verifications concurrently therefore
makes aggregate memory demand unsafe on this host.

## Decision

Use a small, process-local bounded concurrency guard around password
verification only. It defaults to two concurrent operations and waits at most
three seconds. A wait timeout produces a generic HTTP 503 response and a
credential-free warning log. Semaphore release is guaranteed with `finally`.

This mitigation is selected before changing Argon2 parameters because changing
password hashing needs a separate security decision and migration analysis. It
is selected before scaling EC2 because it directly bounds the resource-intensive
operation while preserving the modular monolith. No external coordination
dependency or new service is required.

The guard is process-local because the current deployment is a modular monolith
and the immediate failure is within one Python process. A threading semaphore is
independent of an event loop and easy to unit test.

## Consequences and trade-offs

Memory-intensive work per process is bounded, but excess login requests wait and
may receive 503. This exchanges peak throughput and tail latency for predictable
per-process concurrency. Database lookup, audit handling, and token creation are
not serialized by this guard.

Every worker and instance owns a separate guard. This is not a deployment-wide
limit: potential concurrency equals the configured limit times the worker and
instance count. Future multi-worker or multi-instance deployments must size that
aggregate explicitly or adopt coordinated admission control in a separate
decision. This guard is not rate limiting and does not prevent pressure outside
password verification.

## Alternatives considered

1. Change Argon2 hashing parameters.
2. Scale the EC2 instance vertically.
3. Add distributed admission control.
