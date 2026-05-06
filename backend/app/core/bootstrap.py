"""Application bootstrap and lifecycle management."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

from app.config import get_settings, AppSettings
from app.core.database import close_db, init_db
from app.core.logging_config import setup_logging
from app.core.metrics import setup_metrics
from app.core.tracing import setup_tracing

logger = structlog.get_logger(__name__)


class ApplicationBootstrap:
    """Manages application lifecycle and critical components."""
    def __init__(self, settings: AppSettings | None = None) -> None:
        if settings is None:
            settings = get_settings().app
        self.settings = settings
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        setup_logging(self.settings)
        setup_tracing(self.settings)
        if self.settings.database_url:
            await init_db()
        self._initialized = True

    async def shutdown(self) -> None:
        await close_db()
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def setup_fastapi_lifespan(self) -> callable:
        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
            await self.initialize()
            setup_metrics(app, self.settings)
            try:
                yield
            finally:
                await self.shutdown()
        return lifespan


# Global bootstrap instance
_bootstrap: ApplicationBootstrap | None = None


def get_bootstrap() -> ApplicationBootstrap:
    """Get the global application bootstrap instance."""
    global _bootstrap
    if _bootstrap is None:
        _bootstrap = ApplicationBootstrap()
    return _bootstrap


async def initialize_app() -> None:
    """Initialize the application using the global bootstrap."""
    bootstrap = get_bootstrap()
    await bootstrap.initialize()


async def shutdown_app() -> None:
    """Shutdown the application using the global bootstrap."""
    global _bootstrap
    if _bootstrap:
        await _bootstrap.shutdown()
        _bootstrap = None


def create_fastapi_app(
    title: str | None = None,
    description: str | None = None,
    version: str = "1.0.0",
    **kwargs
) -> FastAPI:
    """Create a FastAPI application with proper lifecycle management."""
    settings = get_settings().app
    bootstrap = get_bootstrap()
    
    app = FastAPI(
        title=title or settings.app_name,
        description=description or "Quorum API with integrated lifecycle management",
        version=version,
        debug=settings.debug,
        lifespan=bootstrap.setup_fastapi_lifespan(),
        **kwargs
    )
    
    return app