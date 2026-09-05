# Non-Functional Requirements

## Security
- NFR-S01: All tenant-owned server queries enforce organization scope.
- NFR-S02: Secrets are injected at runtime, never committed.
- NFR-S03: Uploaded content is treated as untrusted; parsing occurs with file limits and safe-type checks.
- NFR-S04: Authorization failures are logged without leaking protected data.

## Reliability
- NFR-R01: Invalid AI output must not become a published process version.
- NFR-R02: Analysis jobs are idempotent by request key where practical.
- NFR-R03: External AI timeouts and rate limits use bounded retry with jitter; no infinite retries.

## Performance targets for v1
- Standard CRUD P95 < 500 ms in normal load excluding network edge.
- Dashboard P95 < 1.5 s for portfolios under 1,000 opportunities with proper indexes.
- Long AI/document work handled asynchronously when > ~10 s expected.

## Maintainability
- Domain scoring functions have unit tests for boundary cases.
- API contract is versioned.
- Database changes use migrations.
- Prompt versions are immutable once used in a persisted analysis run.

## Accessibility
Core workflows should support keyboard navigation, visible focus, labels, semantic form errors, and readable contrast.
