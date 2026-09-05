# Model Provider Strategy

## Principles
- Configure model IDs through environment/config, not hard-coded domain logic.
- Capability-test structured output and required context size.
- Maintain a default model, optional economical model, and controlled fallback path.
- Capture per-run provider, model, latency, token/usage metadata, prompt version, and schema version.
- Do not silently switch provider for sensitive tenants if data policy differs.

## Model selection by task
Extraction benefits from reliable structured output and instruction following. Narrative report drafting can use a lower-cost model if evals pass. Deterministic calculations remain outside models.

## Upgrade checklist
Run regression evals, compare cost/latency, inspect failure examples, verify data controls, update configuration and decision log.
