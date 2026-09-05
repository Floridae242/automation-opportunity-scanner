# Observability, Backup, and Recovery

## Telemetry
Request ID, tenant ID (non-sensitive identifier), route, status, latency; analysis state duration; model provider/model, latency, usage/cost estimate, validation failures; queue depth; DB latency/slow queries; report failures.

## Alerts
Sustained 5xx, queue backlog, analysis failure spike, DB saturation, model quota/rate limit, cross-tenant authorization anomaly, backup failure.

## Backup
Managed PostgreSQL point-in-time recovery where available; object-storage versioning/lifecycle as appropriate; periodic restore test. A backup that has never been restored is not considered proven.

## Incident minimum
Identify scope, stop harmful behavior, preserve logs, rotate affected secrets, restore service safely, communicate impact, document root cause and preventive actions.
