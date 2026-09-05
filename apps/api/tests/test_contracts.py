import json

from jsonschema.validators import validator_for
from openapi_spec_validator import validate

from aos_api.config import ROOT
from aos_api.main import create_app


def test_m0_openapi_contract():
    schema = create_app().openapi()
    validate(schema)
    assert set(schema["paths"]) == {"/health/live", "/health/ready"}


def test_pack_json_schemas_are_well_formed():
    paths = sorted((ROOT / "schemas").glob("*.schema.json"))
    assert paths
    for path in paths:
        schema = json.loads(path.read_text())
        validator_for(schema).check_schema(schema)
