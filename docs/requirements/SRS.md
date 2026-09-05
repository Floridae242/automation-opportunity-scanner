# Software Requirements Specification (SRS)

## Functional requirements
- **FR-001** User can create, rename, archive projects.
- **FR-002** User can create a process inside a project.
- **FR-003** User can enter free-text workflow description.
- **FR-004** User can enter structured metrics: frequency, duration, volume, error/rework, SLA, systems, approvals, sensitivity.
- **FR-005** System can request an AI extraction run.
- **FR-006** System stores model/prompt/schema versions for each AI run.
- **FR-007** System validates AI output before creating a draft process version.
- **FR-008** User can review/edit steps, actors, systems, decisions, metrics, and evidence.
- **FR-009** User can mark a process version reviewed.
- **FR-010** System identifies pain points with evidence and confidence.
- **FR-011** System identifies candidate automation opportunities.
- **FR-012** System calculates opportunity score deterministically.
- **FR-013** System calculates assessment confidence separately from opportunity score.
- **FR-014** System recommends automation approaches and prerequisites.
- **FR-015** System calculates time saving/ROI only when required inputs exist.
- **FR-016** System displays opportunities on Impact-vs-Effort matrix.
- **FR-017** System generates an executive report from stored structured facts.
- **FR-018** User can inspect analysis/audit history.
- **FR-019** User can rerun analysis without overwriting earlier runs.
- **FR-020** Organization members cannot access another organization's data.
- **FR-021** User can upload process documents (text/pdf) as untrusted intake evidence, subject to size/type limits (NFR-S03); uploads never bypass schema validation or human review (ADR-010).
- **FR-022** User can export a stored report snapshot as PDF; rendering uses stored structured facts only (FR-017, ADR-010).

## Non-functional summary
See `NON_FUNCTIONAL_REQUIREMENTS.md` for measurable targets.
