# Load Test Plan

## Goals
Establish a baseline and discover bottlenecks; not to claim internet-scale capacity.

## Scenarios
1. 50 concurrent users browsing dashboard/project/process CRUD.
2. 20 concurrent process-review editors with normal optimistic/concurrency rules.
3. Burst of 100 analysis submissions to validate queue/backpressure using fake AI latency.
4. Portfolio with 1,000 opportunities and realistic filters/sorts.

## Metrics
P50/P95/P99 latency, error rate, CPU/memory, DB connections/slow queries, queue wait, worker throughput.

## Safety
Use fake/model-stub inference for most load tests. Real provider testing respects rate limits and budget; do not generate wasteful traffic.
