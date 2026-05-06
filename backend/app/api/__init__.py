"""API routes module."""

from fastapi import APIRouter

from app.api.endpoints import auth, health, users

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

__all__ = ["api_router"]
