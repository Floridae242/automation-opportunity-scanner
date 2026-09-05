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
