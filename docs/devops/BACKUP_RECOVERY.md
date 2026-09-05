# Backup and Recovery

## RPO/RTO starting targets for v1
Define with stakeholders before production. Suggested starting engineering target: RPO <= 24h for early pilot unless managed PITR provides better; RTO <= 4h. Do not present these as contractual SLOs without approval.

## Coverage
PostgreSQL, object storage, environment/config metadata needed for restore, and prompt/scoring versions stored in source control/database.

## Restore drill
At least quarterly for production-minded v1 or before major demo/launch: restore into isolated environment, validate tenant counts and referential integrity, open a report/process, and record elapsed time/issues.
