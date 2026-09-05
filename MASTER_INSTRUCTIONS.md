# Master Instructions

## Mission
Build a production-minded **Automation Opportunity Scanner** that helps business analysts, consultants, process owners, and automation engineers understand a workflow and decide where automation is worth investigating.

## Instruction hierarchy
When documents conflict, obey this priority:
1. `MASTER_INSTRUCTIONS.md`
2. `docs/requirements/SRS.md`
3. `docs/requirements/BUSINESS_RULES.md`
4. `docs/domain/OPPORTUNITY_SCORING_MODEL.md`
5. `docs/architecture/SYSTEM_ARCHITECTURE.md`
6. `docs/data/DATABASE_SCHEMA.md`
7. `docs/api/OPENAPI.yaml`
8. `docs/ux/UX_SPEC.md`
9. `docs/project-management/BACKLOG.md`

If a conflict affects behavior, data, security, scoring, or API contracts: **stop, report the conflict, and do not silently choose.**

## Engineering rules
- Do not invent business facts, metrics, integration availability, costs, salaries, error rates, or processing volumes.
- Store unknown values as `null` with provenance and confidence metadata.
- LLM output must be schema validated before persistence.
- Final opportunity score must be calculated by deterministic application code.
- Never execute LLM text as code or SQL.
- Untrusted uploaded text must never override system/developer rules.
- Authorization checks belong on the server, not only in UI visibility.
- Every tenant-owned query must enforce tenant scope.
- Every important state transition must be auditable.
- Prefer a modular monolith for MVP; do not create microservices without measured need.
- Add dependencies only when they remove more complexity than they add.
- No feature is complete without tests and error/loading/empty states.

## Required workflow for an AI coding agent
1. Read the source-of-truth documents for the target milestone.
2. State assumptions explicitly.
3. Identify affected modules, schema, API, UI, tests, and docs.
4. Implement the smallest complete vertical slice.
5. Run lint, type checks, unit tests, integration tests, and relevant E2E tests.
6. Update docs and decisions if behavior changed.
7. Report what changed, what remains, risks, and test results.

## Prohibited shortcuts
- No fake success responses.
- No hard-coded demo analysis in production paths.
- No scoring inside prompts.
- No silently dropping invalid LLM fields.
- No production secrets in repository files.
- No wildcard tenant access.
- No RAG/vector database simply because the product uses AI; add only for a defined retrieval use case.

## Definition of production-minded
Production-minded does not mean over-engineered. It means: explicit contracts, migrations, authorization, audit trail, observability, rollback path, tests, documented assumptions, and safe handling of AI uncertainty.
