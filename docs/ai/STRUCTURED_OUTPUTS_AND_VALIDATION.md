# Structured Outputs and Validation

## Layers
1. Provider-level structured output / JSON schema where supported.
2. Application model validation (Pydantic/Zod/JSON Schema).
3. Semantic validation against current domain entities.
4. Business-rule validation.

## Semantic checks
- every edge source/target step exists;
- duration/frequency units are valid;
- percentages 0–1 or 0–100 consistently;
- model cannot create a reviewed flag;
- evidence references resolve;
- recommendation categories belong to taxonomy;
- no numeric ROI values without input provenance.

## Invalid output handling
Classify as transient/provider error, schema error, semantic error, or safety rejection. Retry only when it can plausibly help. Preserve failure telemetry and provide a user-safe retry/manual-edit path.
