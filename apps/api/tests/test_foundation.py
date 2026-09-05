from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from aos_api.ai import FakeProvider
from aos_api.config import Settings
from aos_api.main import create_app


class Probe:
    def __init__(self, ready=True):
        self.ready = ready
        self.closed = False

    def check(self):
        return self.ready

    def close(self):
        self.closed = True


def test_health_and_cleanup():
    probe = Probe()
    with TestClient(create_app(probe=probe)) as client:
        response = client.get("/health/live", headers={"x-request-id": "valid-123"})
        assert response.json() == {"status": "ok"}
        assert response.headers["x-request-id"] == "valid-123"
        assert client.get("/health/ready").json() == {"status": "ready"}
        assert client.get("/api/v1/projects").status_code == 404
    assert probe.closed


def test_not_ready_and_invalid_request_id():
    with TestClient(create_app(probe=Probe(False))) as client:
        response = client.get("/health/ready", headers={"x-request-id": "<script>"})
        assert response.status_code == 503
        assert response.json() == {"status": "not_ready"}
        UUID(response.headers["x-request-id"])
        assert client.get("/health/live").status_code == 200


def test_database_configuration_requires_postgres(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
    with pytest.raises(ValidationError):
        Settings(database_url="sqlite:///unsafe.db", _env_file=None)
    settings = Settings(database_url="postgresql+psycopg://a:b@localhost/test", _env_file=None)
    assert settings.environment == "production"


class Example(BaseModel):
    value: int


def test_fake_provider_validates_and_requires_test_mode():
    with pytest.raises(ValueError):
        FakeProvider(environment="production", fixture={"value": 1})
    provider = FakeProvider(environment="test", fixture={"value": 1})
    assert provider.generate("test prompt", Example).value == 1
    with pytest.raises(ValidationError):
        FakeProvider(environment="test", fixture={"value": "bad"}).generate("prompt", Example)


def test_app_env_production_cannot_seed(monkeypatch):
    from aos_api.seed import seed

    monkeypatch.setenv("APP_ENV", "production")
    settings = Settings(database_url="postgresql+psycopg://a:b@localhost/test", _env_file=None)
    with pytest.raises(ValueError, match="development or test"):
        seed(settings)


def test_invalid_database_url_not_exposed():
    with pytest.raises(ValidationError) as error:
        Settings(database_url="invalid-secret-database-url", _env_file=None)
    assert "invalid-secret-database-url" not in str(error.value)
