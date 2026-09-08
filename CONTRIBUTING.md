# Contributing

Thank you for improving the Automation Opportunity Scanner.

## Local setup

Use Node 24, npm 11, Python 3.12, and Docker. Follow the [local development guide](docs/devops/LOCAL_DEVELOPMENT.md) to install dependencies, configure a local `.env`, start PostgreSQL, and apply migrations.

## Working agreement

- Keep every user-visible flow tenant-scoped and authenticated.
- Treat uploaded documents and process descriptions as untrusted and sensitive input. Do not add them to fixtures, logs, commits, or issue reports.
- Keep AI output review-gated and validate it against the schema before storage or scoring.
- Preserve deterministic scoring and show the evidence behind a recommendation.
- Do not commit `.env` files, API keys, database URLs, exports, or browser traces containing user data.

## Before opening a pull request

Run the checks that cover your change:

```bash
npm run format:check
npm run lint
npm run typecheck
npm run test:coverage
apps/api/.venv/bin/ruff check apps/api
apps/api/.venv/bin/ruff format --check apps/api
(cd apps/api && .venv/bin/mypy && .venv/bin/pytest)
npm run test:e2e
```

For a new behavior, add a focused unit or integration test. Add a Playwright test when the change affects a critical browser flow. Keep coverage at or above the configured 80% threshold.

## Pull request expectations

Describe the user-facing behavior, include validation evidence, and call out migrations, environment changes, or data-retention effects. Keep commits focused and use conventional prefixes such as `feat:`, `fix:`, `docs:`, or `test:`.
