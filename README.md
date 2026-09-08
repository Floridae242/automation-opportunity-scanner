# Automation Opportunity Scanner — AI Build Pack v1

This repository contains the source-of-truth build pack and a runnable MVP for an Automation Opportunity Scanner. It is ready for local development, automated verification, and a demo deployment.

## Product in one sentence
Turn a business-process description into a reviewed process model, pain-point analysis, ranked automation opportunities, technology recommendations, explainable scores, ROI estimates (when evidence exists), and an executive report.

## Non-negotiable product principles
1. **Human review before scoring.** LLM extraction is a draft, not ground truth.
2. **Deterministic scoring.** The LLM does not invent or directly choose the final numerical score.
3. **Evidence over guessing.** Missing business data stays `null`; confidence decreases instead of fabricating values.
4. **Explainability.** Every recommendation must show the evidence, rule, and score contribution behind it.
5. **Security by default.** Treat uploaded process documents as sensitive enterprise data.
6. **Multi-tenant ready.** Core entities carry `organization_id` from the beginning.
7. **MVP first.** Build an Opportunity Discovery Platform, not a full RPA/orchestration engine.

## Recommended MVP stack
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Process visualization: React Flow (`@xyflow/react`)
- Backend: FastAPI + Pydantic
- Database: PostgreSQL
- Async jobs: Redis-backed queue (optional during hackathon; required before long-running production jobs)
- File storage: S3-compatible object storage
- AI: provider abstraction; OpenAI Responses/Structured Outputs is a supported implementation
- Tests: Pytest, Vitest, Playwright
- Observability: OpenTelemetry + error tracking
- Local environment: Docker Compose

## Run locally

Use Node 24, Python 3.12, and Docker Desktop. From the repository root:

```bash
npm ci
python3.12 -m venv apps/api/.venv
apps/api/.venv/bin/pip install -r apps/api/requirements-dev.lock
apps/api/.venv/bin/pip install --no-deps -e apps/api
cp .env.local.example .env
```

Set the same local password in `POSTGRES_PASSWORD` and `DATABASE_URL` in `.env`, then start PostgreSQL and migrate it:

```bash
npm run db:up
(cd apps/api && .venv/bin/alembic upgrade head)
```

Run the API and web application in separate terminals:

```bash
npm run dev:api
npm run dev
```

Open <http://127.0.0.1:3000>, register a local organization, and begin a project assessment. Full commands and environment notes are in [LOCAL_DEVELOPMENT.md](docs/devops/LOCAL_DEVELOPMENT.md).

## MVP status

The implemented flow includes organization-scoped authentication, project and process intake, untrusted UTF-8/PDF document ingestion, review-gated AI extraction, deterministic opportunity scoring, recommendations and ROI scenarios, a portfolio view, report snapshots, and PDF export. CI runs formatting, static checks, PostgreSQL integration tests, offline AI evaluation, browser tests, build verification, and dependency audits.

The default AI provider is deterministic demo extraction. Configure `AI_PROVIDER=openai_compatible` with `AI_BASE_URL`, `AI_API_KEY`, and `AI_MODEL` only in an approved environment for live-provider testing. Provider-neutral production setup is documented in [PRODUCTION_RUNBOOK.md](docs/devops/PRODUCTION_RUNBOOK.md).

## Start here — AI coding agent
Read in this order:
1. `MASTER_INSTRUCTIONS.md`
2. `AGENTS.md`
3. `AI_BUILD_MANIFEST.yaml`
4. `PROJECT_CONTEXT.md`
5. `docs/requirements/SRS.md`
6. `docs/requirements/BUSINESS_RULES.md`
7. `docs/domain/PROCESS_ANALYSIS_KNOWLEDGE.md`
8. `docs/domain/AUTOMATION_TAXONOMY.md`
9. `docs/domain/OPPORTUNITY_SCORING_MODEL.md`
10. `docs/architecture/SYSTEM_ARCHITECTURE.md`
11. `docs/data/DATABASE_SCHEMA.md`
12. `docs/ai/AI_SYSTEM_DESIGN.md`
13. `docs/testing/DEFINITION_OF_DONE.md`
14. `docs/project-management/BACKLOG.md`

## Start here — beginner developer
Read `docs/learning/ZERO_TO_BUILD_ROADMAP.md`, then follow `docs/devops/LOCAL_DEVELOPMENT.md` and the milestone order in `AI_BUILD_MANIFEST.yaml`.

## Scope boundary
This pack defines how to **discover and prioritize automation opportunities**. It does not instruct the application to automatically execute high-impact business actions, move money, modify ERP records, or operate customer systems without separate authorization, controls, and integration projects.

## Pack status
- Version: 1.0.0 MVP
- Designed for: 18-day hackathon -> internship continuation -> production SaaS evolution
- Language: English technical source-of-truth with Thai-friendly notes in selected planning documents
- Updated: 2026-09-08
