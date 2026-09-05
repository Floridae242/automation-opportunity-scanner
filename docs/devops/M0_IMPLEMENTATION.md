# M0 — Running the foundation

Implementation started on 2026-09-05. The executable workspace lives alongside the original build-pack files. This milestone supplies a Next.js design shell, a FastAPI health service, PostgreSQL bootstrap migrations, a development seed, test-only AI seam, and local/CI checks. Identity authorization, process intake, AI extraction, scoring and reports are later milestones and are not implemented here.

## Local setup

Use Node 24/npm 11, Python 3.12, and Docker. Run from the repository root:

```bash
npm ci
python3.12 -m venv apps/api/.venv
apps/api/.venv/bin/pip install -r apps/api/requirements-dev.lock
apps/api/.venv/bin/pip install --no-deps -e apps/api
```

On a fresh checkout, copy `.env.local.example` to `.env`, replace both password placeholders with the same local password, and restrict file permissions. For this initial workspace a random local password was generated in the ignored `.env`; keep it private. Never overwrite an existing environment file during setup.

```bash
npm run db:up
cd apps/api
.venv/bin/alembic upgrade head
.venv/bin/python -m aos_api.seed
```

The seed creates only a clearly marked local organization, user and membership. It is idempotent, does not create login credentials, and is prohibited in production. M1 will establish authentication and authorization.

Start two terminals at the repository root:

```bash
# Terminal 1
npm run dev:api
```

```bash
# Terminal 2
npm run dev
```

Open <http://127.0.0.1:3000>. The overview, assessment guide and workspace-status pages work without a model API key. Status checks call FastAPI through a server-side route with a bounded timeout. There are no tenant data routes in M0.

| Service | Address |
| --- | --- |
| Web | `http://127.0.0.1:3000` |
| API liveness | `http://127.0.0.1:8000/health/live` |
| API readiness | `http://127.0.0.1:8000/health/ready` |
| Implemented API contract | `http://127.0.0.1:8000/openapi.json` |
| Project PostgreSQL | `127.0.0.1:55432` |

Liveness returns `{"status":"ok"}` independently of database availability. Readiness returns `{"status":"ready"}` only when PostgreSQL is reachable and the Alembic revision is current; otherwise it returns HTTP 503 and `{"status":"not_ready"}`. No credentials or database exceptions are returned.

The executable Compose file is `infra/compose.local.yaml`, with loopback-only exposure and runtime credentials. The original `docker-compose.yml` remains a source-pack example. Redis/object storage are deferred until a milestone uses them. `npm run db:stop` preserves the database volume.

## Checks

```bash
npm run format:check
npm run lint
npm run typecheck
npm run test:coverage
npm run build
apps/api/.venv/bin/ruff check apps/api
apps/api/.venv/bin/ruff format --check apps/api
cd apps/api
.venv/bin/mypy
.venv/bin/pytest
```

PostgreSQL integration tests require `TEST_DATABASE_URL` pointing to a **disposable database named with a `_test` suffix**, separate from the local `aos` database. They migrate up/down and test constraints; never point them at shared or production data. Supply credentials privately through the environment. CI provisions an ephemeral `aos_test` database and runs integration tests explicitly.

After a production web build and migration of the normal local database:

```bash
npx playwright install chromium
npm run test:e2e
```

Playwright starts its own API on 8100 and production web server on 3100, tests desktop/mobile navigation, service readiness and failure recovery, and writes `playwright-report/` and failure traces. These ports must be free. The development servers on 3000/8000 can remain running.

CI is defined in `.github/workflows/ci.yml`. It installs locked dependencies, checks lint/format/types, tests real PostgreSQL, validates implemented OpenAPI and JSON schemas, builds the web app, runs browsers, and scans dependencies. No remote workflow or deployment has been triggered by creating this file.

## Decisions and unresolved source conflicts

M0 uses the manifest's milestone order and the `/health/live` + `/health/ready` endpoints in `LOCAL_DEVELOPMENT.md`. The research report's `/healthz` is not exposed as a second API. Source-pack files remain intact; their original SHA-256 manifest describes the pack, not the new application.

The following work is deferred rather than silently combining incompatible specifications:

| Area | Conflict or missing contract | Resolve before |
| --- | --- | --- |
| Business API/data | Research uses assessments; domain/API spec uses projects/processes/versions. OpenAPI source lacks several path parameters and most bodies/responses. | M1/M2 business endpoints |
| Scoring | Research formula and priority bands differ from `aos-score-v1` in the domain specification. | M6 |
| Final-score eligibility | Minimum reviewed fields, exact normalization and assessment-confidence rules are not fully defined. | M6 |
| Review gate | Research includes confidence-based bypass examples; master instructions require human review before final scoring. | M3/M6 |
| Upload/export | Research treats upload and file exports as must-have; product/backlog defer parts of this scope. | M2/M8 |
| Process representation | Existing extraction schemas lack much of the documented decisions, edges and field-level provenance data. | M3/M4 |

No final scoring, business API, upload/export, or review bypass has been implemented. Resolve each affected contract explicitly before building its milestone, as required by `MASTER_INSTRUCTIONS.md`.
