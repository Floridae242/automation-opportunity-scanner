# Privacy and Data Retention

## Data minimization
Collect only process information needed for assessment. Avoid requesting personal data when role-level information is sufficient.

## Configurable policies for production
- source document retention period;
- generated analysis retention;
- audit retention;
- export retention;
- organization deletion/closure behavior;
- model-provider data region/control requirements.

## Logging
Do not log full source documents or secrets by default. Log identifiers, sizes, states, error classes, timings, and redacted metadata.

## User-visible transparency
The UI should state what content is sent for AI processing and when an assessment is AI-generated vs human-reviewed.
