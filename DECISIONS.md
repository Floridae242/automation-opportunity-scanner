# Architecture Decision Log

## ADR-001 — Modular monolith first
**Decision:** One backend deployable with clear modules.  
**Why:** Fast iteration and simple transactions matter more than independent scaling during MVP.  
**Revisit when:** measured load or team boundaries require independent scaling/deployment.

## ADR-002 — PostgreSQL as primary database
**Decision:** Relational source of truth with JSONB only for model/raw payload metadata.  
**Why:** Strong relations, transactions, auditability, indexing, and reporting.

## ADR-003 — Final score is deterministic
**Decision:** LLM may classify/extract evidence; application code calculates final scores.  
**Why:** Reproducibility, auditability, testability, explainability.

## ADR-004 — Human review gate
**Decision:** A process extraction must be reviewed or explicitly accepted before a final portfolio score is published.  
**Why:** Enterprise workflow descriptions are incomplete and LLM output is probabilistic.

## ADR-005 — Provider abstraction for AI
**Decision:** Domain code depends on an internal AI interface, not provider-specific SDK types.  
**Why:** Enables model upgrades, fallback, cost testing, and future provider change.

## ADR-006 — No vector database in MVP by default
**Decision:** Do not add embeddings/RAG until a concrete retrieval use case exists (e.g., enterprise automation pattern library).  
**Why:** Avoid unnecessary complexity and hidden retrieval quality problems.

## ADR-007 — API/workflow integration preferred over RPA
**Decision:** Recommendation rules prefer supported APIs and workflow engines; use RPA when UI automation is the justified practical path.  
**Why:** UI automation is typically more brittle than stable integration contracts.

## ADR-008 — Spec scoring model is canonical; research formulas become axes/flag
**Decision:** Resolve the C1 conflict (deep-research-report-2 vs docs/domain/OPPORTUNITY_SCORING_MODEL.md) in favor of the domain spec: `aos-score-v1` (7 weighted dimensions, bands 80/65/50) is the only final opportunity score. Report-2's Impact/Effort formulas are adopted, renamed `aos-portfolio-axes-v1`, as derived display axes for the Impact-vs-Effort matrix (FR-016) only. Report-2's `GOVERNANCE_REVIEW` is adopted as a boolean advisory flag set when `implementation_risk >= 70`, orthogonal to bands (supports BR-008). Report-2's P1/P2/P3/DEFER bands and its 5-dimension risk-penalty formula are rejected. `schemas/score.schema.json` and `evals/scoring_test_vectors.json` already pin `aos-score-v1` and are unchanged.  
**Why:** Instruction hierarchy (MASTER_INSTRUCTIONS) ranks domain spec above research reports; the machine-checkable layer (schemas, evals, manifest SHA) already encodes the spec formula, so adopting Report-2 would break 90/90 verified manifest artifacts.  
**Revisit when:** v2 weight recalibration with real portfolio data (must be a new version, per BR-012).

## ADR-009 — Resource naming follows OPENAPI, not the research sketch
**Decision:** The canonical API surface is `docs/api/OPENAPI.yaml` (projects → processes → analyses → opportunities; `/api/v1` base; health endpoints `/health/live` and `/health/ready`). Report-2's `assessments`-centric sketch and `/healthz`, `/v1/scoring`, `/v1/dashboard`, `/v1/assessments/*` routes are treated as superseded drafts.  
**Why:** Hierarchy ranks OPENAPI above research reports; M0 foundation code and contract tests already implement the OPENAPI model.  
**Revisit when:** A future multi-portfolio dashboard may add read-only aggregation endpoints (amend OPENAPI first).

## ADR-010 — File upload and PDF export are in MVP scope
**Decision:** User decision 2026-09-05: add document upload and PDF report export to MVP. New requirements: FR-021 (upload untrusted process documents per process, with size/type limits per NFR-S03, content extracted as untrusted intake evidence) and FR-022 (render a stored report snapshot as PDF). OPENAPI gains `POST /processes/{processId}/documents` and `GET /reports/{reportId}/pdf`. Uploads create intake evidence only; they never bypass schema validation, human review, or override system rules (MASTER_INSTRUCTIONS). PDF renders stored structured facts only; no live LLM calls during export (FR-017, DOMAIN_MODEL snapshot rule).  
**Why:** Report-2 marked upload/export as Must and the user confirmed; keeping NFR-S03's "uploaded content" guardrail meaningful requires an actual upload surface.  
**Revisit when:** Storage/quota costs or parser security findings suggest narrowing accepted types.

## ADR-011 — Deterministic confidence formula and final-score gate
**Decision:** Define previously unspecified terms in OPPORTUNITY_SCORING_MODEL.md as `aos-confidence-v1`:
- `assessment_confidence = 0.45*dimension_coverage + 0.35*source_quality + 0.20*review_status` (all components 0–100).
- `dimension_coverage` = percent of the 7 scoring dimensions computable from reviewed facts.
- `source_quality` = mean fact quality: user-entered 100, AI-extracted with evidence quote 70, AI-inferred without quote 40.
- `review_status` = 100 if the process version is marked reviewed, else 0.
- Final score requires all 7 dimensions non-null AND reviewed; otherwise: coverage ≥ 60 → labeled `provisional` score; coverage < 60 → `insufficient evidence` (no number).
Confidence remains independent of score (FR-013, BR-003); thresholds are versioned configuration.  
**Why:** The old wording ("required minimum fields", "evidence completeness + source quality + human review status") was not implementable deterministically; scoring is contract-affecting, so it was resolved by explicit decision, not silent choice.  
**Revisit when:** Eval metrics on real extractions suggest weights/threshold miscalibration (bump formula version).

## ADR-012 — Email+password with rotating DB sessions for MVP
**Decision:** M1 identity uses locally stored credentials: `users.password_hash` (scrypt N=16384,r=8,p=1, self-describing format) and server-side session records (`sessions` table, SHA-256 of a 256-bit cookie token, 7-day expiry, rotation on login and organization switch, revocation on logout/switch). Cookie: `aos_session`, HttpOnly, SameSite=Lax, Secure in production. `auth_subject` remains for future OIDC/SSO (P2) federation. Active organization lives on the session row, never on the client; switching requires proven membership (non-members receive a non-disclosing 404). Login failures are throttled in-process (10/min/email) with 429. `audit_logs` records register/login/login_failed/logout/organization_switched without credentials or protected data (NFR-S04).  
**Why:** The spec defined roles, membership, and `auth_subject` but no MVP login mechanism; the SSO-first alternative cannot satisfy the 18-day D3 auth target without an external IdP, and trusted-header mode is unsafe to expose directly. Password hashing uses the Python standard library only (no new dependencies, per MASTER rules).  
**Revisit when:** Enterprise SSO (P2) replaces local passwords; move auth_subject population to the OIDC claim and deactivate password_hash for federated users.

## ADR-013 — Intake tables and versioned draft semantics
**Decision:** M2 adds `projects`, `processes`, `process_versions` per DATABASE_SCHEMA plus one addition: `process_versions.metrics_json` (JSONB) carrying the FR-004 structured metrics with fixed keys (`frequency`, `duration_minutes`, `volume_per_period`, `error_rate`, `rework_rate`, `sla`, `systems`, `approvals_required`, `sensitivity`), each nullable — unknown stays null (BR-001), units per DATA_DICTIONARY. Intake saves create a new version (`version_no = max+1`) and mark the previous draft `superseded`; reviewed versions are immutable (DOMAIN_MODEL invariant). RBAC v1 mapping: all members read; owner/admin/analyst create and edit intake; only owner/admin archive or restore. Cross-tenant resource ids resolve to a non-disclosing 404. Creating a process inside an archived project returns 409.  
**Why:** DATABASE_SCHEMA listed intake-adjacent tables but no storage for structured metrics; JSONB with a validated fixed key set keeps ADR-002 (JSONB for metadata) while making FR-004 persistable and testable. Version-on-save preserves auditability without edit-in-place.  
**Revisit when:** M3 extraction review needs per-step metrics; promote step-level fields to their own tables then.
