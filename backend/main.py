"""FastAPI application with PostgreSQL integration."""
from __future__ import annotations

from app.core import create_fastapi_app
from app.api import api_router

# Create FastAPI app with integrated lifecycle management
app = create_fastapi_app(
    title="Quorum API",
    description="FastAPI application with PostgreSQL integration and agent orchestration",
    version="1.0.0",
)


@app.get("/health", summary="Health Check", description="Check if the API is healthy and running")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Quorum API is running"}


# Include API routes
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Disable uvicorn's logging since we have our own
    )