# Automation Opportunity Scanner — AI Build Pack v1

This repository is a **source-of-truth build pack** for an AI coding agent and a 4-person software team to design, implement, test, demo, deploy, and later scale an Automation Opportunity Scanner.

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
- Version: 1.0.0
- Designed for: 18-day hackathon -> internship continuation -> production SaaS evolution
- Language: English technical source-of-truth with Thai-friendly notes in selected planning documents
- Generated: 2026-09-05
