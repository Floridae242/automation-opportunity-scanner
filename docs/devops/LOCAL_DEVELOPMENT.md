# Local Development

## Prerequisites
Git, Node 24, npm 11, Python 3.12, Docker Desktop/Engine, and an AI API key only for approved real-provider testing.

## Recommended local services
Docker Compose: PostgreSQL, Redis, local S3-compatible storage. Run frontend and backend with hot reload outside containers for fast iteration.

## Environment variables
Copy `.env.local.example` to `.env`, replace both local password placeholders with the same value, and never commit the resulting `.env` file. The default `AI_PROVIDER=demo` needs no API key.

## MVP verification
- register an organization and sign in through the frontend;
- create a project and process, then submit/review an intake;
- upload a bounded UTF-8 text or PDF document;
- inspect ranked opportunities, portfolio view, report snapshot, and PDF export;
- confirm API `/health/live` and `/health/ready`, migration, and local checks pass;
- use deterministic demo extraction before testing an approved live AI provider.

## Beginner rule
Build/test with fake AI first. Add live model calls only after the domain schema and validation path works.
