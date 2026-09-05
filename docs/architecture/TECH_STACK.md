# Technology Stack

## Frontend
Next.js + TypeScript; Tailwind CSS; shadcn/ui; TanStack Query; React Hook Form + Zod; React Flow for process visualization; chart library for portfolio visuals.

## Backend
Python + FastAPI + Pydantic; SQLAlchemy/Alembic or equivalent explicit ORM/migrations. Python is selected because AI/data tooling and clear typed validation fit the domain.

## Data
PostgreSQL as source of truth. Redis for cache/job coordination only when needed. S3-compatible object storage for uploaded documents/exports.

## AI
Provider adapter with structured-output capability. Store prompts outside business logic; version prompts/schemas.

## Quality
Pytest; frontend unit runner; Playwright E2E; OpenAPI contract validation; dependency/security scanning in CI.

## Deployment
Frontend may deploy separately from API. API/worker run as containers. Use managed PostgreSQL and managed object storage in production. Avoid pinning this design to one cloud until internship/company requirements are known.
