"""M4 opportunity engine: reviewed-version analysis, scoring states, detail."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from aos_api.config import Settings
from aos_api.main import create_app
from aos_api.routes_auth import reset_login_throttle

TABLES = (
    "TRUNCATE opportunity_scores, opportunities, pain_points, process_steps, evidences, systems,"
    " actors, analysis_runs, process_versions, processes, projects, audit_logs, sessions,"
    " memberships, users, organizations CASCADE"
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


def reviewed_process(client, **metric_overrides):
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
    process = client.post(f"/projects/{project['id']}/processes", json={"name": "Invoices"}).json()
    metrics = {
        "frequency": {"value": 20, "period": "week"},
        "duration_minutes": 45,
        "error_rate": 0.08,
        "approvals_required": 1,
        "sensitivity": "high",
        "strategic_alignment": 80,
        "integration_complexity": 40,
        "change_complexity": 30,
        "security_compliance_effort": 50,
        "exception_handling_complexity": 20,
    } | metric_overrides
    client.post(
        f"/processes/{process['id']}/intake",
        json={
            "description": "Staff copy invoice data into ERP. A manager approves payments.",
            "metrics": metrics,
        },
    )
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    version_id = client.get(f"/analyses/{analysis_id}").json()["draft_version_id"]
    client.patch(
        f"/process-versions/{version_id}",
        json={
            "steps": [
                {"step_key": "S1", "manual": True, "duration_minutes": 15},
                {"step_key": "S2", "manual": True, "duration_minutes": 30},
            ],
            "systems": [{"name": "ERP", "integration_status": "evidence_of_api"}],
        },
    )
    reviewed = client.post(f"/process-versions/{version_id}/review")
    assert reviewed.status_code == 200, reviewed.text
    return process


def test_opportunity_analysis_after_review(client):
    process = reviewed_process(client)
    run = client.post(f"/processes/{process['id']}/analyses")
    assert run.status_code == 202
    analysis_id = run.json()["analysis_id"]
    assert run.json()["status"] == "completed"
    detail = client.get(f"/analyses/{analysis_id}").json()
    assert detail["task"] == "opportunity_analysis"
    categories = {point["category"] for point in detail["pain_points"]}
    assert "repetitive_manual_work" in categories and "quality_rework" in categories
    opportunities = client.get(f"/analyses/{analysis_id}/opportunities").json()
    assert len(opportunities) == 1
    entry = opportunities[0]
    assert entry["result_state"] == "final"
    assert entry["total_score"] is not None
    assert entry["priority_band"] in {
        "investigate now",
        "high-priority candidate",
        "evaluate with additional evidence",
        "lower priority or redesign first",
    }
    assert entry["axes"]["impact"] is not None and entry["axes"]["effort"] is not None
    full = client.get(f"/opportunities/{entry['id']}").json()
    assert full["score"]["scoring_version"] == "aos-score-v1"
    assert set(full["score"]["dimensions"]) == {
        "business_value",
        "time_saving",
        "repetitiveness",
        "feasibility",
        "error_reduction",
        "integration_ease",
        "risk_safety",
    }
    assert full["score"]["dimension_evidence"]["risk_safety"]
    # sensitivity=high + approvals => risk>=70 => governance flag (ADR-008)
    assert full["scope"]["governance_review"] is True


def test_missing_evidence_never_fabricates(client):
    process = reviewed_process(
        client,
        frequency=None,
        duration_minutes=None,
        error_rate=None,
        approvals_required=None,
        sensitivity=None,
        strategic_alignment=None,
        integration_complexity=None,
        change_complexity=None,
        security_compliance_effort=None,
        exception_handling_complexity=None,
    )
    # steps still carry manual+duration from the patch; only metrics were stripped
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    # No frequency/error/approval evidence and every system has integration
    # evidence: an honest engine proposes nothing rather than fabricating a case.
    assert client.get(f"/analyses/{analysis_id}/opportunities").json() == []
    detail = client.get(f"/analyses/{analysis_id}").json()
    assert {point["category"] for point in detail["pain_points"]} == set()


def test_rerun_preserves_history(client):
    process = reviewed_process(client)
    first = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    second = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    assert first != second  # BR-010 versioned analysis
    assert client.get(f"/analyses/{first}").json()["status"] == "completed"


def test_cross_tenant_opportunities_denied(client):
    process = reviewed_process(client)
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    opportunity_id = client.get(f"/analyses/{analysis_id}/opportunities").json()[0]["id"]
    client.post(
        "/auth/register",
        json={
            "email": "b@other.test",
            "password": "strong-pass-123",
            "display_name": "Bob",
            "organization_name": "Other",
        },
    )
    assert client.get(f"/analyses/{analysis_id}/opportunities").status_code == 404
    assert client.get(f"/opportunities/{opportunity_id}").status_code == 404


def test_portfolio_is_tenant_scoped_and_filters_stored_scores(client):
    process = reviewed_process(client)
    client.post(f"/processes/{process['id']}/analyses")
    response = client.get("/portfolio/opportunities?min_score=1&min_confidence=1&page_size=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["page"] == 1 and payload["page_size"] == 1
    item = payload["items"][0]
    assert item["project_name"] == "Ops" and item["process_name"] == "Invoices"
    assert item["total_score"] >= 1 and item["axes"]["impact"] is not None
    assert (
        client.get("/portfolio/opportunities?category=repetitive_manual_work").json()["total"] == 1
    )
    assert client.get("/portfolio/opportunities?category=missing_evidence").json()["total"] == 0
    assert client.get("/portfolio/opportunities?min_score=101").status_code == 422
    client.post(
        "/auth/register",
        json={
            "email": "portfolio@other.test",
            "password": "strong-pass-123",
            "display_name": "Other",
            "organization_name": "Other",
        },
    )
    assert client.get("/portfolio/opportunities").json()["items"] == []


def test_vector_engine_matches_evals_golden_exactly():
    import json

    from aos_api.opportunity import DIMENSION_WEIGHTS, DimensionResult, total_score

    vectors = json.loads(
        (
            Settings.model_config
            and __import__("pathlib").Path(__file__).resolve().parents[3]
            / "evals"
            / "scoring_test_vectors.json"
        ).read_text()
    )
    for vector in vectors["vectors"]:
        scores = {name: DimensionResult(value, ()) for name, value in vector["dimensions"].items()}
        assert total_score(scores) == vector["expected_total"], vector["name"]
    assert sum(DIMENSION_WEIGHTS.values()) == 1.0


def test_two_step_save_keeps_evidence_of_api_and_manual(client):
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
    process = client.post(f"/projects/{project['id']}/processes", json={"name": "Invoices"}).json()
    client.post(
        f"/processes/{process['id']}/intake",
        json={
            "description": "Support receives a change request. Agents validate the order.",
            "metrics": {"frequency": {"value": 20, "period": "week"}, "error_rate": 0.08},
        },
    )
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    version_id = client.get(f"/analyses/{analysis_id}").json()["draft_version_id"]
    # save 1: minutes + manual + system name (as the web form does)
    save_one = client.patch(
        f"/process-versions/{version_id}",
        json={
            "steps": [
                {
                    "step_key": "S1",
                    "name": "x",
                    "duration_minutes": 20,
                    "manual": True,
                    "system": "ERP",
                },
                {"step_key": "S2", "name": "y", "duration_minutes": 35, "manual": True},
            ],
        },
    )
    assert save_one.status_code == 200, save_one.text
    detail = client.get(f"/process-versions/{version_id}").json()
    assert detail["systems"] == [{"name": "ERP", "integration_status": "unknown"}]
    # save 2: systems status upgraded (second web save)
    save_two = client.patch(
        f"/process-versions/{version_id}",
        json={
            "steps": [
                {
                    "step_key": "S1",
                    "name": "x",
                    "duration_minutes": 20,
                    "manual": True,
                    "system": "ERP",
                },
                {"step_key": "S2", "name": "y", "duration_minutes": 35, "manual": True},
            ],
            "systems": [{"name": "ERP", "integration_status": "evidence_of_api"}],
        },
    )
    assert save_two.status_code == 200, save_two.text
    assert client.get(f"/process-versions/{version_id}").json()["systems"] == [
        {"name": "ERP", "integration_status": "evidence_of_api"}
    ]
    client.post(f"/process-versions/{version_id}/review")
    run = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    opportunities = client.get(f"/analyses/{run}/opportunities").json()
    assert len(opportunities) == 1
    detail = client.get(f"/analyses/{run}").json()
    categories = {point["category"] for point in detail["pain_points"]}
    assert "repetitive_manual_work" in categories
    assert "integration_unknown" not in categories


def test_e2e_shaped_flow_reaches_final(client):
    """Mirror extraction.spec: 4 demo steps (2 from sentences, 2 from the
    metrics JSON line), durations only on S1/S2, metrics duration 55."""
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
    process = client.post(f"/projects/{project['id']}/processes", json={"name": "P"}).json()
    client.post(
        f"/processes/{process['id']}/intake",
        json={
            "description": (
                "Support receives a change request. Agents validate the order in ERP and confirm"
                " by email."
            ),
            "metrics": {
                "frequency": {"value": 20, "period": "week"},
                "error_rate": 0.08,
                "duration_minutes": 55,
            },
        },
    )
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    version_id = client.get(f"/analyses/{analysis_id}").json()["draft_version_id"]
    detail = client.get(f"/process-versions/{version_id}").json()
    assert [step["step_key"] for step in detail["steps"]] == ["S1", "S2"]
    client.patch(
        f"/process-versions/{version_id}",
        json={
            "steps": [
                {
                    "step_key": "S1",
                    "name": detail["steps"][0]["name"],
                    "duration_minutes": 20,
                    "manual": True,
                    "system": "ERP",
                },
                {
                    "step_key": "S2",
                    "name": detail["steps"][1]["name"],
                    "duration_minutes": 35,
                    "manual": True,
                },
            ],
        },
    )
    client.patch(
        f"/process-versions/{version_id}",
        json={
            "steps": [
                {"step_key": "S1", "name": "Support receives a change request."},
                {
                    "step_key": "S2",
                    "name": "Agents validate the order in ERP and confirm by email.",
                },
            ],
            "systems": [{"name": "ERP", "integration_status": "evidence_of_api"}],
        },
    )
    client.post(f"/process-versions/{version_id}/review")
    run_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    opportunities = client.get(f"/analyses/{run_id}/opportunities").json()
    assert opportunities, "expected a candidate"
    full = client.get(f"/opportunities/{opportunities[0]['id']}").json()
    missing = [name for name, value in full["score"]["dimensions"].items() if value is None]
    assert not missing, f"missing dimensions: {missing}"
    assert full["result_state"] == "final"
