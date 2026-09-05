# Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Scope creep | High | Critical | P0 freeze, cut order, daily demo |
| LLM hallucination | High | High | null policy, schemas, review gate, evals |
| Inconsistent structured output | Medium | High | structured outputs + validation + bounded retry |
| Weak business data | High | High | missing-data UI, confidence, scenarios |
| Cross-tenant bug | Medium | Critical | tenant repository pattern + integration tests |
| Prompt injection | Medium | High | trust boundary, adversarial eval, no agent write tools |
| Deployment failure | Medium | High | deploy early, Day 17 freeze |
| External model outage/rate limit | Medium | Medium | fake/manual fallback, retries, quota telemetry |
| Team bottleneck | Medium | High | vertical ownership + code review + shared contracts |
| Demo network issue | Medium | High | seeded demo, resilient staging, fallback material |
