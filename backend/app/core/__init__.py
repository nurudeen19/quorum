"""Core application setup utilities."""

from app.core.bootstrap import (
    ApplicationBootstrap,
    create_fastapi_app,
    get_bootstrap,
    initialize_app,
    shutdown_app,
)
from app.core.database import close_db, get_db, init_db
from app.core.logging_config import setup_logging
from app.core.metrics import setup_metrics
from app.core.security import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    decode_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from app.core.tracing import setup_tracing

__all__ = [
    "setup_logging",
    "setup_tracing",
    "setup_metrics",
    "init_db",
    "close_db",
    "get_db",
    "ApplicationBootstrap",
    "get_bootstrap",
    "initialize_app",
    "shutdown_app",
    "create_fastapi_app",
    "hash_password",
    "verify_password",
    "needs_rehash",
    "TokenPayload",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "decode_access_token",
    "decode_refresh_token",
]
