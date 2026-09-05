"""ADR-012: email+password credentials with DB-backed rotating sessions."""

import hashlib
import hmac
import secrets
from base64 import b64decode, b64encode
from datetime import UTC, datetime, timedelta

SCRYPT_PARAMS = {"n": 2**14, "r": 8, "p": 1, "maxmem": 64 * 1024 * 1024}
SALT_BYTES = 16
SESSION_TTL = timedelta(days=7)
COOKIE_NAME = "aos_session"


def hash_password(password: str) -> str:
    if len(password.encode()) < 10 or len(password.encode()) > 1024:
        raise ValueError("password must be 10-1024 bytes")
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_PARAMS)
    return "$".join(
        (
            "scrypt",
            str(SCRYPT_PARAMS["n"]),
            str(SCRYPT_PARAMS["r"]),
            str(SCRYPT_PARAMS["p"]),
            b64encode(salt).decode(),
            b64encode(digest).decode(),
        )
    )


def verify_password(password: str, stored: str | None) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = (stored or "").split("$")
        if scheme != "scrypt":
            return False
        expected = _b64(digest_b64)
        actual = hashlib.scrypt(
            password.encode(),
            salt=_b64(salt_b64),
            n=int(n),
            r=int(r),
            p=int(p),
            maxmem=64 * 1024 * 1024,
        )
        return hmac.compare_digest(expected, actual)
    except (ValueError, TypeError):
        return False


def _b64(value: str) -> bytes:
    return b64decode(value.encode(), validate=True)


def new_session_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()


def session_expires_at(now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + SESSION_TTL
