"""Application bootstrap and lifecycle management."""
from __future__ import annotations

import asyncio
import warnings
from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from app.cache import build_conversation_cache, set_conversation_cache
from app.cache.base import ConversationCache
from app.config import AppSettings, get_settings
from app.core.agent_factory import AgentFactory, configure_langsmith_tracing
from app.core.database import close_db, init_db, ping_database
from app.core.exceptions import StartupConfigurationError
from app.core.logging_config import setup_logging
from app.core.metrics import setup_metrics
from app.core.rate_limit import configure_rate_limiter, limiter
from app.core.startup_console import failed, initialized, skipped, starting
from app.core.tracing import setup_tracing
from app.guardrails.prompt_guard import setup_prompt_guard, teardown_prompt_guard

logger = structlog.get_logger(__name__)


class ApplicationBootstrap:
    """Manages application lifecycle and critical components."""

    def __init__(self, settings: AppSettings | None = None) -> None:
        if settings is None:
            settings = get_settings().app
        self.settings = settings
        self._initialized = False
        self.history_cache: ConversationCache | None = None
        self.agent_factory: AgentFactory | None = None
        self.executive_briefing_graph: Any | None = None

    async def initialize(self) -> None:
        if self._initialized:
            return

        settings_all = get_settings()

        starting("logging")
        setup_logging(self.settings)
        initialized("logging")

        starting("telemetry")
        try:
            setup_tracing(self.settings)
            configure_langsmith_tracing(settings_all.agents)
        except StartupConfigurationError:
            failed("telemetry", "configuration")
            raise
        except Exception as exc:
            failed("telemetry", str(exc)[:160])
            raise
        initialized("telemetry")

        if self.settings.database_url:
            starting("database")
            try:
                await ping_database()
                await init_db()
            except Exception as exc:
                failed("database", str(exc)[:160])
                raise
            initialized("database")
        else:
            skipped("database", "DATABASE_URL not set")

        starting("briefing graph")
        try:
            # Local import avoids a cycle: bootstrap → briefing_graph → agent_factory →
            # app.core package __init__ (re-imports bootstrap while briefing_graph loads).
            from app.graph.briefing_graph import build_briefing_graph

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                self.agent_factory = AgentFactory(settings_all.agents)
                self.executive_briefing_graph = build_briefing_graph(self.agent_factory)
        except Exception as exc:
            self.agent_factory = None
            self.executive_briefing_graph = None
            failed("briefing graph", str(exc)[:160])
            raise
        initialized("briefing graph")

        if settings_all.enable_promtpt_guard:
            hf = settings_all.hf_token.get_secret_value() if settings_all.hf_token else ""
            if not hf.strip():
                failed("prompt guard", "HF_TOKEN missing")
                raise StartupConfigurationError(
                    "ENABLE_PROMPT_GUARD is true but HF_TOKEN is missing."
                )
            starting("prompt guard")
            try:
                await asyncio.to_thread(setup_prompt_guard, settings_all)
            except Exception as exc:
                failed("prompt guard", str(exc)[:160])
                logger.exception("prompt_guard_startup_failed")
                raise StartupConfigurationError(
                    "Prompt guard failed to initialize; see logs for details."
                ) from exc
            initialized("prompt guard")
        else:
            skipped("prompt guard", "disabled in configuration")

        starting("cache")
        try:
            self.history_cache = build_conversation_cache(settings_all.cache)
            await self.history_cache.verify_connectivity()
        except Exception as exc:
            failed("cache", str(exc)[:160])
            logger.exception("conversation_cache_connectivity_failed")
            raise StartupConfigurationError(
                "Conversation cache failed connectivity check; see logs for details."
            ) from exc
        set_conversation_cache(self.history_cache)
        initialized("cache")

        self._initialized = True
        initialized("application")

    async def shutdown(self) -> None:
        teardown_prompt_guard()
        self.agent_factory = None
        self.executive_briefing_graph = None
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

    try:
        setup_metrics(app, settings)
    except Exception as exc:
        failed("metrics", str(exc)[:160])
        raise

    return app
