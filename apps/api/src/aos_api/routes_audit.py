"""Owner/admin read-only audit explorer."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from aos_api.models import AuditLog, User
from aos_api.routes_auth import AuthContext, db_session, require_roles, tenant_context

audit_router = APIRouter(tags=["administration"])
_admin = require_roles("owner", "admin")


@audit_router.get("/audit-events")
def list_audit_events(
    limit: int = Query(default=50, ge=1, le=200),
    org_id: uuid.UUID = Depends(tenant_context),
    _context: AuthContext = Depends(_admin),
    db: Session = Depends(db_session),
) -> list[dict[str, object]]:
    events = db.execute(
        select(AuditLog, User.display_name)
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .where(AuditLog.organization_id == org_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": str(event.id),
            "action": event.action,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "actor": actor_name,
            "details": event.metadata_json,
            "created_at": event.created_at.isoformat(),
        }
        for event, actor_name in events
    ]
