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

## Priority bands
- 80–100: investigate now
- 65–79: high-priority candidate
- 50–64: evaluate with additional evidence
- <50: lower priority or redesign first

Bands are portfolio guidance, not guarantees.
