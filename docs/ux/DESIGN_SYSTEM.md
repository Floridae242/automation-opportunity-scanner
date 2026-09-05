# Design System Guidance

## Visual intent
Professional enterprise decision-support product. Avoid “AI magic” visuals; emphasize evidence, process clarity, prioritization, and confidence.

## Component vocabulary
AppShell, Breadcrumbs, ProjectCard, ProcessStatusBadge, EvidenceChip, ConfidenceBadge, ScoreGauge, ScoreBreakdown, ProcessNode, OpportunityCard, ImpactEffortMatrix, MissingDataCallout, AnalysisJobStatus, AuditTimeline, ReportSection.

## States required for data components
Loading skeleton; empty; partial/missing data; error/retry; stale/re-analysis available; read-only historical state.

## Content rules
Use precise labels: “AI draft”, “Reviewed”, “Provisional”, “Insufficient evidence”. Avoid absolute claims such as “will save” when only an estimate exists.
