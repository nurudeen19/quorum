"""Async SQLAlchemy engine, session factory, and FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

logger = structlog.get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def sync_database_url(url: str) -> str:
    """Convert async SQLAlchemy URL to sync (Alembic / psycopg3)."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return url


def get_sync_database_url() -> str:
    """Sync database URL for Alembic migrations."""
    settings = get_settings().app
    if not settings.database_url:
        raise ValueError("DATABASE_URL is required for migrations")
    return sync_database_url(settings.database_url)


async def init_db() -> None:
    """Create the async engine, session factory, and verify connectivity."""
    global _engine, _session_factory
    settings = get_settings().app
    if not settings.database_url:
        logger.info("database_skipped_missing_url")
        return
    if _engine is not None:
        return
    _engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_recycle=settings.database_pool_recycle,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with _engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("database_initialized")


async def close_db() -> None:
    """Dispose of the async engine."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
    logger.info("database_closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: session per request with commit on success."""
    if _session_factory is None:
        raise RuntimeError("Database is not configured or application lifespan did not run")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
