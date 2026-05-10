"""API routes module."""

from fastapi import APIRouter

from app.api.endpoints import auth, chat, health, observability, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(
    observability.router,
    prefix="/observability",
    tags=["observability"],
)

__all__ = ["api_router"]
