# Business Rules

- **BR-001 Unknown is not zero.** Missing operational metrics are `null`, not `0`.
- **BR-002 Score requires reviewed data.** Draft/unreviewed processes may show a provisional preview but not a “final” score.
- **BR-003 Score and confidence are independent.** A high-potential opportunity can have low confidence.
- **BR-004 Risk direction is inverse.** Higher implementation/compliance risk reduces the score via `risk_safety`.
- **BR-005 ROI requires evidence.** If labor cost, frequency, duration, or realistic automation percentage is missing, show partial time-saving scenarios instead of invented ROI.
- **BR-006 Evidence required.** Pain points and opportunities must reference at least one process step or user-confirmed fact.
- **BR-007 Recommendation hierarchy.** Prefer stable supported APIs/integration and workflow capabilities; use RPA where UI automation is justified; use AI when semantic/unstructured reasoning adds value.
- **BR-008 Human controls.** High-risk or judgment-heavy processes should recommend human approval/exception handling rather than full unattended automation.
- **BR-009 No unsupported system claim.** Never claim a named system has an API/integration unless user evidence or an approved integration catalog confirms it.
- **BR-010 Versioned analysis.** Re-analysis creates a new analysis run; prior results stay auditable.
- **BR-011 Tenant isolation.** Tenant ownership is derived server-side from authenticated membership.
- **BR-012 Scoring configuration is versioned.** Historical scores can be reproduced with the weight/rule version used at the time.
