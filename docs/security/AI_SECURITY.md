# AI Security Controls

## Prompt injection
Separate instructions from untrusted process/document content; delimit data; require structured output; do not expose tools that can write to external systems; adversarially test injection strings.

## Sensitive disclosure
Minimize context, redact where appropriate, use provider configurations approved for the customer, avoid raw document logging, and prevent cross-tenant retrieval/context construction.

## Improper output handling
Treat output as untrusted. Validate schemas and identifiers; escape UI text; never execute generated HTML/SQL/shell/code.

## Excessive agency
The MVP has no autonomous action tools. Future tools require explicit server authorization and narrowly scoped capabilities.

## Cost/DoS
Input size limits, per-tenant quotas, token limits, bounded retries, queue concurrency limits, cancellation, and usage telemetry.
