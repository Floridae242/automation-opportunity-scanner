# Requirements Traceability Matrix

| Requirement | Domain/Design | API | Primary Test |
|---|---|---|---|
| FR-003 Intake | UX_SPEC | POST /processes/:id/intake | E2E intake |
| FR-005 AI extraction | AI_SYSTEM_DESIGN | POST /processes/:id/analyses | integration AI adapter |
| FR-008 Review | DOMAIN_MODEL | PATCH /process-versions/:id | E2E review |
| FR-012 Score | OPPORTUNITY_SCORING_MODEL | GET /analyses/:id/opportunities | unit scoring golden vectors |
| FR-014 Recommendation | RECOMMENDATION_RULES | analysis result | AI/rule eval |
| FR-015 ROI | ROI_CALCULATION | opportunity detail | unit ROI boundaries |
| FR-020 Tenant isolation | MULTI_TENANCY | all tenant routes | authorization integration suite |

Update this matrix when endpoints or ownership change.
