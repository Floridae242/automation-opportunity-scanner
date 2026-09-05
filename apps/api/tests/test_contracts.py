import json

from jsonschema.validators import validator_for
from openapi_spec_validator import validate

from aos_api.config import ROOT
from aos_api.main import create_app


def test_m3_openapi_contract():
    schema = create_app().openapi()
    validate(schema)
    assert set(schema["paths"]) == {
        "/health/live",
        "/health/ready",
        "/auth/register",
        "/auth/login",
        "/auth/logout",
        "/auth/me",
        "/auth/active-organization",
        "/projects",
        "/projects/{projectId}",
        "/projects/{projectId}/processes",
        "/processes/{processId}",
        "/processes/{processId}/intake",
        "/processes/{processId}/analyses",
        "/analyses/{analysisId}",
        "/process-versions/{versionId}",
        "/process-versions/{versionId}/review",
        "/analyses/{analysisId}/opportunities",
        "/opportunities/{opportunityId}",
    }


def test_pack_json_schemas_are_well_formed():
    paths = sorted((ROOT / "schemas").glob("*.schema.json"))
    assert paths
    for path in paths:
        schema = json.loads(path.read_text())
        validator_for(schema).check_schema(schema)
