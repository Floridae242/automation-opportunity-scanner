# Production Runbook

## Before release

Set runtime secrets through the deployment platform: `DATABASE_URL`, `AI_PROVIDER`, `AI_BASE_URL`, `AI_API_KEY`, and `AI_MODEL`. Do not copy values into Compose files, logs, or tickets. Validate only their shape with `python3 scripts/check-production-config.py`.

Run backward-compatible migrations before starting the new API image. Confirm `/health/live` returns `ok` and `/health/ready` returns `ready`. If readiness fails after a migration, stop rollout, retain logs without document content, and restore the prior image; do not downgrade a destructive migration without a tested restore plan.

## Data handling

Keep staging and production databases, object storage, and AI credentials separate. Uploaded documents are untrusted evidence: restrict access through tenant-scoped API routes, retain according to the customer policy, and never place raw document content in logs or audit metadata.

## Evidence

Record the release image digest, commit SHA, migration head, prompt/schema version, and scoring version in the deployment record. Test backup restoration periodically rather than relying only on backup completion status.
