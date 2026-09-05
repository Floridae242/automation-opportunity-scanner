# Opportunity Scoring Model v1

## Final score
Each dimension is normalized to 0–100.

`score = 0.20*business_value + 0.20*time_saving + 0.15*repetitiveness + 0.15*feasibility + 0.10*error_reduction + 0.10*integration_ease + 0.10*risk_safety`

Where `risk_safety = 100 - implementation_risk`.

## Dimension anchors
### Business value
0 = negligible local convenience; 50 = meaningful team benefit; 100 = strategic/customer/compliance/large cost impact.

### Time saving
Derived from evidence when possible. 0 = no meaningful saving; 100 = substantial recurring effort removal relative to current process.

### Repetitiveness
0 = rare/unique cases; 100 = highly standardized, frequent repeated work.

### Feasibility
0 = major unknowns/constraints; 100 = clear inputs, stable systems, known implementation path.

### Error reduction
0 = no quality benefit; 100 = major preventable rework/error/control improvement.

### Integration ease
0 = inaccessible/unstable systems; 100 = well-defined supported interfaces and data contracts.

### Implementation risk
0 = low risk; 100 = high security/compliance/change/operational risk. Converted to risk safety before weighting.

## Missing values
Never silently substitute 0 or 50. Compute:
- `dimension_score`: only from reviewed facts/rules;
- `coverage`: weighted fraction of evidence-complete dimensions;
- `assessment_confidence`: evidence completeness + source quality + human review status.

A final score may be shown only when required minimum fields are reviewed. Otherwise show a provisional range or “insufficient evidence”.

### Confidence formula (`aos-confidence-v1`, ADR-011)
`assessment_confidence = 0.45*dimension_coverage + 0.35*source_quality + 0.20*review_status`
- `dimension_coverage`: percent of the 7 dimensions computable from reviewed facts (0–100).
- `source_quality`: mean over cited facts — user-entered 100, AI-extracted with evidence quote 70, AI-inferred without quote 40.
- `review_status`: 100 if the process version is marked reviewed, else 0.

### Final-score gate (ADR-011)
- **Final:** all 7 dimensions non-null AND process version reviewed.
- **Provisional:** `dimension_coverage >= 60` → show the number labeled `provisional` with missing-field list.
- **Insufficient evidence:** `dimension_coverage < 60` → no number; show missing fields only.

## Priority bands
- 80–100: investigate now
- 65–79: high-priority candidate
- 50–64: evaluate with additional evidence
- <50: lower priority or redesign first

Bands are portfolio guidance, not guarantees.

### Governance review flag (ADR-008)
`governance_review = implementation_risk >= 70`. The flag is advisory and orthogonal to bands: any banded opportunity may carry it, recommending human approval/exception handling per BR-008.

## Portfolio matrix axes (ADR-008, `aos-portfolio-axes-v1`)
Impact-vs-Effort placement (FR-016) uses derived display axes, never a second total score:
- `impact = 0.45*business_value + 0.25*time_saving + 0.15*error_reduction + 0.15*strategic_alignment_input`
- `effort = 0.35*integration_complexity + 0.25*change_complexity + 0.20*security_compliance_effort + 0.20*exception_handling_complexity`

Inputs without reviewed evidence are `null`; the matrix cell then shows “insufficient evidence” instead of a guessed position. Axis-only inputs (strategic alignment, effort sub-factors) are collected at intake as optional facts and do not enter `aos-score-v1`.
