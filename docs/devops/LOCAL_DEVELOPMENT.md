# Local Development

## Prerequisites
Git, Node.js current LTS, Python 3.12+ compatible with chosen dependencies, Docker Desktop/Engine, package managers (pnpm/npm and uv/pip), and an AI API key only for real-provider testing.

## Recommended local services
Docker Compose: PostgreSQL, Redis, local S3-compatible storage. Run frontend and backend with hot reload outside containers for fast iteration.

## Environment variables
Copy `.env.example` to local secret files. Never commit real values.

## First milestone verification
- frontend loads;
- API `/health/live` and `/health/ready` work;
- DB migration succeeds;
- test organization/user seed succeeds;
- CI commands can run locally;
- AI provider can be replaced by a deterministic fake fixture.

## Beginner rule
Build/test with fake AI first. Add live model calls only after the domain schema and validation path works.
