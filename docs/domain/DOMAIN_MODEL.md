# Domain Model

Organization -> Membership -> User

Organization -> Project -> Process -> ProcessVersion -> ProcessStep

ProcessVersion -> Actor / System / Evidence / PainPoint

AnalysisRun -> uses ProcessVersion + PromptVersion + ScoringVersion

AnalysisRun -> Opportunity -> ScoreBreakdown -> Recommendation -> ROI Scenario

## Important invariants
- A ProcessVersion is immutable once marked reviewed; edits create a new version.
- AnalysisRun references an exact ProcessVersion.
- Opportunity evidence references reviewed process entities or explicit user facts.
- Published report references an AnalysisRun, not “latest mutable state”.
- Tenant ownership is inherited but also stored/checked where needed for safe efficient queries.
