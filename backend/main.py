"""FastAPI application entrypoint."""

from __future__ import annotations


from app.api import api_router
from app.core import create_fastapi_app
from app.core.logging_middleware import LoggingMiddleware


app = create_fastapi_app(
    title="Quorum API",
    description="FastAPI application with PostgreSQL, JWT auth, and agent orchestration",
    version="1.0.0",
)

app.add_middleware(LoggingMiddleware)

app.include_router(api_router)
