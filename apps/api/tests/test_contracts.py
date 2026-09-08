import json

from jsonschema.validators import validator_for
from openapi_spec_validator import validate

from aos_api.config import ROOT
from aos_api.main import create_app


def test_m5_openapi_contract():
    schema = create_app().openapi()
    validate(schema)
    assert set(schema["paths"]) == {
        "/analyses/{analysisId}",
        "/analyses/{analysisId}/opportunities",
        "/analyses/{analysisId}/report",
        "/analyses/{analysisId}/reports",
        "/auth/active-organization",
        "/auth/login",
        "/auth/logout",
        "/auth/me",
        "/auth/register",
        "/health/live",
        "/health/ready",
        "/opportunities/{opportunityId}",
        "/portfolio/opportunities",
            "/process-versions/{versionId}",
            "/process-versions/{versionId}/comments",
            "/process-versions/{versionId}/review",
        "/processes/{processId}",
        "/processes/{processId}/analyses",
        "/processes/{processId}/documents",
        "/processes/{processId}/intake",
        "/projects",
        "/projects/{projectId}",
        "/projects/{projectId}/processes",
        "/reports/{reportId}/pdf",
    }


def test_pack_json_schemas_are_well_formed():
    paths = sorted((ROOT / "schemas").glob("*.schema.json"))
    assert paths
    for path in paths:
        schema = json.loads(path.read_text())
        validator_for(schema).check_schema(schema)
