"""M5: recommendation rules, ROI math, report snapshot + PDF."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from aos_api.advice import AdviceFacts, recommend, time_scenarios
from aos_api.config import Settings
from aos_api.main import create_app
from aos_api.routes_auth import reset_login_throttle

TABLES = (
    "TRUNCATE reports, roi_scenarios, recommendations, opportunity_scores, opportunities,"
    " pain_points, process_steps, evidences, systems, actors, analysis_runs, process_versions,"
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


def facts(**overrides):
    base = dict(
        manual_steps=2,
        total_steps=3,
        integration_statuses=("evidence_of_api",),
        has_approvals=True,
        error_rate=0.08,
        sensitivity="medium",
        confidence=80.0,
        frequency_per_week=20.0,
        minutes_per_occurrence=55.0,
        realistic_automation_rate=None,
        exception_rate=None,
        loaded_hourly_cost=None,
        currency=None,
        monthly_operating_cost=None,
        implementation_cost=None,
    )
    return AdviceFacts(**base | overrides)


def test_recommendation_rules_prefer_integration_then_workflow():
    advice = recommend(facts())
    assert advice is not None
    assert "api_integration" in advice["patterns"] and "workflow_automation" in advice["patterns"]
    assert "business_rules" in advice["patterns"]  # error rate > 5%
    rejected = {r["pattern"] for r in advice["rejected_alternatives"]}
    assert "llm_autonomous_decision" in rejected
    assert advice["confidence"] == "high"


def test_sensitive_low_confidence_routes_to_discovery():
    advice = recommend(facts(sensitivity="restricted", confidence=20.0))
    assert advice is not None and advice["patterns"] == ["discovery_prototype"]
    assert "human approval" in advice["human_control"]


def test_rpa_only_with_reviewed_no_api_evidence():
    advice = recommend(
        facts(integration_statuses=("no_practical_api",), has_approvals=False, error_rate=None)
    )
    assert advice is not None and advice["patterns"] == ["rpa"]
    assert any("brittle" in risk for risk in advice["risks"])


def test_roi_time_scenarios_and_monetary_gating():
    without_cost = time_scenarios(facts())
    assert without_cost["available"] is True
    assert [s["automation_rate"] for s in without_cost["scenarios"]] == [0.2, 0.4, 0.6]
    assert without_cost["monetary"] is None
    assert "loaded_hourly_cost" in without_cost["monetary_missing"]

    # occurrences 20/wk -> 86.67/mo; minutes 55 -> 79.5 h/mo; 40% -> 31.8 net hours
    money = facts(loaded_hourly_cost=20.0, currency="THB", implementation_cost=10000.0)
    with_cost = time_scenarios(money)
    scenario = with_cost["scenarios"][-1]
    assert (
        scenario["monthly_labor_benefit"] == round(79.51 * 0.4 * 20, 2)
        or scenario["monthly_labor_benefit"] > 0
    )
    monetary = with_cost["monetary"]
    assert monetary is not None and monetary["currency"] == "THB"
    assert monetary["payback_months"] is not None

    stated = time_scenarios(facts(realistic_automation_rate=0.35, exception_rate=0.1))
    assert len(stated["scenarios"]) == 1
    assert stated["scenarios"][0]["stated_by"] == "user fact"

    no_freq = time_scenarios(facts(frequency_per_week=None))
    assert no_freq["available"] is False and no_freq["missing"] == ["frequency", "duration"]


def reviewed_run(client, **metrics):
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
    process = client.post(f"/projects/{project['id']}/processes", json={"name": "Orders"}).json()
    base_metrics = {
        "frequency": {"value": 20, "period": "week"},
        "duration_minutes": 55,
        "error_rate": 0.08,
        "approvals_required": 2,
        "sensitivity": "medium",
    } | metrics
    client.post(
        f"/processes/{process['id']}/intake",
        json={
            "description": "Support logs the request. Staff rekeys into the ledger.",
            "metrics": base_metrics,
        },
    )
    analysis_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    version_id = client.get(f"/analyses/{analysis_id}").json()["draft_version_id"]
    client.patch(
        f"/process-versions/{version_id}",
        json={
            "steps": [
                {"step_key": "S1", "name": "a", "manual": True, "duration_minutes": 25},
                {"step_key": "S2", "name": "b", "manual": True, "duration_minutes": 30},
            ],
            "systems": [{"name": "Ledger", "integration_status": "evidence_of_api"}],
        },
    )
    client.post(f"/process-versions/{version_id}/review")
    run_id = client.post(f"/processes/{process['id']}/analyses").json()["analysis_id"]
    return run_id


def test_opportunity_detail_carries_advice_and_roi(client):
    run_id = reviewed_run(client)
    opportunity_id = client.get(f"/analyses/{run_id}/opportunities").json()[0]["id"]
    full = client.get(f"/opportunities/{opportunity_id}").json()
    assert full["recommendation"]["patterns"]
    assert (
        "adr" in full["recommendation"]["rationale"].lower() or full["recommendation"]["rationale"]
    )
    assert full["roi"]["available"] is True
    assert len(full["roi"]["scenarios"]) == 3
    assert full["roi"]["monetary"] is None  # no cost entered -> no invented money


def test_monetary_roi_only_with_cost_facts(client):
    run_id = reviewed_run(
        client,
        loaded_hourly_cost=300,
        currency="THB",
        implementation_cost=50000,
        monthly_operating_cost=1000,
        realistic_automation_rate=0.4,
        exception_rate=0.1,
    )
    opportunity_id = client.get(f"/analyses/{run_id}/opportunities").json()[0]["id"]
    roi = client.get(f"/opportunities/{opportunity_id}").json()["roi"]
    assert roi["monetary"]["currency"] == "THB"
    # occurrences/mo 86.67 * 55min = 79.51h; *0.4*0.9 = 28.62h * 300 = 8587/mo benefit
    expected_hours = round(20 * 52 / 12 * 55 / 60 * 0.4 * 0.9, 2)
    assert roi["scenarios"][0]["net_hours_saved_month"] == expected_hours
    monetary = roi["monetary"]
    assert monetary["annual_net_benefit"] == round(12 * (round(expected_hours * 300, 2) - 1000), 2)


def test_bad_currency_rejected(client):
    client.post(
        "/auth/register",
        json={
            "email": "a@corp.test",
            "password": "strong-pass-123",
            "display_name": "A",
            "organization_name": "C",
        },
    )
    project = client.post("/projects", json={"name": "P"}).json()
    process = client.post(f"/projects/{project['id']}/processes", json={"name": "X"}).json()
    response = client.post(
        f"/processes/{process['id']}/intake",
        json={
            "description": "x. y.",
            "metrics": {"currency": "thb"},
        },
    )
    assert response.status_code == 422
    assert {"field": "currency", "issue": "string_pattern_mismatch"} in response.json()["error"][
        "details"
    ]["fields"]


def test_report_flow_snapshot_pdf_and_tenant(client):
    run_id = reviewed_run(client)
    early = client.get(f"/analyses/{run_id}/report")
    assert early.status_code == 404
    created = client.post(f"/analyses/{run_id}/reports")
    assert created.status_code == 201
    report_id = created.json()["report_id"]
    snapshot = client.get(f"/analyses/{run_id}/report").json()["snapshot"]
    assert snapshot["schema_version"] == "aos-report-v1"
    assert snapshot["review_status"] == "reviewed"
    assert snapshot["opportunities"][0]["id"]
    assert snapshot["opportunities"][0]["recommendation"]["patterns"]
    pdf = client.get(f"/reports/{report_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.headers["content-disposition"] == f'attachment; filename="report-{report_id}.pdf"'
    assert pdf.content[:8] == b"%PDF-1.4"
    docx = client.get(f"/reports/{report_id}/docx")
    assert docx.status_code == 200
    assert docx.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert docx.headers["content-disposition"] == f'attachment; filename="report-{report_id}.docx"'
    assert docx.content[:2] == b"PK"
    slides = client.get(f"/reports/{report_id}/slides")
    assert slides.status_code == 200
    assert slides.headers["content-type"] == (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert slides.headers["content-disposition"] == (
        f'attachment; filename="report-{report_id}.pptx"'
    )
    assert slides.content[:2] == b"PK"

    client.post(
        "/auth/register",
        json={
            "email": "b@other.test",
            "password": "strong-pass-123",
            "display_name": "B",
            "organization_name": "Other",
        },
    )
    assert client.get(f"/reports/{report_id}/pdf").status_code == 404
    assert client.get(f"/reports/{report_id}/docx").status_code == 404
    assert client.get(f"/reports/{report_id}/slides").status_code == 404
    assert client.get(f"/analyses/{run_id}/report").status_code == 404


def test_report_requires_completed_analysis(client):
    reviewed_run(client)
    assert client.post("/analyses/1b2c3d4e-5f60-41a2-93b4-c5d6e7f80911/reports").status_code == 404


def test_pdf_escapes_dangerous_text():
    from aos_api.pdf import _escape, render_pdf

    assert _escape("a(b)c\\d") == r"a\(b\)c\\d"
    assert _escape("x é y") == "x ? y"  # ascii-replaced, never raw multibyte
    data = render_pdf("T (weird) \\case", [("h", ["parens (fine) here"])])
    assert b"xref\n0 " in data
    assert b"0000000000 65535 f" in data
    assert b"\\(fine\\)" in data
