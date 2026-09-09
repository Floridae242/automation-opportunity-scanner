"""M1 authentication, session lifecycle, RBAC and tenant-context primitives."""

import hashlib
import re
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from aos_api.auth import (
    COOKIE_NAME,
    hash_password,
    new_session_token,
    session_expires_at,
    verify_password,
)
from aos_api.errors import ApiError
from aos_api.models import AuditLog, Membership, Organization, User
from aos_api.models import Session as UserSession

EMAIL_RE = re.compile(r"^[^@\s]{1,200}@[^@\s.]+(\.[^@\s.]+)+$")
ROLE_ORDER = {"owner": 5, "admin": 4, "analyst": 3, "reviewer": 2, "viewer": 1}
WRITE_ROLES = ("owner", "admin", "analyst")
LOGIN_WINDOW_SECONDS = 60
LOGIN_MAX_FAILURES = 10
_login_attempts: dict[str, list[float]] = {}


def _now() -> datetime:
    return datetime.now(UTC)


def normalize_email(raw: str) -> str:
    email = raw.strip().lower()
    if not EMAIL_RE.fullmatch(email) or len(email) > 320:
        raise ApiError(422, "VALIDATION_ERROR", "A valid email is required.")
    return email


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: UserSession
    memberships: list[Membership]

    def role_in(self, organization_id: uuid.UUID) -> str | None:
        for membership in self.memberships:
            if membership.organization_id == organization_id:
                return membership.role
        return None

    @property
    def active_organization_id(self) -> uuid.UUID | None:
        return self.session.organization_id


def _db(request: Request) -> Session:
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise ApiError(503, "SERVICE_UNAVAILABLE", "Identity storage is not available.")
    return cast(Callable[[], Session], factory)()


def db_session(request: Request) -> Iterator[Session]:
    session = _db(request)
    try:
        yield session
    finally:
        session.close()


def auth_context(request: Request, db: Session = Depends(db_session)) -> AuthContext:
    token = request.cookies.get(COOKIE_NAME, "")
    if not token:
        raise ApiError(401, "AUTH_UNAUTHENTICATED", "Authentication is required.")
    record = db.scalar(select(UserSession).where(UserSession.token_hash == _digest(token)))
    if record is None or record.revoked_at is not None or _as_utc(record.expires_at) < _now():
        raise ApiError(401, "AUTH_UNAUTHENTICATED", "Session is invalid or expired.")
    user = db.get(User, record.user_id)
    if user is None:
        raise ApiError(401, "AUTH_UNAUTHENTICATED", "Session is invalid or expired.")
    memberships = list(
        db.scalars(
            select(Membership).where(Membership.user_id == user.id).order_by(Membership.role)
        )
    )
    context = AuthContext(user=user, session=record, memberships=memberships)
    request.state.auth = context
    return context


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def require_roles(*roles: str) -> Callable[..., AuthContext]:
    allowed = set(roles)

    def guard(context: AuthContext = Depends(auth_context)) -> AuthContext:
        org_id = context.active_organization_id
        role = context.role_in(org_id) if org_id else None
        if role is None or role not in allowed:
            raise ApiError(403, "AUTH_FORBIDDEN", "Your role cannot perform this action.")
        return context

    return guard


def tenant_context(context: AuthContext = Depends(auth_context)) -> uuid.UUID:
    org_id = context.active_organization_id
    if org_id is None or context.role_in(org_id) is None:
        raise ApiError(401, "AUTH_NO_ORGANIZATION", "Select an active organization first.")
    return org_id


def _audit(
    db: Session,
    action: str,
    *,
    org_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditLog(
            id=uuid.uuid4(),
            organization_id=org_id,
            actor_user_id=actor_id,
            action=action,
            metadata_json=details or {},
        )
    )


def _issue_session(db: Session, user_id: uuid.UUID, org_id: uuid.UUID | None) -> str:
    token, token_hash = new_session_token()
    db.add(
        UserSession(
            id=uuid.uuid4(),
            token_hash=token_hash,
            user_id=user_id,
            organization_id=org_id,
            expires_at=session_expires_at(),
        )
    )
    return token


def _set_cookie(request: Request, response: Response, token: str) -> None:
    secure = getattr(request.app.state.settings, "environment", "development") == "production"
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=int(session_expires_at().timestamp() - _now().timestamp()),
        path="/",
    )


def _me_payload(db: Session, context: AuthContext) -> dict[str, object]:
    orgs = {
        organization.id: organization.name
        for organization in db.scalars(
            select(Organization).where(
                Organization.id.in_([m.organization_id for m in context.memberships])
            )
        )
    }
    return {
        "user": {
            "id": str(context.user.id),
            "email": context.user.email,
            "display_name": context.user.display_name,
        },
        "active_organization_id": (
            str(context.active_organization_id) if context.active_organization_id else None
        ),
        "memberships": [
            {
                "organization_id": str(m.organization_id),
                "organization_name": orgs.get(m.organization_id, ""),
                "role": m.role,
            }
            for m in context.memberships
        ],
    }


class RegisterIn(BaseModel):
    email: str
    password: str = Field(min_length=10, max_length=1024)
    display_name: str = Field(min_length=1, max_length=200)
    organization_name: str = Field(min_length=1, max_length=200)


class LoginIn(BaseModel):
    email: str
    password: str = Field(min_length=1, max_length=1024)


class SwitchIn(BaseModel):
    organization_id: uuid.UUID


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(
    body: RegisterIn, request: Request, response: Response, db: Session = Depends(db_session)
) -> dict[str, object]:
    email = normalize_email(body.email)
    if db.scalar(select(func.count()).select_from(User).where(User.email == email)):
        raise ApiError(409, "EMAIL_IN_USE", "An account with this email already exists.")
    user = User(
        id=uuid.uuid4(),
        auth_subject=f"local:{email}",
        email=email,
        display_name=body.display_name.strip(),
        password_hash=hash_password(body.password),
    )
    organization = Organization(id=uuid.uuid4(), name=body.organization_name.strip())
    db.add(user)
    db.add(organization)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "EMAIL_IN_USE", "An account with this email already exists.") from None
    db.add(
        Membership(id=uuid.uuid4(), organization_id=organization.id, user_id=user.id, role="owner")
    )
    token = _issue_session(db, user.id, organization.id)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, "EMAIL_IN_USE", "An account with this email already exists.") from None
    _audit(db, "auth.register", org_id=organization.id, actor_id=user.id)
    db.commit()
    _set_cookie(request, response, token)
    return {
        "user": {"id": str(user.id), "email": email, "display_name": user.display_name},
        "active_organization_id": str(organization.id),
        "memberships": [
            {
                "organization_id": str(organization.id),
                "organization_name": organization.name,
                "role": "owner",
            }
        ],
    }


@router.post("/login")
def login(
    body: LoginIn, request: Request, response: Response, db: Session = Depends(db_session)
) -> dict[str, object]:
    email = normalize_email(body.email)
    _throttle_login(email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(body.password, user.password_hash):
        record_login_failure(email)
        _audit(db, "auth.login_failed")
        db.commit()
        raise ApiError(401, "AUTH_INVALID", "Email or password is incorrect.")
    memberships = list(db.scalars(select(Membership).where(Membership.user_id == user.id)))
    token = _issue_session(db, user.id, memberships[0].organization_id if memberships else None)
    _audit(
        db,
        "auth.login",
        org_id=memberships[0].organization_id if memberships else None,
        actor_id=user.id,
    )
    db.commit()
    _set_cookie(request, response, token)
    record = _session_by_token(db, token)
    if record is None:
        raise ApiError(503, "SERVICE_UNAVAILABLE", "Identity storage is not available.")
    context = AuthContext(user=user, session=record, memberships=memberships)
    return _me_payload(db, context)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(db_session)) -> None:
    token = request.cookies.get(COOKIE_NAME, "")
    record = (
        db.scalar(select(UserSession).where(UserSession.token_hash == _digest(token)))
        if token
        else None
    )
    if record is not None and record.revoked_at is None:
        record.revoked_at = _now()

        _audit(db, "auth.logout", org_id=record.organization_id, actor_id=record.user_id)
        db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me")
def me(
    request: Request,
    context: AuthContext = Depends(auth_context),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    return _me_payload(db, context)


@router.get("/sso/status")
def sso_status(
    request: Request,
    context: AuthContext = Depends(require_roles("owner")),
) -> dict[str, object]:
    settings = request.app.state.settings
    if settings is None:
        raise ApiError(503, "SERVICE_UNAVAILABLE", "Identity configuration is unavailable.")
    missing = settings.sso_missing_settings()
    return {
        "provider": "openid_connect",
        "configured": not missing,
        "missing": missing,
    }


@router.post("/active-organization")
def switch_organization(
    body: SwitchIn,
    request: Request,
    response: Response,
    context: AuthContext = Depends(auth_context),
    db: Session = Depends(db_session),
) -> dict[str, object]:
    membership = next(
        (m for m in context.memberships if m.organization_id == body.organization_id), None
    )
    if membership is None:
        raise ApiError(404, "NOT_FOUND", "Organization not found for this account.")
    context.session.revoked_at = _now()
    token = _issue_session(db, context.user.id, body.organization_id)
    _audit(db, "auth.organization_switched", org_id=body.organization_id, actor_id=context.user.id)
    db.commit()
    _set_cookie(request, response, token)
    return {
        "user": {
            "id": str(context.user.id),
            "email": context.user.email,
            "display_name": context.user.display_name,
        },
        "active_organization_id": str(body.organization_id),
        "memberships": _me_payload(db, context)["memberships"],
    }


def _session_by_token(db: Session, token: str) -> UserSession | None:
    return db.scalar(select(UserSession).where(UserSession.token_hash == _digest(token)))


def _throttle_login(email: str) -> None:
    now = _now().timestamp()
    attempts = [at for at in _login_attempts.get(email, []) if now - at < LOGIN_WINDOW_SECONDS]
    if len(attempts) >= LOGIN_MAX_FAILURES:
        raise ApiError(429, "AUTH_RATE_LIMITED", "Too many login attempts. Try again shortly.")
    _login_attempts[email] = attempts


def record_login_failure(email: str) -> None:
    _login_attempts.setdefault(email, []).append(_now().timestamp())


def reset_login_throttle() -> None:
    _login_attempts.clear()


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)
