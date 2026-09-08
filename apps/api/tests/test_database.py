from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from aos_api.config import Settings
from aos_api.db import DatabaseProbe
from aos_api.seed import seed


def settings(environment="test"):
    return Settings(
        database_url="postgresql+psycopg://a:b@localhost/test",
        environment=environment,
        _env_file=None,
    )


def test_database_probe_checks_migration_and_connection():
    with (
        patch("aos_api.db.create_engine") as factory,
        patch("aos_api.db.MigrationContext") as context,
    ):
        probe = DatabaseProbe(settings())
        context.configure.return_value.get_current_heads.return_value = (
            "0011_benefit_realization",
        )
        assert probe.check()
        context.configure.return_value.get_current_heads.return_value = ()
        assert not probe.check()
        factory.return_value.connect.side_effect = OperationalError(
            "query", {}, Exception("secret")
        )
        assert not probe.check()
        probe.close()
        factory.return_value.dispose.assert_called_once()


def test_seed_rejects_production_before_connecting():
    with patch("aos_api.seed.create_engine") as factory:
        with pytest.raises(ValueError, match="development or test"):
            seed(settings("production"))
        factory.assert_not_called()


def test_seed_disposes_after_failure():
    engine = MagicMock()
    engine.begin.side_effect = OperationalError("query", {}, Exception("offline"))
    with patch("aos_api.seed.create_engine", return_value=engine):
        with pytest.raises(OperationalError):
            seed(settings())
        engine.dispose.assert_called_once()
