# RBAC Policy v1

## Roles
- Owner: organization ownership, members, settings, all project actions.
- Admin: member/settings management except ownership-sensitive actions; all project actions.
- Analyst: create/edit process data, start analyses, create reports.
- Reviewer: read/edit draft process facts and approve reviewed versions; cannot manage org.
- Viewer: read reviewed/published analysis and reports.

## Enforcement
Authorization is evaluated server-side using authenticated user + active organization membership + resource tenant ownership + action. UI permissions are convenience only.

## Sensitive actions
Membership changes, retention/deletion settings, export administration, and future external-system integrations require elevated roles and audit events.
