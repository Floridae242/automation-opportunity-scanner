# Component Design

## Frontend feature modules
`projects`, `process-intake`, `process-review`, `process-map`, `analysis`, `opportunities`, `portfolio`, `reports`, `settings`.

Each module owns UI components, types derived from API contracts, query/mutation hooks, and feature tests. Shared design-system components must not know domain-specific business rules.

## Backend modules
- identity/organizations: auth context, membership, RBAC.
- projects/processes: lifecycle and versioning.
- analysis: job orchestration and AI run metadata.
- ai_gateway: provider adapters and prompt/schema versions.
- scoring: pure deterministic functions.
- recommendations: taxonomy/rule normalization + narrative generation.
- reports: immutable report snapshots.
- audit: append-only event records.

## Dependency direction
Routes depend on use cases/services; services depend on domain + repository interfaces; infrastructure adapters implement repositories/providers. Scoring/domain logic must not import web framework or AI SDK types.
