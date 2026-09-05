# AI System Design

## Pipeline
1. Intake normalization.
2. Optional safe document text extraction.
3. Process extraction model call -> strict structured schema.
4. Schema and semantic validation.
5. Human review/correction.
6. Pain-point + candidate opportunity analysis.
7. Rule normalization and deterministic scoring.
8. Recommendation generation constrained by taxonomy and evidence.
9. Report narrative generated from stored structured facts, never as the source of truth.

## Provider adapter
Expose internal methods such as:
- `extract_process(input, schema_version)`
- `analyze_pain_points(process_version)`
- `suggest_opportunities(process_version, taxonomy_version)`
- `draft_report(analysis_run)`

Provider-specific request/response types remain inside adapter modules.

## Reliability controls
- structured outputs;
- bounded retries for transient failures;
- timeout and cancellation;
- prompt/schema/model version persistence;
- idempotency key for analysis request;
- semantic validators (e.g., referenced step IDs must exist);
- confidence and “unknown” fields;
- fallback to manual intake when model unavailable.
