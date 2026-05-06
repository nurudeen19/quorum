"""Health checks for load balancers and monitoring."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Returns OK when the API process is running.",
)
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "healthy"}
