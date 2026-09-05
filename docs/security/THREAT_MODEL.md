# Threat Model

## Main threats
- Cross-tenant IDOR/broken access control.
- Prompt injection from process text/documents.
- Sensitive information disclosure to model/provider/logs.
- Improper model-output handling.
- Excessive agency if future tools are added.
- Malicious/oversized document upload.
- SQL/XSS/injection via user/model text.
- Stolen tokens/secrets.
- Queue abuse / denial-of-wallet through model calls.
- Audit-log tampering or missing traceability.

## Required mitigations
Explicit authorization per resource; tenant-scoped repositories; structured output + encoding; no model-generated executable actions; content limits; usage quotas; request IDs; immutable analysis metadata; safe logging/redaction; least privilege; dependency patching.

## AI security reference
Map controls to the current OWASP GenAI/LLM risk guidance during production security review, especially prompt injection, sensitive information disclosure, improper output handling, excessive agency, and supply-chain risks.
