# Product Backlog

## Completed P0 — Demo critical
- EPIC-01 Foundation and CI
- EPIC-02 Auth + organization tenant scope
- EPIC-03 Project/process intake
- EPIC-04 Structured AI extraction
- EPIC-05 Review + process map
- EPIC-06 Pain points/opportunities
- EPIC-07 Deterministic scoring + confidence
- EPIC-08 Recommendation + ROI scenarios
- EPIC-09 Portfolio matrix/dashboard
- EPIC-10 Executive report
- EPIC-11 Intake document upload (untrusted parsing) + PDF export of report snapshots (FR-021/FR-022, ADR-010)
- EPIC-12 E2E + AI eval + deploy

## Completed P1
- Comments and process-version comparison
- DOCX and slides exports
- Immutable, configurable scoring weights

## Completed P2
- Read-only integration catalog
- Organization member administration and audit explorer
- Benefit realization tracking after implementation
- OIDC configuration status and deployment handoff

## Remaining external dependency
- Full OIDC sign-in requires an issuer, client ID, client secret, redirect URI, and provider verification. See `docs/devops/SSO_SETUP.md`.

## Vertical-slice ordering
Never leave “frontend done, backend later” for critical flows. Each P0 epic should reach UI -> API -> DB -> test before moving on.
