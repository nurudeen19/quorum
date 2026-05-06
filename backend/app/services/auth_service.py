"""Registration, login, token refresh, email verification, and password reset."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt
import structlog
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AppSettings, get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schema.user import UserCreate
from app.services.email_service import send_password_reset_email, send_verification_email
from app.services.exceptions import (
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserConflictError,
)

logger = structlog.get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    """Handles credential flows and JWT issuance."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        self.settings = settings or get_settings().app

    async def register(self, session: AsyncSession, data: UserCreate) -> User:
        """Create an account and queue verification email unless dev auto-verify is on."""
        email = data.email.strip().lower()
        username = data.username.strip()

        dup = await session.execute(
            select(User.id).where(or_(User.email == email, User.username == username)).limit(1)
        )
        if dup.first():
            raise UserConflictError(
                "A user with this email or username already exists.",
            )

        verified = self.settings.auth_dev_auto_verify_email
        verification_token: str | None = None
        verification_expires: datetime | None = None

        if not verified:
            verification_token = secrets.token_urlsafe(32)
            verification_expires = _utcnow() + timedelta(
                hours=self.settings.email_verification_expire_hours,
            )

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(data.password),
            full_name=data.full_name.strip() if data.full_name else None,
            is_verified=verified,
            verification_token=verification_token,
            verification_expires_at=verification_expires,
        )
        session.add(user)
        try:
            await session.flush()
        except IntegrityError as exc:
            logger.warning("register_integrity", error=str(exc.orig))
            raise UserConflictError(
                "A user with this email or username already exists.",
            ) from exc

        await session.refresh(user)

        if verification_token:
            await send_verification_email(user.email, verification_token)

        return user

    async def login(self, session: AsyncSession, email: str, password: str) -> tuple[str, str]:
        """Validate credentials and return access and refresh JWTs."""
        email_norm = email.strip().lower()
        result = await session.execute(select(User).where(User.email == email_norm))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Incorrect email or password.")
        if not user.is_active:
            raise InvalidCredentialsError("Account is disabled.")
        if not user.is_verified:
            raise EmailNotVerifiedError("Email address is not verified.")

        access = create_access_token(user.id, self.settings)
        refresh = create_refresh_token(user.id, self.settings)
        return access, refresh

    async def refresh(self, session: AsyncSession, refresh_token: str) -> tuple[str, str]:
        """Issue a new access/refresh pair from a valid refresh token."""
        try:
            payload = decode_refresh_token(refresh_token, self.settings)
        except jwt.PyJWTError as exc:
            raise InvalidTokenError("Invalid or expired refresh token.") from exc

        user_id = payload.user_id
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise InvalidTokenError("Invalid or expired refresh token.")

        access = create_access_token(user.id, self.settings)
        new_refresh = create_refresh_token(user.id, self.settings)
        return access, new_refresh

    async def verify_email(self, session: AsyncSession, token: str) -> User:
        """Mark the email verified using the opaque token from the inbox link."""
        raw = token.strip()
        result = await session.execute(select(User).where(User.verification_token == raw))
        user = result.scalar_one_or_none()
        if user is None:
            raise InvalidTokenError("Invalid verification token.")
        if user.is_verified:
            return user
        if user.verification_expires_at is not None and user.verification_expires_at < _utcnow():
            raise InvalidTokenError("Verification link has expired.")

        user.is_verified = True
        user.verification_token = None
        user.verification_expires_at = None
        await session.flush()
        await session.refresh(user)
        return user

    async def request_password_reset(self, session: AsyncSession, email: str) -> None:
        """Set reset token and send mail if the account exists (anti-enumeration: same UX)."""
        email_norm = email.strip().lower()
        result = await session.execute(select(User).where(User.email == email_norm))
        user = result.scalar_one_or_none()
        if user is None:
            logger.info("password_reset_unknown_email")
            return

        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token = reset_token
        user.password_reset_expires_at = _utcnow() + timedelta(
            minutes=self.settings.password_reset_expire_minutes,
        )
        await session.flush()
        await send_password_reset_email(user.email, reset_token)

    async def reset_password(
        self,
        session: AsyncSession,
        token: str,
        new_password: str,
    ) -> None:
        """Apply a new password using the opaque reset token."""
        raw = token.strip()
        result = await session.execute(select(User).where(User.password_reset_token == raw))
        user = result.scalar_one_or_none()
        if user is None:
            raise InvalidTokenError("Invalid reset token.")
        if (
            user.password_reset_expires_at is None
            or user.password_reset_expires_at < _utcnow()
        ):
            raise InvalidTokenError("Reset link has expired.")

        user.password_hash = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires_at = None
        await session.flush()
