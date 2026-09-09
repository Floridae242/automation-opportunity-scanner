import os
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

ROOT = Path(os.environ.get("AOS_ROOT", Path(__file__).resolve().parents[4]))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", extra="ignore", populate_by_name=True, hide_input_in_errors=True
    )
    database_url: SecretStr
    environment: Literal["development", "test", "production"] = Field(
        default="production", validation_alias="APP_ENV"
    )
    ai_provider: Literal["demo", "openai_compatible"] = Field(
        default="demo", validation_alias="AI_PROVIDER"
    )
    ai_base_url: str | None = Field(default=None, validation_alias="AI_BASE_URL")
    ai_api_key: SecretStr | None = Field(default=None, validation_alias="AI_API_KEY")
    ai_model: str | None = Field(default=None, validation_alias="AI_MODEL")
    ai_timeout_seconds: float = Field(default=30.0, validation_alias="AI_TIMEOUT_SECONDS")
    sso_issuer: str | None = Field(default=None, validation_alias="SSO_ISSUER")
    sso_client_id: str | None = Field(default=None, validation_alias="SSO_CLIENT_ID")
    sso_client_secret: SecretStr | None = Field(default=None, validation_alias="SSO_CLIENT_SECRET")
    sso_redirect_uri: str | None = Field(default=None, validation_alias="SSO_REDIRECT_URI")

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

    def sso_missing_settings(self) -> list[str]:
        values = {
            "SSO_ISSUER": self.sso_issuer,
            "SSO_CLIENT_ID": self.sso_client_id,
            "SSO_CLIENT_SECRET": self.sso_client_secret,
            "SSO_REDIRECT_URI": self.sso_redirect_uri,
        }
        return [
            name
            for name, value in values.items()
            if value is None
            or (isinstance(value, SecretStr) and not value.get_secret_value().strip())
            or (isinstance(value, str) and not value.strip())
        ]
