"""User domain logic and persistence."""

from __future__ import annotations

import structlog
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schema.user import UserCreate
from app.services.exceptions import UserConflictError

logger = structlog.get_logger(__name__)


class UserService:
    """Coordinates user-related async operations and database access."""

    async def create_user(self, session: AsyncSession, data: UserCreate) -> User:
        """Persist a new user; raises ``UserConflictError`` if unique constraints fail."""
        email = data.email.strip().lower()
        username = data.username.strip()

        dup = await session.execute(
            select(User.id).where(or_(User.email == email, User.username == username)).limit(1)
        )
        if dup.first():
            raise UserConflictError(
                "A user with this email or username already exists.",
            )

        user = User(
            email=email,
            username=username,
            password_hash=hash_password(data.password),
            full_name=data.full_name.strip() if data.full_name else None,
        )
        session.add(user)
        try:
            await session.flush()
        except IntegrityError as exc:
            logger.warning("user_create_integrity", error=str(exc.orig))
            raise UserConflictError(
                "A user with this email or username already exists.",
            ) from exc

        await session.refresh(user)
        return user
