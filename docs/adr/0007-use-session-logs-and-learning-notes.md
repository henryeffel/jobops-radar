# ADR 0007: Require Session Logs and Learning Notes

## Status

Accepted

## Context

Codex is used heavily during development. Without durable records, implementation
reasoning, validation evidence, warnings, and learning outcomes can be lost
between sessions.

## Decision

Update `handoff.md` and a dated session log after every Codex task. Update the
work summary and topic-based learning notes when their content materially
changes.

## Consequences

### Positive

- Preserves project context and design reasoning.
- Supports interview review and learning.
- Makes validation history and unresolved issues visible.

### Negative / Trade-offs

- Adds documentation overhead to every task.
- Logs can drift unless they record actual results rather than intended work.

## Alternatives Considered

- Rely only on Git commit messages.
- Keep informal notes outside the repository.
- Generate documentation only at project completion.

## Related Documents

- [Session log template](../session-logs/2026-06-29.md)
- [Work summary](../work-summary.md)
- [Backend concepts](../learning-notes/backend-concepts.md)
- [CS/DSA concepts](../learning-notes/cs-dsa-concepts.md)
