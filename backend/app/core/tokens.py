"""JWT access and refresh token helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.config import AppSettings


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
    """Decode and validate a JWT (checks signature and expiry)."""
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
