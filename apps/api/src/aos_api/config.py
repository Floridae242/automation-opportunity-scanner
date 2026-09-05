from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", extra="ignore", populate_by_name=True, hide_input_in_errors=True
    )
    database_url: SecretStr
    environment: Literal["development", "test", "production"] = Field(
        default="production", validation_alias="APP_ENV"
    )

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
            if url.drivername != "postgresql+psycopg" or not url.database:
                raise ValueError
        except Exception:
            raise ValueError(
                "DATABASE_URL must use postgresql+psycopg and specify a database"
            ) from None
        return value
