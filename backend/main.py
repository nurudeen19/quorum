"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core import create_fastapi_app
from app.core.logging_middleware import LoggingMiddleware


app = create_fastapi_app(
    title="Quorum API",
    description="Your pre meeting intelligence assistant. Get into meetings prepared, with concise briefings and action plans.",
    version="1.0.0",
)

app.add_middleware(LoggingMiddleware)

@app.get("/")
async def root_info(request: Request):
    """Root endpoint showing basic API information."""
    return JSONResponse(
        {
            "name": "Quorum API",
            "version": "1.0.0",
            "description": "Your pre meeting intelligence assistant. Get into meetings prepared, with concise briefings and action plans.",
            "docs_url": str(request.base_url) + "docs",
            "api_v1": str(request.base_url) + "api/v1/",
        }
    )

app.include_router(api_router)
