"""Application bootstrap and lifecycle management."""
from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import structlog
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from app.cache import build_conversation_cache, set_conversation_cache
from app.cache.base import ConversationCache
from app.config import AppSettings, get_settings
from app.core.agent_factory import configure_langsmith_tracing
from app.core.rate_limit import configure_rate_limiter, limiter
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
        self.history_cache: ConversationCache | None = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        setup_logging(self.settings)
        setup_tracing(self.settings)
        configure_langsmith_tracing(get_settings().agents)
        if self.settings.database_url:
            await init_db()
        settings_all = get_settings()
        self.history_cache = build_conversation_cache(settings_all.cache)
        set_conversation_cache(self.history_cache)
        self._initialized = True

    async def shutdown(self) -> None:
        if self.history_cache is not None:
            await self.history_cache.aclose()
            self.history_cache = None
        set_conversation_cache(None)
        await close_db()
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def setup_fastapi_lifespan(
        self,
    ) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
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
    **kwargs,
) -> FastAPI:
    """Create a FastAPI application with proper lifecycle management."""
    settings_all = get_settings()
    settings = settings_all.app
    bootstrap = get_bootstrap()
    
    app = FastAPI(
        title=title or settings.app_name,
        description=description or "Quorum API with integrated lifecycle management",
        version=version,
        debug=settings.debug,
        lifespan=bootstrap.setup_fastapi_lifespan(),
        **kwargs,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    configure_rate_limiter(enabled=settings_all.rate_limits.enabled)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    return app