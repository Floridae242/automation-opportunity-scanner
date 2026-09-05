"""M2 intake services: validated metrics and version-on-save semantics (ADR-013)."""

import uuid
from typing import Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from aos_api.errors import ApiError
from aos_api.models import AuditLog, Process, ProcessVersion, Project

PERIODS = Literal["hour", "day", "week", "month", "quarter", "year"]


class PerPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: float = Field(gt=0)
    period: PERIODS


class IntakeMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    frequency: PerPeriod | None = None
    duration_minutes: float | None = Field(default=None, gt=0)
    volume_per_period: PerPeriod | None = None
    error_rate: float | None = Field(default=None, ge=0, le=1)
    rework_rate: float | None = Field(default=None, ge=0, le=1)
    sla: str | None = Field(default=None, max_length=200)
    systems: list[str] | None = Field(default=None, max_length=50)
    approvals_required: int | None = Field(default=None, ge=0, le=999)
    sensitivity: Literal["low", "medium", "high", "restricted"] | None = None


class IntakeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = Field(min_length=1, max_length=20000)
    metrics: IntakeMetrics = Field(default_factory=IntakeMetrics)


class ProjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    department: str | None = Field(default=None, max_length=200)


class ProjectPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    status: Literal["active", "archived"] | None = None


class ProcessIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)


def audit(
    db: Session,
    action: str,
    *,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    entity_type: str,
    entity_id: str,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditLog(
            id=uuid.uuid4(),
            organization_id=org_id,
            actor_user_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=details or {},
        )
    )


def project_payload(db: Session, org_id: uuid.UUID, project: Project) -> dict[str, object]:
    process_count = db.scalar(
        select(func.count()).select_from(Process).where(Process.project_id == project.id)
    )
    return {
        "id": str(project.id),
        "name": project.name,
        "department": project.department,
        "status": project.status,
        "process_count": process_count,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def process_payload(db: Session, process: Process) -> dict[str, object]:
    versions = list(
        db.scalars(
            select(ProcessVersion)
            .where(ProcessVersion.process_id == process.id)
            .order_by(ProcessVersion.version_no.desc())
        )
    )
    return {
        "id": str(process.id),
        "project_id": str(process.project_id),
        "name": process.name,
        "status": process.status,
        "versions": [version_payload(v) for v in versions],
        "latest_version": version_payload(versions[0]) if versions else None,
    }


def version_payload(version: ProcessVersion) -> dict[str, object]:
    return {
        "id": str(version.id),
        "version_no": version.version_no,
        "review_status": version.review_status,
        "source_summary": version.source_summary,
        "metrics": version.metrics_json,
        "created_at": version.created_at.isoformat(),
    }


class TenantOwned(Protocol):
    organization_id: uuid.UUID


def get_owned[ModelT: TenantOwned](
    db: Session, model: type[ModelT], org_id: uuid.UUID, resource_id: uuid.UUID
) -> ModelT:
    record = cast("ModelT | None", db.get(model, resource_id))
    if record is None or record.organization_id != org_id:
        raise ApiError(404, "NOT_FOUND", "The requested resource was not found.")
    return record


def save_intake(
    db: Session, org_id: uuid.UUID, actor_id: uuid.UUID, process: Process, intake: IntakeIn
) -> ProcessVersion:
    if process.status != "active":
        raise ApiError(409, "PROCESS_ARCHIVED", "This process is archived.")
    latest_no = db.scalar(
        select(func.max(ProcessVersion.version_no)).where(ProcessVersion.process_id == process.id)
    )
    for draft in db.scalars(
        select(ProcessVersion).where(
            ProcessVersion.process_id == process.id,
            ProcessVersion.review_status == "draft",
        )
    ):
        draft.review_status = "superseded"
    version = ProcessVersion(
        id=uuid.uuid4(),
        organization_id=org_id,
        process_id=process.id,
        version_no=(latest_no or 0) + 1,
        review_status="draft",
        source_summary=intake.description.strip(),
        metrics_json=intake.metrics.model_dump(exclude_none=True),
        created_by=actor_id,
    )
    db.add(version)
    db.flush()
    audit(
        db,
        "process.intake_saved",
        org_id=org_id,
        actor_id=actor_id,
        entity_type="process_version",
        entity_id=str(version.id),
        details={"version_no": version.version_no},
    )
    return version
