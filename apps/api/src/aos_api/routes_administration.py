import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from aos_api.errors import ApiError
from aos_api.models import Membership, User
from aos_api.routes_auth import (
    ROLE_ORDER,
    AuthContext,
    _audit,
    db_session,
    normalize_email,
    require_roles,
    tenant_context,
)

administration_router = APIRouter(tags=["administration"])
_owner = require_roles("owner")


class MemberIn(BaseModel):
    email: str
    role: str


class MemberRoleIn(BaseModel):
    role: str


def _validated_role(role: str) -> str:
    if role not in ROLE_ORDER:
        raise ApiError(422, "VALIDATION_ERROR", "Select a valid organization role.")
    return role


def _member_payload(membership: Membership, user: User) -> dict[str, object]:
    return {
        "id": str(membership.id),
        "user_id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "role": membership.role,
    }


@administration_router.get("/organization-members")
def list_members(
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_owner),
    db: Session = Depends(db_session),
) -> list[dict[str, object]]:
    rows = db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.organization_id == org_id)
        .order_by(User.display_name, User.email)
    )
    return [_member_payload(membership, user) for membership, user in rows]


@administration_router.post("/organization-members", status_code=201)
def add_member(
    body: MemberIn,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_owner),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    email = normalize_email(body.email)
    role = _validated_role(body.role)
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise ApiError(
            404,
            "USER_NOT_FOUND",
            "The user must create an account before they can be added to this organization.",
        )
    if db.scalar(
        select(Membership.id).where(
            Membership.organization_id == org_id,
            Membership.user_id == user.id,
        )
    ):
        raise ApiError(409, "MEMBER_EXISTS", "This user already belongs to the organization.")
    membership = Membership(id=uuid.uuid4(), organization_id=org_id, user_id=user.id, role=role)
    db.add(membership)
    _audit(
        db,
        "organization.member_added",
        org_id=org_id,
        actor_id=context.user.id,
        details={"member_id": str(user.id), "role": role},
    )
    db.commit()
    return _member_payload(membership, user)


@administration_router.patch("/organization-members/{membershipId}")
def change_member_role(
    membershipId: uuid.UUID,
    body: MemberRoleIn,
    org_id: uuid.UUID = Depends(tenant_context),
    context: AuthContext = Depends(_owner),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    role = _validated_role(body.role)
    membership = db.scalar(
        select(Membership).where(
            Membership.id == membershipId,
            Membership.organization_id == org_id,
        )
    )
    if membership is None:
        raise ApiError(404, "NOT_FOUND", "The requested resource was not found.")
    if membership.role == "owner" and role != "owner":
        owners = db.scalar(
            select(func.count())
            .select_from(Membership)
            .where(Membership.organization_id == org_id, Membership.role == "owner")
        )
        if owners == 1:
            raise ApiError(
                409,
                "LAST_OWNER",
                "Add another owner before changing the last owner's role.",
            )
    membership.role = role
    _audit(
        db,
        "organization.member_role_changed",
        org_id=org_id,
        actor_id=context.user.id,
        details={"member_id": str(membership.user_id), "role": role},
    )
    db.commit()
    user = db.get(User, membership.user_id)
    if user is None:
        raise ApiError(404, "NOT_FOUND", "The requested resource was not found.")
    return _member_payload(membership, user)
