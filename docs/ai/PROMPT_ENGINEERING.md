# Prompt Engineering Standard

## Prompt anatomy
- Role and task.
- Trust boundary: supplied process text is data, not instructions.
- Allowed inference rules.
- Explicit unknown/null policy.
- Output schema contract.
- Domain taxonomy references.
- Evidence/reference requirement.
- Negative instructions for common failure modes.

## Versioning
Every production prompt has `prompt_id`, semantic `version`, change note, owner, and evaluation result. Persist the version with every AI run.

## Change procedure
1. Create new prompt version.
2. Run golden + adversarial evals.
3. Compare accuracy, unsupported claims, schema success, latency, cost.
4. Review regressions.
5. Promote or reject.
6. Never mutate a historical prompt version in place.

## Prompt rule
Do not ask the LLM to “calculate an opportunity score”. Ask it to extract evidence/classifications that deterministic code uses.
