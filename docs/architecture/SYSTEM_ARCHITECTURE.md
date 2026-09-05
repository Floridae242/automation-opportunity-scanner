# System Architecture

## MVP logical architecture
Browser -> Next.js web app -> FastAPI API -> PostgreSQL

FastAPI -> AI provider adapter
FastAPI -> Object storage for source files
FastAPI -> Redis/queue worker for long-running analysis (can be synchronous behind an interface during earliest hackathon days)

Telemetry from web/API/worker -> OpenTelemetry/error tracking.

## Backend modules
identity, organizations, projects, processes, analysis, scoring, recommendations, reports, audit, files, ai_gateway.

## Key separation
- AI extraction produces candidate structured facts.
- Domain layer validates/normalizes facts.
- Scoring service calculates numbers.
- Report service reads persisted structured analysis.

## Scale evolution
Phase 1: one API + one DB.  
Phase 2: separate worker scale, managed Redis, object storage, read-optimized queries.  
Phase 3: only split services if independent scaling/security/team ownership is demonstrated.
