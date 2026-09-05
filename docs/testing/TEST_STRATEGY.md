# Test Strategy

## Unit
Scoring dimensions, risk inversion, normalization, ROI formulas, confidence/coverage, business rules, parsers/validators.

## Integration
Database repositories with tenant scope; authorization; migrations; AI adapter using fixtures/fake provider; object storage adapter; queue idempotency.

## Contract
OpenAPI/schema compatibility and generated client types where used.

## E2E
Login -> create project -> intake -> AI fixture extraction -> review -> score -> opportunity detail -> report. Include missing-data and failed-analysis paths.

## AI eval
Golden and adversarial datasets run separately from deterministic unit tests; record model/prompt/schema version.

## Security
Cross-tenant resource IDs, role restrictions, XSS text rendering, upload boundaries, prompt injection tests, rate/usage limit behavior.

## Load
Baseline CRUD/dashboard and concurrent analysis-job submission; do not load-test the external model provider irresponsibly—mock/provider-limit aware.
