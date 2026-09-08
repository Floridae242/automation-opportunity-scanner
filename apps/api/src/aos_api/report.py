"""Executive report snapshots built from stored structured facts (FR-017)."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.errors import ApiError
from aos_api.intake import audit
from aos_api.models import (
    AnalysisRun,
    Opportunity,
    OpportunityScore,
    PainPoint,
    Process,
    ProcessVersion,
    Project,
    Recommendation,
    Report,
    RoiScenario,
)

REPORT_SCHEMA_VERSION = "aos-report-v1"


def build_report(db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, run: AnalysisRun) -> Report:
    if run.status != "completed" or run.task != "opportunity_analysis":
        raise ApiError(
            409, "REPORT_NOT_READY", "Finish an opportunity analysis before exporting a report."
        )
    version = db.get(ProcessVersion, run.process_version_id)
    process = db.get(Process, version.process_id) if version else None
    project = db.get(Project, process.project_id) if process else None
    opportunities = list(
        db.scalars(select(Opportunity).where(Opportunity.analysis_run_id == run.id))
    )
    if not opportunities:
        raise ApiError(409, "REPORT_NOT_READY", "There are no scored opportunities to report yet.")
    sections = []
    for opportunity in opportunities:
        score = db.scalar(
            select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity.id)
        )
        advice = db.scalar(
            select(Recommendation).where(Recommendation.opportunity_id == opportunity.id)
        )
        roi = db.scalar(
            select(RoiScenario)
            .where(RoiScenario.opportunity_id == opportunity.id)
            .order_by(RoiScenario.created_at.desc())
        )
        dimensions = (
            score.dimension_json if score and isinstance(score.dimension_json, dict) else {}
        )
        sections.append(
            {
                "id": str(opportunity.id),
                "title": opportunity.title,
                "result_state": opportunity.result_state,
                "priority_band": (
                    opportunity.scope_json.get("priority_band")
                    if isinstance(opportunity.scope_json, dict)
                    else None
                ),
                "governance_review": (
                    bool(opportunity.scope_json.get("governance_review", False))
                    if isinstance(opportunity.scope_json, dict)
                    else False
                ),
                "score": score.total_score if score else None,
                "scoring_version": score.scoring_version if score else None,
                "confidence": opportunity.confidence,
                "dimensions": dimensions.get("scores", {}),
                "dimension_evidence": dimensions.get("evidence", {}),
                "scoring_weights": dimensions.get("weights", {}),
                "recommendation": None
                if advice is None
                else {
                    "patterns": advice.patterns_json,
                    "rationale": advice.rationale,
                    "prerequisites": advice.prerequisites_json,
                    "risks": advice.risks_json,
                    "human_control": advice.human_control,
                    "rejected_alternatives": advice.rejected_alternatives_json,
                    "confidence": advice.confidence,
                },
                "roi": roi.output_json if roi else None,
            }
        )
    pain_points = [
        {
            "category": point.category,
            "description": point.description,
            "severity": point.severity,
            "evidence": point.evidence_json,
        }
        for point in db.scalars(select(PainPoint).where(PainPoint.analysis_run_id == run.id))
    ]
    snapshot = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "analysis_run_id": str(run.id),
        "scoring_configuration_id": (
            str(run.scoring_configuration_id) if run.scoring_configuration_id else None
        ),
        "process": process.name if process else None,
        "project": project.name if project else None,
        "source_version_no": version.version_no if version else None,
        "review_status": version.review_status if version else None,
        "intake_summary": version.source_summary[:2000] if version else None,
        "generated_at": run.finished_at.isoformat() if run.finished_at else None,
        "pain_points": pain_points,
        "opportunities": sections,
    }
    report = Report(
        id=uuid.uuid4(),
        organization_id=org_id,
        analysis_run_id=run.id,
        status="ready",
        snapshot_json=snapshot,
        storage_key=None,
    )
    db.add(report)
    audit(
        db,
        "report.created",
        org_id=org_id,
        actor_id=actor_id,
        entity_type="report",
        entity_id=str(report.id),
    )
    db.commit()
    return report
