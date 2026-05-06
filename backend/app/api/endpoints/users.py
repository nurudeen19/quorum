"""User HTTP endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schema.user import UserCreate, UserResponse
from app.services import UserConflictError, UserService

router = APIRouter()


def get_user_service() -> UserService:
    """Inject a stateless user service instance."""
    return UserService()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Register a new user with email, username, and password.",
    responses={
        201: {"description": "User created"},
        409: {"description": "Email or username already registered"},
    },
)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Validate input and delegate creation to the user service."""
    try:
        user = await user_service.create_user(session, payload)
    except UserConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return UserResponse.model_validate(user)
