# Zero-to-Build Learning Roadmap

## Stage 1 — Web basics (1–2 focused days)
Understand HTTP, JSON, REST, client/server, Git branches/commits, environment variables. Exercise: create a form that POSTs JSON to a mock endpoint.

## Stage 2 — Frontend
Learn React components/state, Next.js routing, TypeScript types, forms, async server state. Exercise: build Process Intake UI from static data.

## Stage 3 — Backend
Learn Python typing, FastAPI routes/dependencies, Pydantic validation, error handling. Exercise: CRUD process in memory, then PostgreSQL.

## Stage 4 — Database
Learn tables, PK/FK, indexes, transactions, migrations, tenant scoping. Exercise: create project/process/process_version and query only current org.

## Stage 5 — AI integration
Learn model request, structured outputs, schema validation, retries, prompt versioning. Exercise: free text -> valid `process.schema.json` using a fake provider first, then a real model.

## Stage 6 — Domain logic
Implement deterministic scoring and ROI as pure tested functions. Exercise: run known test vectors and explain every point.

## Stage 7 — Visualization
Learn React Flow nodes/edges. Exercise: render and edit a 5-step reviewed process.

## Stage 8 — Testing/security/deployment
Write unit/integration/E2E; test cross-tenant access; deploy staging; add telemetry.

## Learning principle
Never learn the entire stack before building. Learn the minimum concept, build one vertical slice, test it, then continue.
