# Multi-Tenancy

## Model
Shared application and database with strict row ownership by `organization_id` for v1. Enterprise deployment models can change later.

## Rules
- Never trust organization_id supplied by the client as authorization.
- Resolve authenticated user -> active membership -> server-side organization scope.
- Every repository/data-access method that touches tenant data requires tenant context.
- Foreign keys should prevent linking entities across organizations where practical.
- Consider PostgreSQL Row Level Security as defense-in-depth when production requirements justify it; application authorization remains explicit.
- Object-storage keys include tenant namespace but access must use signed/authorized server flows, not predictable public paths.
- Cross-tenant tests are mandatory for every new resource type.
