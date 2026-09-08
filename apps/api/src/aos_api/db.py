import os
from pathlib import Path
from typing import Protocol

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from aos_api.config import Settings

API_ROOT = Path(os.environ.get("AOS_API_ROOT", Path(__file__).resolve().parents[2]))


def migration_config() -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    return config


class ReadinessProbe(Protocol):
    def check(self) -> bool: ...
    def close(self) -> None: ...


class DatabaseProbe:
    def __init__(self, settings: Settings) -> None:
        self.engine = create_engine(
            settings.database_url.get_secret_value(),
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=0,
            pool_timeout=2,
            connect_args={"connect_timeout": 2, "options": "-c statement_timeout=2000"},
        )
        self.expected_heads = set(ScriptDirectory.from_config(migration_config()).get_heads())

    def check(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                actual = set(MigrationContext.configure(connection).get_current_heads())
                return bool(self.expected_heads) and actual == self.expected_heads
        except SQLAlchemyError:
            return False

    def close(self) -> None:
        self.engine.dispose()
