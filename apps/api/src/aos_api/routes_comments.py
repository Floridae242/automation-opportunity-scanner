"""Tenant-scoped, append-only comments for a process-version review discussion."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.intake import audit, get_owned
from aos_api.models import ProcessVersion, ProcessVersionComment, User
from aos_api.routes_auth import AuthContext, db_session, require_roles, tenant_context

comments_router = APIRouter(tags=["comments"])
_commenter = require_roles("owner", "admin", "analyst", "reviewer")


class CommentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(min_length=1, max_length=2000)

    @field_validator("body")
    @classmethod
    def meaningful_body(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Comment body cannot be blank.")
        return value


def _payload(comment: ProcessVersionComment, author: User) -> dict[str, object]:
    return {
        "id": str(comment.id),
        "body": comment.body,
        "created_at": comment.created_at.isoformat(),
        "author": {"id": str(author.id), "display_name": author.display_name},
    }


@comments_router.get("/process-versions/{versionId}/comments")
def list_comments(
    versionId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    db: Session = Depends(db_session),
) -> list[dict[str, object]]:
    version = get_owned(db, ProcessVersion, org_id, versionId)
    statement = (
        select(ProcessVersionComment, User)
        .join(User, User.id == ProcessVersionComment.created_by)
        .where(
            ProcessVersionComment.organization_id == org_id,
            ProcessVersionComment.process_version_id == version.id,
        )
        .order_by(ProcessVersionComment.created_at, ProcessVersionComment.id)
    )
    rows = db.execute(statement).all()
    return [_payload(comment, author) for comment, author in rows]


@comments_router.post("/process-versions/{versionId}/comments", status_code=201)
def create_comment(
    body: CommentIn,
    versionId: uuid.UUID,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_commenter),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    version = get_owned(db, ProcessVersion, org_id, versionId)
    comment = ProcessVersionComment(
        id=uuid.uuid4(),
        organization_id=org_id,
        process_version_id=version.id,
        created_by=context.user.id,
        body=body.body,
    )
    db.add(comment)
    db.flush()
    audit(
        db,
        "process_version.comment_created",
        org_id=org_id,
        actor_id=context.user.id,
        entity_type="process_version_comment",
        entity_id=str(comment.id),
        details={"process_version_id": str(version.id), "body_length": len(comment.body)},
    )
    db.commit()
    return _payload(comment, context.user)
