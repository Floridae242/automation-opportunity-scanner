"""Run opportunity analysis over a reviewed process version (deterministic)."""

import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.advice import AdviceFacts, recommend, time_scenarios
from aos_api.intake import audit
from aos_api.models import (
    AnalysisRun,
    Evidence,
    Opportunity,
    OpportunityScore,
    PainPoint,
    ProcessStep,
    ProcessVersion,
    Recommendation,
    RoiScenario,
    System,
)
from aos_api.opportunity import (
    OpportunityFacts,
    StepFact,
    SystemFact,
    derive_opportunity,
    detect_pain_points,
    score_snapshot,
)
from aos_api.scoring_config import configuration_weights, current_configuration

_PERIODS_PER_WEEK = {
    "hour": 24 * 7,
    "day": 7,
    "week": 1,
    "month": 1 / 4.345,
    "quarter": 1 / 13,
    "year": 1 / 52,
}

_CONFIDENCE_BANDS = {"low": 33, "medium": 66, "high": 100}


def _num(metrics: dict[str, object], key: str) -> float | None:
    value = metrics.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _int(metrics: dict[str, object], key: str) -> int | None:
    value = metrics.get(key)
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _str(metrics: dict[str, object], key: str) -> str | None:
    return value if isinstance(value := metrics.get(key), str) else None


def _frequency_per_week(metrics: dict[str, object]) -> float | None:
    raw = metrics.get("frequency")
    if not isinstance(raw, dict):
        return None
    frequency: dict[object, object] = raw
    value, period = frequency.get("value"), frequency.get("period")
    if isinstance(value, (int, float)) and period in _PERIODS_PER_WEEK:
        return value * _PERIODS_PER_WEEK[period]
    return None


def build_facts(db: Session, version: ProcessVersion) -> OpportunityFacts:
    steps = list(
        db.scalars(
            select(ProcessStep)
            .where(ProcessStep.process_version_id == version.id)
            .order_by(ProcessStep.sequence_no)
        )
    )
    systems = list(db.scalars(select(System).where(System.process_version_id == version.id)))
    evidences = list(db.scalars(select(Evidence).where(Evidence.process_version_id == version.id)))
    metrics: dict[str, object] = (
        version.metrics_json if isinstance(version.metrics_json, dict) else {}
    )
    durations = [step.duration_minutes for step in steps if step.duration_minutes is not None]
    total: float | None
    if durations and len(durations) == len(steps):
        total = sum(durations)
    elif isinstance(explicit := metrics.get("duration_minutes"), (int, float)):
        total = float(explicit)
    else:
        total = None
    qualities = tuple(
        100 if item.reviewed else _CONFIDENCE_BANDS.get(item.confidence or "low", 33)
        for item in evidences
    )
    return OpportunityFacts(
        frequency_per_week=_frequency_per_week(metrics),
        step_total_minutes=total,
        steps=tuple(StepFact(step.step_key, step.manual, step.duration_minutes) for step in steps),
        systems=tuple(SystemFact(s.name, s.integration_status) for s in systems),
        error_rate=_num(metrics, "error_rate"),
        rework_rate=_num(metrics, "rework_rate"),
        approvals_required=_int(metrics, "approvals_required"),
        sensitivity=_str(metrics, "sensitivity"),
        strategic_alignment=_num(metrics, "strategic_alignment"),
        integration_complexity=_num(metrics, "integration_complexity"),
        change_complexity=_num(metrics, "change_complexity"),
        security_compliance_effort=_num(metrics, "security_compliance_effort"),
        exception_handling_complexity=_num(metrics, "exception_handling_complexity"),
        realistic_automation_rate=_num(metrics, "realistic_automation_rate"),
        exception_rate=_num(metrics, "exception_rate"),
        loaded_hourly_cost=_num(metrics, "loaded_hourly_cost"),
        currency=_str(metrics, "currency"),
        monthly_operating_cost=_num(metrics, "monthly_operating_cost"),
        implementation_cost=_num(metrics, "implementation_cost"),
        fact_source_qualities=qualities,
        reviewed=version.review_status == "reviewed",
    )


def run_opportunity_analysis(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, version: ProcessVersion
) -> AnalysisRun:
    if version.review_status != "reviewed":
        from aos_api.errors import ApiError

        raise ApiError(
            409,
            "REVIEW_REQUIRED",
            "Mark the process version reviewed before scoring opportunities.",
        )
    facts = build_facts(db, version)
    configuration = current_configuration(db, org_id, actor_id)
    snapshot = score_snapshot(facts, configuration_weights(configuration))
    findings = detect_pain_points(facts)
    candidate = derive_opportunity(facts, findings)
    run = AnalysisRun(
        id=uuid.uuid4(),
        organization_id=org_id,
        process_version_id=version.id,
        status="completed",
        task="opportunity_analysis",
        provider="rules",
        model_id="aos-opportunity-engine-v1",
        prompt_version=None,
        schema_version=snapshot["scoring_version"],
        scoring_version=snapshot["scoring_version"],
        scoring_configuration_id=configuration.id,
    )
    db.add(run)
    db.flush()
    for finding in findings:
        db.add(
            PainPoint(
                id=uuid.uuid4(),
                organization_id=org_id,
                analysis_run_id=run.id,
                category=finding.category,
                description=finding.description,
                severity=finding.severity,
                confidence=finding.confidence,
                evidence_json=list(finding.evidence_refs),
            )
        )
    opportunity_id = None
    if candidate is not None:
        confidence = int(cast("float", snapshot["assessment_confidence"]))
        opportunity = Opportunity(
            id=uuid.uuid4(),
            organization_id=org_id,
            analysis_run_id=run.id,
            title=candidate["title"],
            scope_json={
                **(candidate["scope"] if isinstance(candidate["scope"], dict) else {}),
                "axes": snapshot["axes"],
                "priority_band": snapshot["priority_band"],
                "governance_review": snapshot["governance_review"],
                "result_state": snapshot["result_state"],
            },
            confidence=confidence,
            result_state=snapshot["result_state"],
        )
        db.add(opportunity)
        db.flush()
        db.add(
            OpportunityScore(
                id=uuid.uuid4(),
                organization_id=org_id,
                opportunity_id=opportunity.id,
                total_score=snapshot["total_score"],
                dimension_json={
                    "scores": snapshot["dimensions"],
                    "evidence": snapshot["dimension_evidence"],
                    "weights": snapshot["weights"],
                    "coverage": snapshot["coverage"],
                    "confidence_version": snapshot["confidence_version"],
                },
                confidence_score=confidence,
                scoring_version=str(snapshot["scoring_version"]),
                scoring_configuration_id=configuration.id,
            )
        )
        opportunity_id = opportunity.id
        _persist_advice(db, org_id, opportunity, facts, snapshot)
    audit(
        db,
        "analysis.opportunity_completed",
        org_id=org_id,
        actor_id=actor_id,
        entity_type="analysis_run",
        entity_id=str(run.id),
        details={"pain_points": len(findings), "opportunity": opportunity_id is not None},
    )
    db.commit()
    return run


def _persist_advice(
    db: Session,
    org_id: uuid.UUID,
    opportunity: Opportunity,
    facts: OpportunityFacts,
    snapshot: dict[str, object],
) -> None:
    advice_facts = AdviceFacts(
        manual_steps=sum(1 for step in facts.steps if step.manual),
        total_steps=len(facts.steps),
        integration_statuses=tuple(s.integration_status for s in facts.systems),
        has_approvals=bool(facts.approvals_required),
        error_rate=facts.error_rate,
        sensitivity=facts.sensitivity,
        confidence=float(cast("float", snapshot["assessment_confidence"])),
        frequency_per_week=facts.frequency_per_week,
        minutes_per_occurrence=facts.step_total_minutes,
        realistic_automation_rate=facts.realistic_automation_rate,
        exception_rate=facts.exception_rate,
        loaded_hourly_cost=facts.loaded_hourly_cost,
        currency=facts.currency,
        monthly_operating_cost=facts.monthly_operating_cost,
        implementation_cost=facts.implementation_cost,
    )
    advice = recommend(advice_facts)
    if advice is not None:
        db.add(
            Recommendation(
                id=uuid.uuid4(),
                organization_id=org_id,
                opportunity_id=opportunity.id,
                patterns_json=advice["patterns"],
                rationale=advice["rationale"],
                prerequisites_json=advice["prerequisites"],
                risks_json=advice["risks"],
                human_control=advice["human_control"],
                rejected_alternatives_json=advice["rejected_alternatives"],
                confidence=advice["confidence"],
            )
        )
    scenarios = time_scenarios(advice_facts)
    inputs = scenarios.get("inputs")
    db.add(
        RoiScenario(
            id=uuid.uuid4(),
            organization_id=org_id,
            opportunity_id=opportunity.id,
            input_json=dict(inputs) if isinstance(inputs, dict) else {},
            output_json=scenarios,
        )
    )
    db.flush()
