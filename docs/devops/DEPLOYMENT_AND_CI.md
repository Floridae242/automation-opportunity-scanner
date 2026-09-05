# Deployment and CI/CD

## CI stages
1. install with lockfiles;
2. format/lint;
3. typecheck;
4. unit tests;
5. integration tests with ephemeral Postgres;
6. OpenAPI/JSON schema validation;
7. build frontend/backend images;
8. dependency/security scan;
9. E2E on preview/staging for release branches.

## Deployment
Frontend can use a managed Next.js platform; backend/worker as containers; PostgreSQL/Redis/object storage managed. Staging and production use separate credentials/data.

## Migration policy
Run backward-compatible migrations before new app version where possible. Destructive changes use expand/migrate/contract. Backup/rollback steps are documented for release.

## Release metadata
Store commit SHA, app version, scoring version, and prompt/schema versions in diagnostics so an analysis can be reproduced.
