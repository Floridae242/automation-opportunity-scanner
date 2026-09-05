# AI Evaluation Plan

## Evaluation sets
- `evals/golden_dataset.json`: normal representative processes.
- `evals/adversarial_inputs.json`: prompt injection, missing data, contradictions, noisy text.

## Metrics
- step boundary F1;
- actor/system extraction accuracy;
- evidence-reference validity;
- pain-point recall and precision (human labeled);
- automation-category precision;
- unsupported claim rate;
- schema-valid rate;
- null/unknown correctness;
- prompt-injection instruction-following escape rate;
- latency and cost per analysis.

## Release gate
A new prompt/model must not materially regress critical fields, unsupported claims, schema reliability, tenant/privacy behavior, or adversarial safety. A faster/cheaper model is not accepted solely for cost savings if quality crosses the defined threshold.
