# ADR 0005: Use Deterministic Fit Scoring

## Status

Accepted, implementation pending

## Context

Job fit scores must be explainable, reproducible, and testable. Direct LLM
scoring can vary with prompts, models, and repeated calls.

## Decision

Use an LLM or mock analyzer only to extract structured JD signals. Validate those
signals, then calculate the final fit score with deterministic application code
and documented weights.

## Consequences

### Positive

- Identical validated inputs produce identical scores.
- Weighting, caps, missing values, and tie-breaking can be unit-tested.
- Score explanations can identify contributing factors.

### Negative / Trade-offs

- Rules and weights require explicit design and calibration.
- Structured extraction errors can still affect the deterministic result.
- The approach may capture less nuance than unconstrained model judgment.

## Alternatives Considered

- Ask an LLM to return the final numeric score.
- Use embeddings and a vector database for similarity scoring.
- Manually score every posting.

## Related Documents

- [CS/DSA concepts](../learning-notes/cs-dsa-concepts.md)
- [JobOps answer bank](../interview-prep/jobops-answer-bank.md)
- [ADR 0002](0002-backend-first-mvp.md)
