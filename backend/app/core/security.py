"""Password hashing (Argon2) and JWT access/refresh helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import AppSettings, get_settings


@lru_cache(maxsize=16)
def _password_hasher_for(
    time_cost: int,
    memory_cost: int,
    parallelism: int,
    hash_len: int,
    salt_len: int,
) -> PasswordHasher:
    """Build a hasher for one parameter set (cached so we do not re-instantiate every request)."""
    return PasswordHasher(
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=hash_len,
        salt_len=salt_len,
    )


def _password_hasher() -> PasswordHasher:
    """Hasher configured from application settings (environment)."""
    s = get_settings().app
    return _password_hasher_for(
        s.argon2_time_cost,
        s.argon2_memory_cost,
        s.argon2_parallelism,
        s.argon2_hash_len,
        s.argon2_salt_len,
    )


def hash_password(password: str) -> str:
    if not password or not password.strip():
        raise ValueError("Password cannot be empty")
    return _password_hasher().hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    try:
        _password_hasher().verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    if not hashed_password:
        return True
    try:
        return _password_hasher().check_needs_rehash(hashed_password)
    except Exception:
        return True


class TokenPayload(dict):
    """Decoded JWT claims."""

    @property
    def user_id(self) -> UUID:
        return UUID(str(self["sub"]))

    @property
    def token_type(self) -> str:
        return str(self["type"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: UUID, settings: AppSettings) -> str:
    """Return a short-lived bearer access token."""
    expires = _utc_now() + timedelta(minutes=settings.jwt_access_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expires,
        "iat": _utc_now(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID, settings: AppSettings) -> str:
    """Return a longer-lived refresh token."""
    expires = _utc_now() + timedelta(days=settings.jwt_refresh_expire_days)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expires,
        "iat": _utc_now(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: AppSettings) -> TokenPayload:
    """Decode and validate a JWT (signature and expiry)."""
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    return TokenPayload(payload)


def decode_access_token(token: str, settings: AppSettings) -> TokenPayload:
    """Decode an access token and ensure ``type`` is ``access``."""
    data = decode_token(token, settings)
    if data.token_type != "access":
        raise jwt.InvalidTokenError("Not an access token")
    return data


def decode_refresh_token(token: str, settings: AppSettings) -> TokenPayload:
    """Decode a refresh token and ensure ``type`` is ``refresh``."""
    data = decode_token(token, settings)
    if data.token_type != "refresh":
        raise jwt.InvalidTokenError("Not a refresh token")
    return data
