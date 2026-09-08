"""Validate production configuration without printing secret values."""

import os
import sys
from urllib.parse import urlparse


def invalid(name: str) -> None:
    print(f"Missing or invalid required setting: {name}", file=sys.stderr)
    raise SystemExit(1)


if os.environ.get("APP_ENV") != "production":
    invalid("APP_ENV")
database_url = os.environ.get("DATABASE_URL", "")
if not database_url.startswith("postgresql+psycopg://") or not urlparse(database_url).path.strip("/"):
    invalid("DATABASE_URL")
provider = os.environ.get("AI_PROVIDER")
if provider not in {"demo", "openai_compatible"}:
    invalid("AI_PROVIDER")
if provider == "demo":
    invalid("AI_PROVIDER")
for name in ("AI_BASE_URL", "AI_API_KEY", "AI_MODEL"):
    if not os.environ.get(name):
        invalid(name)
print("Production configuration shape is valid.")
