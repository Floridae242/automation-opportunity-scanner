"""Run against a disposable database whose name ends in _test; migrations reset it."""

import os

import pytest
from alembic import command
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from aos_api.config import Settings
from aos_api.db import DatabaseProbe, migration_config
from aos_api.models import Membership, Organization, User
from aos_api.seed import seed


@pytest.mark.integration
def test_migration_seed_constraints_and_readiness(monkeypatch):
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL database ending _test")
    assert (make_url(database_url).database or "").endswith("_test"), "Disposable _test DB required"
    monkeypatch.setenv("DATABASE_URL", database_url)
    settings = Settings(environment="test")
    config = migration_config()
    command.downgrade(config, "base")
    probe = DatabaseProbe(settings)
    engine = create_engine(database_url)
    try:
        assert not probe.check()
        command.upgrade(config, "head")
        assert probe.check()
        command.check(config)
        seed(settings)
        seed(settings)
        with engine.connect() as connection:
            for model in (Organization, User, Membership):
                assert connection.scalar(select(func.count()).select_from(model)) == 1
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO memberships SELECT gen_random_uuid(), "
                    "organization_id, user_id, role FROM memberships"
                )
            )
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO memberships VALUES (gen_random_uuid(), "
                    "gen_random_uuid(), gen_random_uuid(), 'owner')"
                )
            )
        command.downgrade(config, "base")
        assert not probe.check()
        command.upgrade(config, "head")
        assert probe.check()
    finally:
        probe.close()
        engine.dispose()
