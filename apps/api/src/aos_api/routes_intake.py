"""M2 intake router: tenant-scoped project/process CRUD and guided intake."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.errors import ApiError
from aos_api.intake import (
    IntakeIn,
    ProcessIn,
    ProjectIn,
    ProjectPatch,
    audit,
    get_owned,
    process_payload,
    project_payload,
    save_intake,
)
from aos_api.models import Process, Project
from aos_api.routes_auth import WRITE_ROLES, AuthContext, db_session, require_roles, tenant_context

projects_router = APIRouter(tags=["projects"])
processes_router = APIRouter(tags=["processes"])

_writer = require_roles(*WRITE_ROLES)
_admin = require_roles("owner", "admin")


@projects_router.get("/projects")
def list_projects(
    org_id: uuid.UUID = Depends(tenant_context), db: Session = Depends(db_session)
) -> list[dict[str, object]]:
    projects = db.scalars(
        select(Project).where(Project.organization_id == org_id).order_by(Project.created_at.desc())
    )
    return [project_payload(db, org_id, project) for project in projects]


@projects_router.post("/projects", status_code=201)
def create_project(
    body: ProjectIn,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_writer),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    project = Project(
        id=uuid.uuid4(),
        organization_id=org_id,
        name=body.name.strip(),
        department=body.department,
        created_by=context.user.id,
    )
    db.add(project)
    db.flush()
    audit(
        db,
        "project.created",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="project",
        entity_id=str(project.id),
    )
    db.commit()
    return project_payload(db, org_id, project)


@projects_router.get("/projects/{projectId}")
def read_project(
    projectId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    project = get_owned(db, Project, org_id, projectId)
    payload = project_payload(db, org_id, project)
    processes = db.scalars(
        select(Process).where(Process.project_id == project.id).order_by(Process.created_at.desc())
    )
    payload["processes"] = [process_payload(db, process) for process in processes]
    return payload


@projects_router.patch("/projects/{projectId}")
def patch_project(
    body: ProjectPatch,
    projectId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_writer),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    if body.status is not None and context.role_in(org_id) not in {"owner", "admin"}:
        raise ApiError(403, "AUTH_FORBIDDEN", "Only organization managers can archive projects.")
    project = get_owned(db, Project, org_id, projectId)
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise ApiError(422, "VALIDATION_ERROR", "Provide at least one field to change.")
    for field, value in changes.items():
        setattr(project, field, value.strip() if isinstance(value, str) else value)
    db.flush()
    audit(
        db,
        "project.updated",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="project",
        entity_id=str(project.id),
        details={"fields": sorted(changes)},
    )
    db.commit()
    return project_payload(db, org_id, project)


@projects_router.post("/projects/{projectId}/processes", status_code=201)
def create_process(
    body: ProcessIn,
    projectId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_writer),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    project = get_owned(db, Project, org_id, projectId)
    if project.status != "active":
        raise ApiError(409, "PROJECT_ARCHIVED", "Create processes inside an active project.")
    process = Process(
        id=uuid.uuid4(),
        organization_id=org_id,
        project_id=project.id,
        name=body.name.strip(),
        created_by=context.user.id,
    )
    db.add(process)
    db.flush()
    audit(
        db,
        "process.created",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="process",
        entity_id=str(process.id),
    )
    db.commit()
    return process_payload(db, process)


@processes_router.get("/processes/{processId}")
def read_process(
    processId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    return process_payload(db, get_owned(db, Process, org_id, processId))


@processes_router.post("/processes/{processId}/intake")
def save_process_intake(
    body: IntakeIn,
    processId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_writer),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    process = get_owned(db, Process, org_id, processId)
    version = save_intake(db, org_id, context.user.id, process, body)
    db.commit()
    return {
        "version_id": str(version.id),
        "version_no": version.version_no,
        "review_status": "draft",
    }
