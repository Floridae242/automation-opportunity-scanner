# Security Architecture

## Assets
Sensitive business-process descriptions, documents, systems/integration details, employee roles, operational metrics, reports, model prompts/config, credentials, audit records.

## Controls
Authentication; server-side RBAC; tenant scoping; TLS; encryption at rest through managed services; secret manager/runtime secrets; signed object access; file type/size controls; rate limits; audit logging; dependency scanning; safe output encoding; backups; deletion/retention workflows.

## AI trust boundary
User documents are untrusted data. Model responses are untrusted data until validated. LLMs receive only the minimum necessary context. Provider data controls must be reviewed before production customer use.

## Document upload
Allowlist supported types, validate MIME/signature where practical, set size/page limits, isolate parsing, scan as required by deployment environment, and never execute embedded macros/scripts.
