"""User HTTP endpoints (authenticated profile)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schema.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current user",
)
async def read_me(current: User = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user from the Bearer access token."""
    return UserResponse.model_validate(current)
