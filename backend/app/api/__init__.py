"""API routes module."""
from fastapi import APIRouter

from app.api.endpoints import users

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(users.router, prefix="/users", tags=["users"])

__all__ = ["api_router"]