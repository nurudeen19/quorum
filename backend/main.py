"""FastAPI application entrypoint."""

from __future__ import annotations

from app.api import api_router
from app.core import create_fastapi_app

app = create_fastapi_app(
    title="Quorum API",
    description="FastAPI application with PostgreSQL, JWT auth, and agent orchestration",
    version="1.0.0",
)

app.include_router(api_router)

