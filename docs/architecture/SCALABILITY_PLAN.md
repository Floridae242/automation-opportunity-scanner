# Scalability Plan

## 1–100 active users
Single API instance or small replica set, PostgreSQL, direct model calls, basic object storage. Optimize developer speed.

## 100–1,000 active users
Async workers; DB connection pooling; proper indexes; cached read-heavy portfolio summaries; model rate-limit scheduler; job status events/polling.

## 1,000–10,000 active users
Horizontal API/worker scale; queue partitioning; database tuning/read replicas if measured; separate analytics workloads; stricter per-tenant quotas and cost controls.

## 10,000+
Re-evaluate service boundaries from telemetry. Consider regional/data-residency architecture, dedicated enterprise tenants, partitioning, and asynchronous event contracts.

## Always measure
P95/P99 API latency, queue depth, DB slow queries, connections, model latency/rate limits, object-storage throughput, analysis cost, per-tenant usage.
