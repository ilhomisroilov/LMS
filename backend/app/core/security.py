"""Password hashing and JWT token helpers."""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt with an explicit cost of 12 (spec §12.1: bcrypt cost >= 12).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

ACCESS = "access"
REFRESH = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str | None) -> bool:
    # An invited user has no password yet -> verification always fails.
    if not hashed:
        return False
    return pwd_context.verify(plain, hashed)


def hash_token(raw: str) -> str:
    """SHA-256 hex digest used to store refresh/invite tokens at rest."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def new_family_id() -> str:
    return uuid.uuid4().hex


def generate_secret(length: int = 32) -> str:
    """URL-safe random secret for invite tokens / temp passwords."""
    return secrets.token_urlsafe(length)


def _create_token(subject: str | int, token_type: str, expires_delta: timedelta,
                  extra: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "jti": uuid.uuid4().hex,  # unique per token (prevents identical-second collisions)
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    subject: str | int,
    role: str,
    *,
    organization_id: int,
    branch_id: int | None = None,
    token_version: int = 0,
) -> str:
    return _create_token(
        subject, ACCESS,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        {"role": role, "org": organization_id, "branch": branch_id, "tv": token_version},
    )


def create_refresh_token(subject: str | int, family_id: str) -> str:
    return _create_token(
        subject, REFRESH,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        {"fam": family_id},
    )


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
