"""M3 analysis routes: start extraction, poll status, review process versions."""

import json
import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from aos_api.errors import ApiError
from aos_api.extraction import (
    PROMPT_VERSION,
    SCHEMA_VERSION,
    ExtractionError,
    ExtractionProvider,
    ProcessDraft,
    build_provider,
    load_prompt,
    validate_extraction,
)
from aos_api.intake import audit, get_owned
from aos_api.models import (
    Actor,
    AnalysisRun,
    Evidence,
    Process,
    ProcessStep,
    ProcessVersion,
    System,
)
from aos_api.routes_auth import WRITE_ROLES, AuthContext, db_session, require_roles, tenant_context

analyses_router = APIRouter(tags=["analysis"])
versions_router = APIRouter(tags=["process-versions"])

_writer = require_roles(*WRITE_ROLES)

DRAFT_SUMMARY = "AI extraction draft (analysis {analysis_id})"


def _provider_for(request: Request) -> ExtractionProvider:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        raise ApiError(503, "AI_UNAVAILABLE", "The AI service is not configured.")
    if settings.environment == "production" and settings.ai_provider == "demo":
        raise ApiError(503, "AI_UNAVAILABLE", "The AI service is not configured.")
    try:
        return build_provider(
            settings.ai_provider,
            settings.ai_base_url,
            settings.ai_api_key.get_secret_value() if settings.ai_api_key else None,
            settings.ai_model,
        )
    except ExtractionError:
        raise ApiError(503, "AI_UNAVAILABLE", "The AI service is not configured.") from None


def _intake_text(version: ProcessVersion) -> str:
    metrics = json.dumps(version.metrics_json, ensure_ascii=False)
    return f"{version.source_summary}\nRecorded metrics: {metrics}"


def _persist_draft(
    db: Session,
    source: ProcessVersion,
    analysis_id: uuid.UUID,
    actor_id: uuid.UUID,
    draft: ProcessDraft,
) -> ProcessVersion:
    """Create the AI draft version. Drafts are never marked reviewed (FR-007, NFR-R01)."""
    latest_no = db.scalar(
        select(ProcessVersion.version_no)
        .where(ProcessVersion.process_id == source.process_id)
        .order_by(ProcessVersion.version_no.desc())
        .limit(1)
    )
    for draft_row in db.scalars(
        select(ProcessVersion).where(
            ProcessVersion.process_id == source.process_id,
            ProcessVersion.review_status == "draft",
        )
    ):
        draft_row.review_status = "superseded"
    version = ProcessVersion(
        id=uuid.uuid4(),
        organization_id=source.organization_id,
        process_id=source.process_id,
        version_no=(latest_no or 0) + 1,
        review_status="draft",
        source_summary=DRAFT_SUMMARY.format(analysis_id=analysis_id),
        metrics_json=dict(source.metrics_json),
        created_by=actor_id,
    )
    db.add(version)
    db.flush()
    db.add(
        Evidence(
            id=uuid.uuid4(),
            organization_id=version.organization_id,
            process_version_id=version.id,
            source_type="user_input",
            source_ref="intake",
            excerpt=source.source_summary[:2000],
            reviewed=False,
            confidence="medium",
        )
    )
    db.flush()
    actors: dict[str, Actor] = {}
    systems: dict[str, System] = {}
    for index, step in enumerate(draft.steps, start=1):
        actor = None
        if step.actor:
            actor = actors.get(step.actor)
            if actor is None:
                actor = Actor(
                    id=uuid.uuid4(),
                    organization_id=version.organization_id,
                    process_version_id=version.id,
                    name=step.actor[:200],
                )
                actors[step.actor] = actor
                db.add(actor)
                db.flush()
        system = None
        if step.system:
            system = systems.get(step.system)
            if system is None:
                system = System(
                    id=uuid.uuid4(),
                    organization_id=version.organization_id,
                    process_version_id=version.id,
                    name=step.system[:200],
                    integration_status="unknown",
                )
                systems[step.system] = system
                db.add(system)
                db.flush()
        db.add(
            ProcessStep(
                id=uuid.uuid4(),
                organization_id=version.organization_id,
                process_version_id=version.id,
                step_key=step.step_key,
                sequence_no=index,
                name=step.name,
                actor_id=actor.id if actor else None,
                system_id=system.id if system else None,
                manual=step.manual,
                duration_minutes=step.duration_minutes,
                data_json={"evidence_refs": step.evidence_refs},
            )
        )
    db.flush()
    return version


def run_extraction(
    session_factory: sessionmaker[Session],
    analysis_id: uuid.UUID,
    provider: ExtractionProvider,
    actor_id: uuid.UUID,
) -> None:
    """Execute one queued extraction; any failure preserves the intake (USER_FLOWS)."""
    with session_factory() as db:
        run = db.get(AnalysisRun, analysis_id)
        source = db.get(ProcessVersion, run.process_version_id) if run else None
        if run is None or source is None:
            return
        run.status = "running"
        db.commit()
        try:
            draft = validate_extraction(provider.extract(load_prompt(), _intake_text(source)))
        except ExtractionError as error:
            run.status = "failed"
            run.error_code = error.code
            run.finished_at = datetime.now(UTC)
            db.commit()
            return
        version = _persist_draft(db, source, run.id, actor_id, draft)
        run.status = "completed"
        run.finished_at = datetime.now(UTC)
        audit(
            db,
            "analysis.extraction_completed",
            org_id=run.organization_id,
            actor_id=actor_id,
            entity_type="process_version",
            entity_id=str(version.id),
        )
        db.commit()


@analyses_router.post("/processes/{processId}/analyses", status_code=202)
def start_analysis(
    processId: uuid.UUID,
    request: Request,
    background: BackgroundTasks,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_writer),
    db: Session = Depends(db_session),
) -> dict[str, str]:
    process = get_owned(db, Process, org_id, processId)
    latest = db.scalar(
        select(ProcessVersion)
        .where(ProcessVersion.process_id == process.id)
        .order_by(ProcessVersion.version_no.desc())
        .limit(1)
    )
    if latest is None:
        raise ApiError(409, "NOTHING_TO_EXTRACT", "Save an intake draft before running extraction.")
    if latest.review_status == "reviewed":
        from aos_api.opportunity_engine import run_opportunity_analysis

        run = run_opportunity_analysis(db, org_id, context.user.id, latest)
        return {"analysis_id": str(run.id), "status": run.status}
    key = request.headers.get("idempotency-key") or None
    if key:
        existing = db.scalar(
            select(AnalysisRun).where(
                AnalysisRun.organization_id == org_id, AnalysisRun.idempotency_key == key
            )
        )
        if existing is not None:
            return {"analysis_id": str(existing.id), "status": existing.status}
    provider = _provider_for(request)
    run = AnalysisRun(
        id=uuid.uuid4(),
        organization_id=org_id,
        process_version_id=latest.id,
        status="queued",
        provider=provider.name,
        model_id=provider.model_id,
        prompt_version=PROMPT_VERSION,
        schema_version=SCHEMA_VERSION,
        idempotency_key=key,
    )
    db.add(run)
    audit(
        db,
        "analysis.extraction_started",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="analysis_run",
        entity_id=str(run.id),
    )
    db.commit()
    factory = request.app.state.session_factory
    background.add_task(run_extraction, factory, run.id, provider, context.user.id)
    return {"analysis_id": str(run.id), "status": "queued"}


@analyses_router.get("/analyses/{analysisId}/opportunities")
def list_analysis_opportunities(
    analysisId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> list[dict[str, object]]:
    from aos_api.models import Opportunity, OpportunityScore

    run = get_owned(db, AnalysisRun, org_id, analysisId)
    rows = db.scalars(
        select(Opportunity).where(
            Opportunity.analysis_run_id == run.id, Opportunity.organization_id == org_id
        )
    )
    output = []
    for opportunity in rows:
        score = db.scalar(
            select(OpportunityScore).where(OpportunityScore.opportunity_id == opportunity.id)
        )
        scope = opportunity.scope_json if isinstance(opportunity.scope_json, dict) else {}
        output.append(
            {
                "id": str(opportunity.id),
                "title": opportunity.title,
                "status": opportunity.status,
                "result_state": opportunity.result_state,
                "confidence": opportunity.confidence,
                "priority_band": scope.get("priority_band"),
                "total_score": score.total_score if score else None,
                "scoring_version": score.scoring_version if score else None,
                "axes": scope.get("axes"),
                "governance_review": scope.get("governance_review", False),
            }
        )
    return output


@analyses_router.get("/analyses/{analysisId}")
def read_analysis(
    analysisId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    run = get_owned(db, AnalysisRun, org_id, analysisId)
    draft_id = db.scalar(
        select(ProcessVersion.id).where(
            ProcessVersion.organization_id == org_id,
            ProcessVersion.source_summary == DRAFT_SUMMARY.format(analysis_id=run.id),
        )
    )
    from aos_api.models import PainPoint

    pain_points = [
        {
            "category": point.category,
            "description": point.description,
            "severity": point.severity,
            "confidence": point.confidence,
            "evidence_refs": point.evidence_json,
        }
        for point in db.scalars(select(PainPoint).where(PainPoint.analysis_run_id == run.id))
    ]
    return {
        "analysis_id": str(run.id),
        "status": run.status,
        "task": run.task,
        "pain_points": pain_points,
        "provider": run.provider,
        "model_id": run.model_id,
        "prompt_version": run.prompt_version,
        "schema_version": run.schema_version,
        "error_code": run.error_code,
        "draft_version_id": str(draft_id) if draft_id else None,
    }


class SystemPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    integration_status: Literal[
        "unknown", "evidence_of_api", "no_practical_api", "manual_only", "mixed"
    ] = "unknown"


class StepPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_key: str
    name: str | None = Field(default=None, min_length=1, max_length=300)
    duration_minutes: float | None = Field(default=None, ge=0)
    manual: bool | None = None
    actor: str | None = Field(default=None, max_length=200)
    system: str | None = Field(default=None, max_length=200)
    sequence_no: int | None = Field(default=None, ge=1)


class DraftEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    steps: list[StepPatch] = Field(min_length=1)
    systems: list[SystemPatch] | None = None


def _get_draft(db: Session, org_id: uuid.UUID, version_id: uuid.UUID) -> ProcessVersion:
    version = get_owned(db, ProcessVersion, org_id, version_id)
    if version.review_status != "draft":
        raise ApiError(
            409,
            "VERSION_IMMUTABLE",
            "Only draft versions can be edited. Create a new version instead.",
        )
    return version


@versions_router.get("/process-versions/{versionId}")
def read_version(
    versionId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    version = get_owned(db, ProcessVersion, org_id, versionId)
    steps = db.scalars(
        select(ProcessStep)
        .where(ProcessStep.process_version_id == version.id)
        .order_by(ProcessStep.sequence_no)
    )
    actors = {
        a.id: a for a in db.scalars(select(Actor).where(Actor.process_version_id == version.id))
    }
    systems = {
        s.id: s for s in db.scalars(select(System).where(System.process_version_id == version.id))
    }
    evidence = list(db.scalars(select(Evidence).where(Evidence.process_version_id == version.id)))
    return {
        "id": str(version.id),
        "process_id": str(version.process_id),
        "version_no": version.version_no,
        "review_status": version.review_status,
        "source_summary": version.source_summary,
        "metrics": version.metrics_json,
        "steps": [
            {
                "step_id": str(step.id),
                "step_key": step.step_key,
                "sequence_no": step.sequence_no,
                "name": step.name,
                "actor": actors[step.actor_id].name
                if step.actor_id and step.actor_id in actors
                else None,
                "system": (
                    systems[step.system_id].name
                    if step.system_id and step.system_id in systems
                    else None
                ),
                "manual": step.manual,
                "duration_minutes": step.duration_minutes,
                "evidence_refs": (step.data_json or {}).get("evidence_refs", []),
            }
            for step in steps
        ],
        "evidence": [
            {"source_ref": item.source_ref, "excerpt": item.excerpt, "confidence": item.confidence}
            for item in evidence
        ],
        "systems": [
            {"name": item.name, "integration_status": item.integration_status}
            for item in db.scalars(select(System).where(System.process_version_id == version.id))
        ],
    }


@versions_router.patch("/process-versions/{versionId}")
def edit_draft_version(
    versionId: uuid.UUID,
    body: DraftEdit,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_writer),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    version = _get_draft(db, org_id, versionId)
    steps = {
        step.step_key: step
        for step in db.scalars(
            select(ProcessStep).where(ProcessStep.process_version_id == version.id)
        )
    }
    for patch in body.steps:
        step = steps.get(patch.step_key)
        if step is None:
            raise ApiError(422, "VALIDATION_ERROR", f"Unknown step key {patch.step_key!r}.")
        if patch.name is not None:
            step.name = patch.name
        if patch.duration_minutes is not None:
            step.duration_minutes = patch.duration_minutes
        if patch.manual is not None:
            step.manual = patch.manual
        if patch.sequence_no is not None:
            step.sequence_no = patch.sequence_no
        if patch.actor is not None:
            step.actor_id = (
                _resolve_party(db, version, actors=True, name=patch.actor).id
                if patch.actor
                else None
            )
        if patch.system is not None:
            step.system_id = (
                _resolve_party(db, version, actors=False, name=patch.system).id
                if patch.system
                else None
            )
    if body.systems is not None:
        existing = {
            row.name: row
            for row in db.scalars(select(System).where(System.process_version_id == version.id))
        }
        for sys_patch in body.systems:
            row = existing.get(sys_patch.name)
            if row is None:
                row = System(
                    id=uuid.uuid4(),
                    organization_id=org_id,
                    process_version_id=version.id,
                    name=sys_patch.name,
                    integration_status=sys_patch.integration_status,
                )
                db.add(row)
            else:
                row.integration_status = sys_patch.integration_status
    audit(
        db,
        "process_version.draft_edited",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="process_version",
        entity_id=str(version.id),
    )
    db.commit()
    return {"version_id": str(version.id), "review_status": "draft"}


def _resolve_party(
    db: Session, version: ProcessVersion, *, actors: bool, name: str
) -> Actor | System:
    name = name.strip()[:200]
    if actors:
        existing_actor = db.scalar(
            select(Actor).where(Actor.name == name, Actor.process_version_id == version.id)
        )
        if existing_actor is not None:
            return existing_actor
        created: Actor | System = Actor(
            id=uuid.uuid4(),
            organization_id=version.organization_id,
            process_version_id=version.id,
            name=name,
        )
    else:
        existing_system = db.scalar(
            select(System).where(System.name == name, System.process_version_id == version.id)
        )
        if existing_system is not None:
            return existing_system
        created = System(
            id=uuid.uuid4(),
            organization_id=version.organization_id,
            process_version_id=version.id,
            name=name,
            integration_status="unknown",
        )
    db.add(created)
    db.flush()
    return created


@versions_router.post("/process-versions/{versionId}/review")
def mark_reviewed(
    versionId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(require_roles("owner", "admin", "reviewer")),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    version = _get_draft(db, org_id, versionId)
    step_count = len(
        list(db.scalars(select(ProcessStep.id).where(ProcessStep.process_version_id == version.id)))
    )
    if step_count == 0:
        raise ApiError(409, "NOTHING_TO_REVIEW", "Capture steps before marking a version reviewed.")
    version.review_status = "reviewed"
    for evidence in db.scalars(select(Evidence).where(Evidence.process_version_id == version.id)):
        evidence.reviewed = True
    audit(
        db,
        "process_version.reviewed",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="process_version",
        entity_id=str(version.id),
    )
    db.commit()
    return {"version_id": str(version.id), "review_status": "reviewed", "step_count": step_count}


opportunities_router = APIRouter(tags=["opportunities"])


@opportunities_router.get("/opportunities/{opportunityId}")
def read_opportunity(
    opportunityId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    from aos_api.models import Opportunity, OpportunityScore

    opportunity = get_owned(db, Opportunity, org_id, opportunityId)
    score = db.scalar(
        select(OpportunityScore)
        .where(OpportunityScore.opportunity_id == opportunity.id)
        .order_by(OpportunityScore.created_at.desc())
        .limit(1)
    )
    if score is None:
        raise ApiError(404, "NOT_FOUND", "The requested resource was not found.")
    dimensions = score.dimension_json if isinstance(score.dimension_json, dict) else {}
    return {
        "id": str(opportunity.id),
        "analysis_run_id": str(opportunity.analysis_run_id),
        "title": opportunity.title,
        "status": opportunity.status,
        "result_state": opportunity.result_state,
        "confidence": opportunity.confidence,
        "scope": opportunity.scope_json,
        "score": {
            "total": score.total_score,
            "scoring_version": score.scoring_version,
            "dimensions": dimensions.get("scores", {}),
            "dimension_evidence": dimensions.get("evidence", {}),
            "coverage": dimensions.get("coverage"),
            "confidence_version": dimensions.get("confidence_version"),
        },
    }
