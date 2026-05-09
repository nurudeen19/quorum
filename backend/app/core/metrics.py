"""Prometheus FastAPI metrics setup."""
from typing import TYPE_CHECKING

from prometheus_fastapi_instrumentator import Instrumentator
from app.config import get_settings, AppSettings

if TYPE_CHECKING:
    from fastapi import FastAPI


def setup_metrics(app: "FastAPI", settings: AppSettings | None = None) -> None:
    """Configure Prometheus metrics for FastAPI using AppSettings."""
    if settings is None:
        settings = get_settings().app
    
    if not settings.metrics_enabled:
        return
    
    # Must run while building the app (before ASGI lifespan / server start);
    # ``instrument`` registers middleware, which Starlette disallows after startup.
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/api/v1/health", "/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="fastapi_inprogress",
        inprogress_labels=True,
    )
    instrumentator.instrument(app).expose(app)
