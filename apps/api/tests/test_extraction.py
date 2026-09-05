"""M3 extraction + review: happy path, failure handling, immutability."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from aos_api.config import Settings
from aos_api.extraction import DemoExtractionProvider, ExtractionError, validate_extraction
from aos_api.main import create_app
from aos_api.routes_auth import reset_login_throttle

TABLES = (
    "TRUNCATE process_steps, evidences, systems, actors, analysis_runs, process_versions,"
    " processes, projects, audit_logs, sessions, memberships, users, organizations CASCADE"
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
        yield test_client
    engine.dispose()


def prepared(client, email="a@corp.test"):
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "strong-pass-123",
            "display_name": "Ada",
            "organization_name": "Corp",
        },
    )
    project = client.post("/projects", json={"name": "Ops"}).json()
    process = client.post(f"/projects/{project['id']}/processes", json={"name": "Invoices"}).json()
    client.post(
        f"/processes/{process['id']}/intake",
        json={"description": "Finance receives invoices. Keys them into SAP.", "metrics": {}},
    )
    return process


def test_demo_provider_is_honest_about_unknowns():
    draft = validate_extraction(
        DemoExtractionProvider().extract("prompt", "Team reviews claims. Approves payouts.")
    )
    assert [step.step_key for step in draft.steps] == ["S1", "S2"]
    assert all(step.actor is None and step.duration_minutes is None for step in draft.steps)
    assert draft.steps[0].evidence_refs == ["intake"]
    assert draft.open_questions


def test_start_analysis_requires_intake(client):
    client.post(
        "/auth/register",
        json={
            "email": "a@corp.test",
            "password": "strong-pass-123",
            "display_name": "Ada",
            "organization_name": "Corp",
        },
    )
    project = client.post("/projects", json={"name": "Ops"}).json()
    process = client.post(f"/projects/{project['id']}/processes", json={"name": "Empty"}).json()
    response = client.post(f"/processes/{process['id']}/analyses")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "NOTHING_TO_EXTRACT"


def test_extraction_creates_draft_version_for_review(client):
    process = prepared(client)
    accepted = client.post(f"/processes/{process['id']}/analyses")
    assert accepted.status_code == 202, accepted.text
    analysis_id = accepted.json()["analysis_id"]
    status = client.get(f"/analyses/{analysis_id}").json()
    assert status["status"] == "completed", status
    assert status["provider"] == "demo"
    assert status["prompt_version"] == "aos-process-extract v1.0.0"
    assert status["schema_version"] == "process.schema.json@aos-v1"
    draft = client.get(f"/process-versions/{status['draft_version_id']}").json()
    assert draft["review_status"] == "draft"
    assert len(draft["steps"]) >= 2
    assert draft["steps"][0]["evidence_refs"] == ["intake"]
    assert draft["evidence"][0]["excerpt"].startswith("Finance receives invoices")
    stored = client.get(f"/processes/{process['id']}").json()
    assert stored["latest_version"]["review_status"] == "draft"
    statuses = [version["review_status"] for version in stored["versions"]]
    assert "superseded" in statuses  # original intake draft preserved as superseded


def test_idempotency_key_returns_same_run(client):
    process = prepared(client)
    first = client.post(
        f"/processes/{process['id']}/analyses", headers={"idempotency-key": "same-key-1"}
    ).json()
    second = client.post(
        f"/processes/{process['id']}/analyses", headers={"idempotency-key": "same-key-1"}
    ).json()
    assert first["analysis_id"] == second["analysis_id"]


class BadProvider:
    name = "test"
    model_id = "bad"

    def __init__(self, payload):
        self.payload = payload

    def extract(self, prompt, source):
        return self.payload


def test_invalid_schema_fails_without_data_loss(client, monkeypatch):
    process = prepared(client)
    from aos_api import routes_analysis

    monkeypatch.setattr(
        routes_analysis, "_provider_for", lambda request: BadProvider({"steps": []})
    )
    accepted = client.post(f"/processes/{process['id']}/analyses")
    analysis_id = accepted.json()["analysis_id"]
    status = client.get(f"/analyses/{analysis_id}").json()
    assert status["status"] == "failed"
    assert status["error_code"] == "AI_SCHEMA_INVALID"
    assert status["draft_version_id"] is None
    stored = client.get(f"/processes/{process['id']}").json()
    assert stored["latest_version"]["review_status"] == "draft"
    assert "Finance receives invoices" in stored["latest_version"]["source_summary"]


def test_unresolved_evidence_is_semantic_error(client, monkeypatch):
    process = prepared(client)
    from aos_api import routes_analysis

    payload = {
        "name": "Flow",
        "trigger": None,
        "outcome": None,
        "steps": [
            {
                "step_key": "S1",
                "name": "Do",
                "actor": None,
                "system": None,
                "manual": None,
                "duration_minutes": None,
                "evidence_refs": ["invented-span"],
            }
        ],
        "open_questions": [],
    }
    monkeypatch.setattr(routes_analysis, "_provider_for", lambda request: BadProvider(payload))
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    status = client.get(f"/analyses/{analysis_id}").json()
    assert (status["status"], status["error_code"]) == ("failed", "AI_SEMANTIC_INVALID")


def test_review_edit_and_immutability(client):
    process = prepared(client)
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    version_id = client.get(f"/analyses/{analysis_id}").json()["draft_version_id"]
    edited = client.patch(
        f"/process-versions/{version_id}",
        json={
            "steps": [
                {"step_key": "S1", "name": "Receive supplier invoices", "actor": "Finance team"}
            ]
        },
    )
    assert edited.status_code == 200, edited.text
    detail = client.get(f"/process-versions/{version_id}").json()
    assert detail["steps"][0]["name"] == "Receive supplier invoices"
    assert detail["steps"][0]["actor"] == "Finance team"
    reviewed = client.post(f"/process-versions/{version_id}/review")
    assert reviewed.status_code == 200
    assert reviewed.json()["review_status"] == "reviewed"
    locked = client.patch(
        f"/process-versions/{version_id}", json={"steps": [{"step_key": "S1", "name": "x"}]}
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "VERSION_IMMUTABLE"
    re_review = client.post(f"/process-versions/{version_id}/review")
    assert re_review.status_code == 409


def test_reviewer_role_can_review_but_viewer_cannot(client):
    from sqlalchemy import select
    from sqlalchemy.orm import sessionmaker

    from aos_api.models import Membership

    process = prepared(client)
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    version_id = client.get(f"/analyses/{analysis_id}").json()["draft_version_id"]
    engine = create_engine(os.environ["DATABASE_URL"])
    with sessionmaker(bind=engine)() as db:
        membership = db.scalar(select(Membership))
        membership.role = "viewer"
        db.commit()
    denied = client.post(f"/process-versions/{version_id}/review")
    assert denied.status_code == 403
    with sessionmaker(bind=engine)() as db:
        membership = db.scalar(select(Membership))
        membership.role = "reviewer"
        db.commit()
    engine.dispose()
    assert client.post(f"/process-versions/{version_id}/review").status_code == 200


def test_cross_tenant_analysis_ids_are_not_disclosed(client):
    process = prepared(client, "a@corp.test")
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    client.post(
        "/auth/register",
        json={
            "email": "b@other.test",
            "password": "strong-pass-123",
            "display_name": "Bob",
            "organization_name": "Other",
        },
    )
    assert client.get(f"/analyses/{analysis_id}").status_code == 404
    assert client.get(f"/process-versions/{uuid.uuid4()}").status_code == 404


def test_openai_provider_requires_full_configuration():
    from aos_api.extraction import build_provider

    with pytest.raises(ExtractionError):
        build_provider("openai_compatible", None, None, None)
    assert build_provider("openai_compatible", "http://gw.test/v1", "key", "m").model_id == "m"


def test_production_refuses_demo_provider():
    import types

    from aos_api.errors import ApiError
    from aos_api.routes_analysis import _provider_for

    settings = Settings(
        database_url="postgresql+psycopg://a:b@localhost/test",
        environment="production",
        ai_provider="demo",
        _env_file=None,
    )
    state = types.SimpleNamespace(settings=settings)
    request = types.SimpleNamespace(app=types.SimpleNamespace(state=state))
    with pytest.raises(ApiError) as err:
        _provider_for(request)
    assert (err.value.status, err.value.code) == (503, "AI_UNAVAILABLE")
