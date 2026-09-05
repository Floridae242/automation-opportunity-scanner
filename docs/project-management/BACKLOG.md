# Product Backlog

## P0 — Demo critical
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

## P1
Comments; compare process versions; additional export formats (DOCX/slides); configurable scoring weights.

## P2
Integration catalog; SSO; enterprise administration; benefit realization tracking.

## Vertical-slice ordering
Never leave “frontend done, backend later” for critical flows. Each P0 epic should reach UI -> API -> DB -> test before moving on.
