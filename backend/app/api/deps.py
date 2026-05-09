"""Shared FastAPI dependencies (authentication)."""

from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import get_conversation_cache
from app.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.services.history_service import HistoryService

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the User from a valid Bearer access JWT."""
    try:
        payload = decode_access_token(credentials.credentials, get_settings().app)
        user_id = payload.user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address is not verified.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_history_service() -> HistoryService:
    """Conversation cache + DB history (same limits as bootstrap)."""
    settings = get_settings()
    cache = get_conversation_cache()
    return HistoryService(
        cache,
        max_turns=settings.cache.cache_max_turns,
        summary_every_n_messages=settings.cache.conversation_summary_every_n_messages,
    )
