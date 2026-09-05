# Incident Response Runbook

1. Detect/triage: severity, affected tenants/features, security/privacy potential.
2. Contain: disable affected path, pause worker/model calls, revoke/rotate credentials if needed.
3. Preserve evidence: logs, request IDs, deployment SHA, prompt/model versions.
4. Recover: rollback/forward fix, restore data only when integrity requires it.
5. Validate: tenant authorization, critical E2E, queue consistency, monitoring.
6. Communicate through approved stakeholder channel.
7. Post-incident: timeline, root cause, contributing factors, actions, owners, due dates.

Never expose another tenant's data while diagnosing an incident.
