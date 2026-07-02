# Carrot Identity Service Backend Case Study

## Purpose

This document records the first job-posting case study that will guide JobOps
Radar's domain roadmap. It is a concise engineering interpretation of the
posting, not an implementation claim or a verbatim archive of its text.

The current codebase does not contain Auth, OIDC, organization-account,
security-policy, audit-log, LLM, or high-availability features. Those concerns
remain future work that must be designed and tested separately.

## Posting Summary

### Identity/Auth Platform Backend

The role is centered on backend systems that provide identity and authentication
capabilities as a shared platform. This implies clear ownership boundaries for
identities, credentials, sessions, authorization context, and downstream
service integration.

### OIDC-Based Login Platform Direction

The platform direction includes OpenID Connect-based login. For JobOps Radar,
this is a future design input: issuer and client boundaries, authorization-code
flows, token validation, key rotation, redirect URI protection, and failure
handling must be understood before any endpoint is added.

### B2B Organization Account Modeling

The posting highlights business organization accounts rather than only
individual consumer accounts. A future model will need to distinguish users,
organizations, memberships, roles, invitations, and organization-scoped
authorization without assuming that one user belongs to only one organization.

### Security and Privacy

Identity data is security- and privacy-sensitive. Future work should minimize
stored personal data, define access and retention rules, protect secrets and
tokens, avoid leaking account existence, and produce reviewable security events.
These requirements should be backed by threat modeling and tests rather than
framework defaults alone.

### High Availability

An identity platform is a dependency for many other services, so availability
and predictable failure behavior matter. Relevant future concerns include
redundancy, stateless request handling where appropriate, database failure
modes, safe retries, key availability, monitoring, and recovery objectives.
JobOps Radar does not yet claim production high availability.

### Authentication UX

Authentication quality includes the user-facing failure and recovery path, not
only protocol correctness. Login, consent, account linking, organization
selection, session expiry, and recovery should be secure while remaining clear
to users. API error contracts and observability will need to support that
experience.

### AI-Assisted Engineering Workflow Culture

The posting signals a culture that uses AI-assisted engineering workflows.
Within JobOps Radar, AI may later help extract structured requirements or draft
analysis, but generated output must remain reviewable. Deterministic validation,
tests, source evidence, and human approval should protect core security and
scoring decisions.

## How This Guides JobOps Radar

The case study supplies a coherent target domain for later portfolio extensions:

- JD requirements can capture OIDC, B2B account modeling, privacy, reliability,
  authentication UX, and engineering-culture signals.
- Candidate evidence can be compared with each requirement independently.
- Skill gaps can explain both missing implementation knowledge and missing
  operational/security evidence.
- Preparation roadmaps can sequence protocol study, data modeling, threat
  modeling, testing, and operations work.
- Future Auth, OIDC, and AuditLog features can be justified by explicit case
  study requirements rather than added as generic portfolio checkboxes.

## Scope Boundary

This documentation does not authorize or implement:

- Auth or user models
- OIDC endpoints or identity-provider integration
- LLM calls
- AWS deployment resources
- production availability claims

The next implementation step should remain in the core analysis domain: store
structured, manually curated JD requirements for a posting, with schemas,
migrations, services, and tests. Auth/OIDC design can follow after the analysis
model establishes why those capabilities are relevant.
