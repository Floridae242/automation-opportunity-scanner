"""M1 identity: unit + postgres integration coverage (EPIC-02)."""

import os
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from aos_api.auth import hash_password, verify_password
from aos_api.config import Settings
from aos_api.errors import ApiError
from aos_api.main import create_app
from aos_api.models import Membership, User
from aos_api.models import Session as UserSession
from aos_api.routes_auth import (
    AuthContext,
    normalize_email,
    require_roles,
    reset_login_throttle,
    tenant_context,
)


class Probe:
    def check(self):
        return True

    def close(self):
        pass


def test_password_roundtrip_and_format():
    stored = hash_password("correct horse battery staple")
    assert stored.startswith("scrypt$16384$8$1$")
    assert verify_password("correct horse battery staple", stored)
    assert not verify_password("wrong", stored)
    assert not verify_password("x", None)
    assert not verify_password("x", "argon2$junk")
    with pytest.raises(ValueError):
        hash_password("short")


def test_email_normalization():
    assert normalize_email("  Bob@Example.COM ") == "bob@example.com"
    for bad in ["nope", "a@b", "@x.io", "a b@c.io"]:
        with pytest.raises(ApiError) as err:
            normalize_email(bad)
        assert err.value.status == 422


def _context(active_org, role):
    user = User(id=uuid.uuid4(), auth_subject="x", email="a@b.io", display_name="A")
    session = UserSession(id=uuid.uuid4(), organization_id=active_org)
    memberships = (
        [Membership(id=uuid.uuid4(), organization_id=active_org, user_id=user.id, role=role)]
        if active_org
        else []
    )
    return AuthContext(user=user, session=session, memberships=memberships)


def test_require_roles_and_tenant_context():
    org = uuid.uuid4()
    guard = require_roles("owner", "admin")
    assert guard(_context(org, "owner")).active_organization_id == org
    with pytest.raises(ApiError) as err:
        guard(_context(org, "viewer"))
    assert err.value.status == 403
    with pytest.raises(ApiError) as err:
        tenant_context(_context(None, None))
    assert (err.value.status, err.value.code) == (401, "AUTH_NO_ORGANIZATION")


def _test_settings():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database ending _test")
    os.environ["DATABASE_URL"] = database_url
    return Settings(environment="test")


@pytest.fixture(scope="module", autouse=True)
def migrate_test_db():
    if not os.environ.get("TEST_DATABASE_URL"):
        return
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
    from alembic import command

    from aos_api.db import migration_config

    command.upgrade(migration_config(), "head")


@pytest.fixture()
def client():
    reset_login_throttle()
    settings = _test_settings()
    engine = create_engine(settings.database_url.get_secret_value())
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "TRUNCATE audit_logs, sessions, memberships, users, organizations CASCADE"
        )
    app = create_app(probe=Probe(), settings=settings, engine=engine)
    with TestClient(app, base_url="http://test") as test_client:
        yield test_client
    engine.dispose()


def register(client, email="owner@corp.test", org="Corp", password="strong-pass-123"):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "display_name": "Ada",
            "organization_name": org,
        },
    )
    assert response.status_code == 201, response.text
    return response


def test_register_login_me_logout_flow(client):
    body = register(client).json()
    assert body["memberships"] == [
        {
            "organization_id": body["active_organization_id"],
            "organization_name": "Corp",
            "role": "owner",
        }
    ]
    assert client.get("/auth/me").json()["user"]["email"] == "owner@corp.test"
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401
    client.cookies.clear()
    login = client.post(
        "/auth/login", json={"email": "owner@corp.test", "password": "strong-pass-123"}
    )
    assert login.status_code == 200
    assert login.json()["active_organization_id"] == body["active_organization_id"]


def test_login_failure_envelope_and_throttle(client):
    register(client)
    client.post("/auth/logout")
    client.cookies.clear()
    for _ in range(10):
        bad = client.post(
            "/auth/login", json={"email": "owner@corp.test", "password": "nope-nope-nope"}
        )
        assert bad.status_code == 401
    envelope = bad.json()["error"]
    assert envelope["code"] == "AUTH_INVALID"
    assert set(envelope) == {"code", "message", "request_id", "details"}
    assert "nope" not in bad.text
    limited = client.post(
        "/auth/login", json={"email": "owner@corp.test", "password": "nope-nope-nope"}
    )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "AUTH_RATE_LIMITED"


def test_duplicate_email_conflict(client):
    register(client)
    dup = client.post(
        "/auth/register",
        json={
            "email": "OWNER@corp.test",
            "password": "strong-pass-123",
            "display_name": "Evil",
            "organization_name": "Other",
        },
    )
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "EMAIL_IN_USE"


def test_validation_errors_name_the_field_without_leaking_values(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "v@corp.test",
            "password": "short",
            "display_name": "Ada",
            "organization_name": "Corp",
        },
    )
    assert response.status_code == 422
    envelope = response.json()["error"]
    assert envelope["code"] == "VALIDATION_ERROR"
    assert envelope["details"]["fields"] == [{"field": "password", "issue": "string_too_short"}]
    assert '"short"' not in response.text  # never echo submitted values back


def test_unauthenticated_and_invalid_session(client):
    assert client.get("/auth/me").json()["error"]["code"] == "AUTH_UNAUTHENTICATED"
    register(client)
    settings = Settings(environment="test")
    engine = create_engine(settings.database_url.get_secret_value())
    factory = sessionmaker(bind=engine)
    with factory() as db:
        record = db.scalar(select(UserSession))
        record.expires_at = record.expires_at - timedelta(days=8)
        db.commit()
    engine.dispose()
    assert client.get("/auth/me").status_code == 401


def test_organization_switch_rotates_and_denies_foreign_org(client):
    body = register(client).json()
    org_a = uuid.UUID(body["active_organization_id"])
    assert client.get("/auth/me").json()["active_organization_id"] == str(org_a)
    settings = Settings(environment="test")
    engine = create_engine(settings.database_url.get_secret_value())
    factory = sessionmaker(bind=engine)
    with factory() as db:
        user = db.scalar(select(User))
        from aos_api.models import Organization

        other_org_id = uuid.uuid4()
        db.add(Organization(id=other_org_id, name="Second"))
        db.flush()
        db.add(
            Membership(
                id=uuid.uuid4(), organization_id=other_org_id, user_id=user.id, role="analyst"
            )
        )
        db.commit()
    engine.dispose()

    old_token = client.cookies.get("aos_session")
    switched = client.post("/auth/active-organization", json={"organization_id": str(other_org_id)})
    assert switched.status_code == 200
    assert switched.json()["active_organization_id"] == str(other_org_id)
    assert client.cookies.get("aos_session") != old_token
    assert client.get("/auth/me").json()["active_organization_id"] == str(other_org_id)

    stale = TestClient(
        create_app(probe=Probe(), settings=settings, engine=None), base_url="http://test"
    )
    stale.cookies.set("aos_session", old_token)
    assert stale.get("/auth/me").status_code == 401

    stranger = uuid.uuid4()
    denied = client.post("/auth/active-organization", json={"organization_id": str(stranger)})
    assert denied.status_code == 404
    assert denied.json()["error"]["code"] == "NOT_FOUND"
