"""M2 intake: tenant isolation, RBAC, versioning, and payload validation."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from aos_api.config import Settings
from aos_api.main import create_app
from aos_api.models import AuditLog, Membership
from aos_api.routes_auth import reset_login_throttle

TABLES = (
    "TRUNCATE process_versions, processes, projects, audit_logs, sessions, memberships, users,"
    " organizations CASCADE"
)


class Probe:
    def check(self):
        return True

    def close(self):
        pass


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
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database ending _test")
    settings = Settings(environment="test")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.exec_driver_sql(TABLES)
    app = create_app(probe=Probe(), settings=settings, engine=engine)
    with TestClient(app, base_url="http://test") as test_client:
        test_client.engine = engine  # type: ignore[attr-defined]
        yield test_client
    engine.dispose()


def register(client, email, name="Ada", org="Corp"):
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "strong-pass-123",
            "display_name": name,
            "organization_name": org,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def set_role(client, user_id, role):
    with sessionmaker(bind=client.engine)() as db:  # type: ignore[attr-defined]
        membership = db.scalar(select(Membership).where(Membership.user_id == user_id))
        membership.role = role
        db.commit()


def create_project(client, name="Claims", department="Ops"):
    response = client.post("/projects", json={"name": name, "department": department})
    assert response.status_code == 201, response.text
    return response.json()


def create_process(client, project_id, name="Verify claims"):
    response = client.post(f"/projects/{project_id}/processes", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def save_intake(
    client, process_id, description="Team receives emails, checks policy manually.", **metrics
):
    response = client.post(
        f"/processes/{process_id}/intake",
        json={"description": description, "metrics": metrics},
    )
    return response


def test_project_and_process_crud_flow(client):
    me = register(client, "a@corp.test")
    project = create_project(client)
    assert project["status"] == "active" and project["process_count"] == 0
    process = create_process(client, project["id"])
    assert process["versions"] == [] and process["latest_version"] is None
    renamed = client.patch(f"/projects/{project['id']}", json={"name": "Claims 2026"})
    assert renamed.status_code == 200 and renamed.json()["name"] == "Claims 2026"
    detail = client.get(f"/projects/{project['id']}").json()
    assert detail["processes"][0]["name"] == "Verify claims"
    assert client.get("/projects").json()[0]["process_count"] == 1
    assert client.get("/auth/me").json()["user"]["id"] == me["user"]["id"]


def test_tenant_isolation_is_non_disclosing(client):
    register(client, "a@corp.test", org="Corp")
    project = create_project(client)
    process = create_process(client, project["id"])
    register(client, "b@other.test", org="Other")
    for response in (
        client.get(f"/projects/{project['id']}"),
        client.patch(f"/projects/{project['id']}", json={"name": "stolen"}),
        client.post(f"/projects/{project['id']}/processes", json={"name": "x"}),
        client.get(f"/processes/{process['id']}"),
        save_intake(client, process["id"], "cross tenant attempt"),
    ):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
    assert client.get("/projects").json() == []


def test_intake_versioning_and_supersede(client):
    register(client, "a@corp.test")
    project = create_project(client)
    process = create_process(client, project["id"])
    first = save_intake(
        client,
        process["id"],
        "v1 description",
        frequency={"value": 40, "period": "week"},
        duration_minutes=25.5,
        systems=["Outlook", "SAP"],
        sensitivity="high",
        error_rate=0.02,
    )
    assert first.status_code == 200, first.text
    assert first.json()["version_no"] == 1
    second = save_intake(client, process["id"], "v2 description")
    assert second.json()["version_no"] == 2
    stored = client.get(f"/processes/{process['id']}").json()
    versions = stored["versions"]
    assert [v["version_no"] for v in versions] == [2, 1]
    assert versions[1]["review_status"] == "superseded"
    assert versions[0]["review_status"] == "draft"
    assert versions[1]["metrics"]["frequency"] == {"value": 40, "period": "week"}
    assert versions[1]["metrics"]["error_rate"] == 0.02
    assert "sla" not in versions[1]["metrics"]  # unknown stays null, never fabricated
    assert versions[0]["metrics"] == {}


def test_process_version_comments_are_tenant_scoped_and_audited(client):
    user = register(client, "comments@corp.test", name="Commenter")
    project = create_project(client)
    process = create_process(client, project["id"])
    version_id = save_intake(client, process["id"]).json()["version_id"]
    first = client.post(
        f"/process-versions/{version_id}/comments", json={"body": "  Please verify the handoff.  "}
    )
    assert first.status_code == 201, first.text
    assert first.json()["body"] == "Please verify the handoff."
    assert first.json()["author"]["id"] == user["user"]["id"]
    second = client.post(
        f"/process-versions/{version_id}/comments", json={"body": "Reviewed by operations."}
    )
    assert second.status_code == 201
    listed = client.get(f"/process-versions/{version_id}/comments")
    assert [item["body"] for item in listed.json()] == [
        "Please verify the handoff.",
        "Reviewed by operations.",
    ]
    with sessionmaker(bind=client.engine)() as db:  # type: ignore[attr-defined]
        entry = db.scalar(select(AuditLog).where(AuditLog.action == "process_version.comment_created"))
        assert entry is not None
        assert entry.metadata_json["body_length"] == len("Please verify the handoff.")
        assert "body" not in entry.metadata_json


def test_process_version_comments_validate_role_and_tenant(client):
    user = register(client, "viewer@corp.test")
    project = create_project(client)
    process = create_process(client, project["id"])
    version_id = save_intake(client, process["id"]).json()["version_id"]
    for body in ({"body": "   "}, {"body": "x" * 2001}, {"body": "valid", "role": "owner"}):
        assert client.post(f"/process-versions/{version_id}/comments", json=body).status_code == 422
    set_role(client, user["user"]["id"], "viewer")
    assert client.post(f"/process-versions/{version_id}/comments", json={"body": "blocked"}).status_code == 403
    register(client, "other@tenant.test", org="Other")
    assert client.get(f"/process-versions/{version_id}/comments").status_code == 404
    assert client.post(f"/process-versions/{version_id}/comments", json={"body": "blocked"}).status_code == 404


def test_metrics_validation_rejects_fabrication(client):
    register(client, "a@corp.test")
    project = create_project(client)
    process = create_process(client, project["id"])
    for bad in (
        {"error_rate": 5},  # percentages are 0-1 decimals
        {"frequency": {"value": 0, "period": "week"}},
        {"frequency": {"value": 1, "period": "fortnight"}},
        {"duration_minutes": 30, "unlisted_field": 1},
        {"systems": ["x"] * 51},
    ):
        response = save_intake(client, process["id"], "attempt", **bad)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_roles_enforced_server_side(client):
    me = register(client, "a@corp.test")
    project = create_project(client)
    set_role(client, me["user"]["id"], "viewer")
    forbidden = client.post("/projects", json={"name": "nope"})
    assert forbidden.status_code == 403
    forbidden_patch = client.patch(f"/projects/{project['id']}", json={"name": "renamed"})
    assert forbidden_patch.status_code == 403
    assert client.get("/projects").status_code == 200  # reads stay open to members

    set_role(client, me["user"]["id"], "analyst")
    assert client.post("/projects", json={"name": "allowed"}).status_code == 201
    archived = client.patch(f"/projects/{project['id']}", json={"status": "archived"})
    assert archived.status_code == 403  # archive needs owner/admin
    set_role(client, me["user"]["id"], "owner")
    assert (
        client.patch(f"/projects/{project['id']}", json={"status": "archived"}).status_code == 200
    )
    blocked = client.post(f"/projects/{project['id']}/processes", json={"name": "late"})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "PROJECT_ARCHIVED"


def test_audit_events_recorded_for_intake(client):
    register(client, "a@corp.test")
    project = create_project(client)
    process = create_process(client, project["id"])
    save_intake(client, process["id"], "audited intake")
    with sessionmaker(bind=client.engine)() as db:  # type: ignore[attr-defined]
        actions = [entry.action for entry in db.scalars(select(AuditLog).order_by(AuditLog.action))]
        entry = db.scalar(select(AuditLog).where(AuditLog.action == "process.intake_saved"))
    assert sorted(actions) == [
        "auth.register",
        "process.created",
        "process.intake_saved",
        "project.created",
    ]
    assert entry is not None and entry.entity_type == "process_version"
    assert entry.metadata_json == {"version_no": 1}


def test_document_upload_is_bounded_audited_and_tenant_scoped(client):
    register(client, "a@corp.test")
    project = create_project(client)
    process = create_process(client, project["id"])
    uploaded = client.post(
        f"/processes/{process['id']}/documents",
        files={"file": ("notes.txt", b"Copy invoice values into ERP.", "text/plain")},
    )
    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["extracted_text_chars"] == len("Copy invoice values into ERP.")
    documents = client.get(f"/processes/{process['id']}/documents")
    assert documents.status_code == 200 and documents.json()[0]["filename"] == "notes.txt"
    register(client, "b@other.test", org="Other")
    assert client.get(f"/processes/{process['id']}/documents").status_code == 404


def test_document_upload_rejects_unsupported_or_empty_content(client):
    register(client, "a@corp.test")
    project = create_project(client)
    process = create_process(client, project["id"])
    for filename, content, media_type, status in (
        ("script.exe", b"data", "application/octet-stream", 415),
        ("notes.txt", b"", "text/plain", 422),
        ("bad.pdf", b"not a pdf", "application/pdf", 415),
    ):
        response = client.post(
            f"/processes/{process['id']}/documents",
            files={"file": (filename, content, media_type)},
        )
        assert response.status_code == status
