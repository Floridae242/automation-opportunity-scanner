# Integration Architecture

## MVP integrations
AI provider, object storage, authentication provider, optional error/telemetry services. No customer-system write integrations.

## Future enterprise connectors
Treat ERP/CRM/DMS/workflow systems as separate connector projects. Connector contract should expose capabilities such as read metadata, list supported operations, connectivity evidence, and health—not give the LLM unrestricted credentials.

## Principle of least authority
If future tools are added, every tool has a narrow allowlisted action, explicit tenant context, server-side authorization, input schema, timeout, audit event, and confirmation policy for consequential writes.

## Recommendation vs execution
The Scanner may recommend “API integration” based on confirmed capability evidence. It must not automatically call that API simply because the model recommended it.
