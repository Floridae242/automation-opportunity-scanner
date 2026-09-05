# Data Dictionary — Important Fields

- `review_status`: draft | reviewed | superseded.
- `integration_status`: unknown | evidence_of_api | no_practical_api | manual_only | mixed.
- `source_type`: user_input | questionnaire | document | reviewer_edit | system_measurement.
- `confidence`: low | medium | high for qualitative fields; 0–100 for aggregate assessment confidence.
- `opportunity.status`: candidate | validated | rejected | planned | implemented (future tracking).
- `analysis_run.status`: queued | running | needs_review | completed | failed | cancelled.
- `scoring_version`: immutable configuration ID, e.g., `aos-score-v1`.
- `prompt_version`: immutable prompt ID + version.
- `snapshot_json`: report facts frozen at publish time; never the only copy of normalized domain records.

## Units
Store durations in minutes, monetary amounts with ISO currency, periodic frequencies with explicit period, percentages as decimal 0–1 internally.
