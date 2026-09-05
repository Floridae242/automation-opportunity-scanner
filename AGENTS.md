# AGENTS.md — Coding Agent Operating Guide

## Before coding
Read `MASTER_INSTRUCTIONS.md` and `AI_BUILD_MANIFEST.yaml`. For the requested feature, also read its relevant requirements, domain rules, architecture, schema, API, UX, and tests.

## Work one milestone at a time
Do not implement later milestones merely because they seem convenient. Avoid broad refactors unless required by the current acceptance criteria.

## Preferred implementation style
- Frontend: feature-oriented components; typed API client; server state separated from UI state.
- Backend: router -> service/use-case -> repository/data access. Domain calculations are pure functions where possible.
- AI: provider adapter -> prompt/version -> structured schema -> validator -> normalized domain result.
- Database: migrations are append-only once shared; no manual production edits.

## Required validation after changes
- format/lint
- TypeScript typecheck
- Python static/type checks if configured
- backend unit/integration tests
- frontend unit tests
- relevant Playwright E2E flow
- JSON/YAML/OpenAPI schema validation

## Security reminders
Treat all user text and documents as untrusted. Never concatenate untrusted input into SQL, shell commands, HTML, or tool instructions. Do not expose model prompts, secrets, tokens, or cross-tenant records.

## AI-specific rule
If extracted values have no source evidence, return `null`; never make the UI look more certain than the evidence.
