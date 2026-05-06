"""User lookups used by dependencies and other services."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserService:
    """Lightweight read helpers for ``User`` rows."""

    async def get_by_id(self, session: AsyncSession, user_id: UUID) -> User | None:
        """Return the user by primary key, if any."""
        return await session.get(User, user_id)

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        """Return the user by normalized email, if any."""
        result = await session.execute(
            select(User).where(User.email == email.strip().lower()).limit(1)
        )
        return result.scalar_one_or_none()
