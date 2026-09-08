"""M4 deterministic opportunity engine (ADR-003/008/011/013).

Pure functions only: reviewed facts in, score snapshots out. The LLM never
participates here; every band is a documented rule anchor from
docs/domain/OPPORTUNITY_SCORING_MODEL.md. Missing evidence yields None —
never a fabricated zero (BR-001).
"""

import statistics
from dataclasses import dataclass, field
from typing import Literal

SCORING_VERSION = "aos-score-v1"
CONFIDENCE_VERSION = "aos-confidence-v1"
AXES_VERSION = "aos-portfolio-axes-v1"

DIMENSION_WEIGHTS = {
    "business_value": 0.20,
    "time_saving": 0.20,
    "repetitiveness": 0.15,
    "feasibility": 0.15,
    "error_reduction": 0.10,
    "integration_ease": 0.10,
    "risk_safety": 0.10,
}

_INTEGRATION_SCORES = {
    "evidence_of_api": 90,
    "mixed": 50,
    "no_practical_api": 15,
    "manual_only": 10,
}


@dataclass(frozen=True)
class StepFact:
    step_key: str
    manual: bool | None
    duration_minutes: float | None


@dataclass(frozen=True)
class SystemFact:
    name: str
    integration_status: str


@dataclass(frozen=True)
class OpportunityFacts:
    """Everything the engine may use must be a reviewed fact."""

    frequency_per_week: float | None
    step_total_minutes: float | None
    steps: tuple[StepFact, ...]
    systems: tuple[SystemFact, ...]
    error_rate: float | None
    rework_rate: float | None
    approvals_required: int | None
    sensitivity: str | None
    strategic_alignment: float | None
    integration_complexity: float | None
    change_complexity: float | None
    security_compliance_effort: float | None
    exception_handling_complexity: float | None
    realistic_automation_rate: float | None = None
    exception_rate: float | None = None
    loaded_hourly_cost: float | None = None
    currency: str | None = None
    monthly_operating_cost: float | None = None
    implementation_cost: float | None = None
    fact_source_qualities: tuple[int, ...] = field(default_factory=tuple)
    reviewed: bool = False


@dataclass(frozen=True)
class DimensionResult:
    score: float | None
    evidence: tuple[str, ...]


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _frequency_band(per_week: float) -> float:
    if per_week < 1:
        return 10.0
    if per_week < 5:
        return 30.0
    if per_week < 20:
        return 50.0
    if per_week < 70:
        return 70.0
    return 90.0


def _hours_per_week(facts: OpportunityFacts) -> float | None:
    if facts.frequency_per_week is None or facts.step_total_minutes is None:
        return None
    return facts.frequency_per_week * facts.step_total_minutes / 60.0


def time_saving(facts: OpportunityFacts) -> DimensionResult:
    hours = _hours_per_week(facts)
    if hours is None:
        return DimensionResult(None, ("missing frequency or duration evidence",))
    score = _clamp(hours)  # 0h->0, ~100+ weekly hours -> 100
    return DimensionResult(round(score, 1), (f"{round(hours, 1)} manual hours/week evidence",))


def repetitiveness(facts: OpportunityFacts) -> DimensionResult:
    if facts.frequency_per_week is None or not facts.steps:
        return DimensionResult(None, ("missing frequency or step evidence",))
    manual_known = [step.manual for step in facts.steps if step.manual is not None]
    if not manual_known:
        return DimensionResult(None, ("no reviewed manual flags on steps",))
    ratio = sum(1 for m in manual_known if m) / len(manual_known)
    score = (_frequency_band(facts.frequency_per_week) + ratio * 100) / 2
    return DimensionResult(
        round(score, 1), (f"freq/week={facts.frequency_per_week}, manual ratio={round(ratio, 2)}",)
    )


def error_reduction(facts: OpportunityFacts) -> DimensionResult:
    rates = [r for r in (facts.error_rate, facts.rework_rate) if r is not None]
    if not rates:
        return DimensionResult(None, ("no error/rework evidence",))
    return DimensionResult(
        round(_clamp(statistics.mean(rates) * 100), 1), ("rate evidence 0-1 scale",)
    )


def feasibility(facts: OpportunityFacts) -> DimensionResult:
    if not facts.steps:
        return DimensionResult(None, ("no steps captured",))
    score = 50.0
    evidence = ["baseline 50"]
    manual_known = [step.manual for step in facts.steps if step.manual is not None]
    if manual_known:
        ratio = sum(1 for m in manual_known if m) / len(manual_known)
        score -= 20 * ratio
        evidence.append(f"manual ratio {round(ratio, 2)}")
    if facts.systems and all(s.integration_status == "evidence_of_api" for s in facts.systems):
        score += 25
        evidence.append("all systems have integration evidence")
    if len(facts.steps) <= 8:
        score += 10
        evidence.append("8 or fewer steps")
    return DimensionResult(round(_clamp(score), 1), tuple(evidence))


def integration_ease(facts: OpportunityFacts) -> DimensionResult:
    known = [s for s in facts.systems if s.integration_status != "unknown"]
    if not known:
        return DimensionResult(None, ("no system integration evidence",))
    return DimensionResult(
        round(statistics.mean(_INTEGRATION_SCORES[s.integration_status] for s in known), 1),
        tuple(f"{s.name}:{s.integration_status}" for s in known),
    )


def implementation_risk(facts: OpportunityFacts) -> DimensionResult:
    score = 20.0
    evidence = ["baseline 20"]
    if facts.sensitivity in {"high", "restricted"}:
        score += 40
        evidence.append(f"sensitivity={facts.sensitivity}")
    if (facts.approvals_required or 0) > 0:
        score += 10
        evidence.append("human approvals required")
    if facts.error_rate is not None and facts.error_rate > 0.1:
        score += 15
        evidence.append("error rate above 10%")
    return DimensionResult(round(_clamp(score), 1), tuple(evidence))


def dimension_scores(facts: OpportunityFacts) -> dict[str, DimensionResult]:
    risk = implementation_risk(facts)
    scores: dict[str, DimensionResult] = {
        "business_value": business_value(facts),
        "time_saving": time_saving(facts),
        "repetitiveness": repetitiveness(facts),
        "feasibility": feasibility(facts),
        "error_reduction": error_reduction(facts),
        "integration_ease": integration_ease(facts),
        "risk_safety": (
            DimensionResult(
                round(100.0 - risk.score, 1) if risk.score is not None else None,
                risk.evidence,
            )
            if risk.score is not None
            else risk
        ),
    }
    return scores


def business_value(facts: OpportunityFacts) -> DimensionResult:
    parts: list[float] = []
    evidence: list[str] = []
    hours = _hours_per_week(facts)
    if hours is not None:
        parts.append(_clamp(hours))
        evidence.append("weekly hours")
    rates = [r for r in (facts.error_rate, facts.rework_rate) if r is not None]
    if rates:
        parts.append(_clamp(statistics.mean(rates) * 100))
        evidence.append("quality rates")
    if facts.strategic_alignment is not None:
        parts.append(_clamp(facts.strategic_alignment))
        evidence.append("stated strategic alignment")
    if not parts:
        return DimensionResult(None, ("no value evidence",))
    if facts.sensitivity == "restricted":
        evidence.append("restricted data raises compliance relevance")
    return DimensionResult(round(_clamp(statistics.mean(parts)), 1), tuple(evidence))


def total_score(scores: dict[str, DimensionResult]) -> float | None:
    """aos-score-v1 weighted sum; None when any required dimension is missing."""
    values: list[float] = []
    for name in DIMENSION_WEIGHTS:
        score = scores[name].score
        if score is None:
            return None
        values.append(score)
    weights = list(DIMENSION_WEIGHTS.values())
    return round(sum(v * w for v, w in zip(values, weights, strict=True)), 2)


def coverage(scores: dict[str, DimensionResult]) -> float:
    known = sum(1 for result in scores.values() if result.score is not None)
    return known * 100 / len(DIMENSION_WEIGHTS)


def assessment_confidence(scores: dict[str, DimensionResult], facts: OpportunityFacts) -> float:
    cov = coverage(scores)
    quality = statistics.mean(facts.fact_source_qualities) if facts.fact_source_qualities else 40.0
    review = 100.0 if facts.reviewed else 0.0
    return round(0.45 * cov + 0.35 * quality + 0.20 * review, 1)


def result_state(
    cov: float, reviewed: bool, complete: bool
) -> Literal["final", "provisional", "insufficient_evidence"]:
    if complete and reviewed:
        return "final"
    if cov >= 60:
        return "provisional"
    return "insufficient_evidence"


def priority_band(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 80:
        return "investigate now"
    if score >= 65:
        return "high-priority candidate"
    if score >= 50:
        return "evaluate with additional evidence"
    return "lower priority or redesign first"


def governance_flag(facts: OpportunityFacts) -> bool:
    risk = implementation_risk(facts)
    return risk.score is not None and risk.score >= 70


def portfolio_axes(
    scores: dict[str, DimensionResult], facts: OpportunityFacts
) -> dict[str, object]:
    def value(name: str) -> float | None:
        result = scores.get(name)
        return result.score if result else None

    impact_parts = [
        (value("business_value"), 0.45),
        (value("time_saving"), 0.25),
        (value("error_reduction"), 0.15),
        (facts.strategic_alignment if facts.strategic_alignment is not None else None, 0.15),
    ]
    effort_parts = [
        (facts.integration_complexity, 0.35),
        (facts.change_complexity, 0.25),
        (facts.security_compliance_effort, 0.20),
        (facts.exception_handling_complexity, 0.20),
    ]

    def combine(parts: list[tuple[float | None, float]]) -> float | None:
        present: list[tuple[float, float]] = [
            (value, weight) for value, weight in parts if value is not None
        ]
        if not present:
            return None
        return round(_clamp(sum(v * w for v, w in present) / sum(w for _, w in present)), 1)

    return {
        "version": AXES_VERSION,
        "impact": combine(impact_parts),
        "effort": combine(effort_parts),
    }


def score_snapshot(facts: OpportunityFacts) -> dict[str, object]:
    scores = dimension_scores(facts)
    cov = coverage(scores)
    confidence = assessment_confidence(scores, facts)
    total = total_score(scores)
    state = result_state(cov, facts.reviewed, total is not None)
    return {
        "scoring_version": SCORING_VERSION,
        "total_score": total,
        "assessment_confidence": confidence,
        "dimensions": {name: scores[name].score for name in DIMENSION_WEIGHTS},
        "dimension_evidence": {name: scores[name].evidence for name in DIMENSION_WEIGHTS},
        "coverage": round(cov, 1),
        "result_state": state,
        "priority_band": priority_band(total) if state != "insufficient_evidence" else None,
        "governance_review": governance_flag(facts),
        "axes": portfolio_axes(scores, facts),
        "confidence_version": CONFIDENCE_VERSION,
    }


@dataclass(frozen=True)
class PainPointFinding:
    category: str
    description: str
    severity: Literal["low", "medium", "high"]
    confidence: Literal["low", "medium", "high"]
    evidence_refs: tuple[str, ...]


def detect_pain_points(facts: OpportunityFacts) -> list[PainPointFinding]:
    """Rule-based detection over reviewed facts (PROCESS_ANALYSIS_KNOWLEDGE)."""
    findings: list[PainPointFinding] = []
    manual_keys = tuple(step.step_key for step in facts.steps if step.manual)
    if len(manual_keys) >= 2 and facts.frequency_per_week and facts.frequency_per_week >= 5:
        findings.append(
            PainPointFinding(
                "repetitive_manual_work",
                "Multiple manual steps repeat at high frequency.",
                "high" if facts.frequency_per_week >= 20 else "medium",
                "high"
                if all(step.duration_minutes is not None for step in facts.steps)
                else "medium",
                manual_keys + ("metrics:frequency",),
            )
        )
    missing_duration = tuple(step.step_key for step in facts.steps if step.duration_minutes is None)
    if missing_duration:
        findings.append(
            PainPointFinding(
                "missing_evidence",
                "Step durations were not provided, so time-saving is a lower-bound estimate.",
                "low",
                "high",
                missing_duration,
            )
        )
    unknown_systems = tuple(s.name for s in facts.systems if s.integration_status == "unknown")
    if unknown_systems:
        findings.append(
            PainPointFinding(
                "integration_unknown",
                "System integration availability has no evidence yet.",
                "medium",
                "medium",
                tuple(f"system:{name}" for name in unknown_systems),
            )
        )
    if facts.error_rate is not None and facts.error_rate > 0.05:
        findings.append(
            PainPointFinding(
                "quality_rework",
                "Reported error rate indicates preventable rework.",
                "high" if facts.error_rate > 0.15 else "medium",
                "medium",
                ("metrics:error_rate",),
            )
        )
    if (facts.approvals_required or 0) > 0:
        findings.append(
            PainPointFinding(
                "approval_waiting",
                "Human approval steps can introduce handoff waits.",
                "medium",
                "medium",
                ("metrics:approvals_required",),
            )
        )
    return findings


def derive_opportunity(
    facts: OpportunityFacts, findings: list[PainPointFinding]
) -> dict[str, object] | None:
    """One candidate opportunity per analyzed version (M4 scope)."""
    if not findings:
        return None
    actionable = [f for f in findings if f.category != "missing_evidence"]
    if not actionable:
        return None
    steps = tuple(step.step_key for step in facts.steps if step.manual)
    return {
        "title": "Automate repetitive manual steps",
        "scope": {
            "step_keys": steps or tuple(step.step_key for step in facts.steps),
            "pain_categories": [f.category for f in actionable],
        },
    }
