"""M2 intake router: tenant-scoped project/process CRUD and guided intake."""

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.document_ingestion import MAX_BYTES, parse_document
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
from aos_api.models import Process, ProcessDocument, Project
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


@processes_router.post("/processes/{processId}/documents", status_code=201)
async def upload_process_document(
    processId: uuid.UUID,
    file: UploadFile = File(...),
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_writer),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    process = get_owned(db, Process, org_id, processId)
    content = await file.read(MAX_BYTES + 1)
    media_type, extracted_text, digest = parse_document(
        file.filename or "", file.content_type, content
    )
    document = ProcessDocument(
        id=uuid.uuid4(),
        organization_id=org_id,
        process_id=process.id,
        filename=file.filename or "",
        media_type=media_type,
        byte_size=len(content),
        sha256=digest,
        extracted_text=extracted_text,
        created_by=context.user.id,
    )
    db.add(document)
    audit(
        db,
        "process.document_uploaded",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="process_document",
        entity_id=str(document.id),
        details={"media_type": media_type, "byte_size": len(content)},
    )
    db.commit()
    return {
        "id": str(document.id),
        "filename": document.filename,
        "media_type": media_type,
        "byte_size": len(content),
        "extracted_text_chars": len(extracted_text),
    }


@processes_router.get("/processes/{processId}/documents")
def list_process_documents(
    processId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> list[dict[str, object]]:
    process = get_owned(db, Process, org_id, processId)
    documents = db.scalars(
        select(ProcessDocument)
        .where(ProcessDocument.organization_id == org_id, ProcessDocument.process_id == process.id)
        .order_by(ProcessDocument.created_at.desc())
    )
    return [
        {
            "id": str(document.id),
            "filename": document.filename,
            "media_type": document.media_type,
            "byte_size": document.byte_size,
            "extracted_text_chars": len(document.extracted_text),
            "created_at": document.created_at.isoformat(),
        }
        for document in documents
    ]


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
