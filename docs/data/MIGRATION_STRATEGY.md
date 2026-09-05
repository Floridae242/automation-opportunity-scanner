# Database Migration Strategy

## Rules
- All schema changes through version-controlled migrations.
- Never edit a migration already applied to shared/staging/production environments.
- Prefer additive/backward-compatible changes.
- Destructive changes use expand -> backfill -> switch reads/writes -> verify -> contract.
- Large backfills run as resumable jobs, not request-time migrations.

## Required PR notes for schema changes
Migration name, affected tables, expected lock/runtime, rollback/forward-fix plan, index impact, tenant-scope impact, data backfill, and test evidence.

## Seed data
Development/demo seeds are deterministic and clearly marked. Production migrations never insert fake demo business records.
