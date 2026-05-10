"""Authenticated observability helpers for metrics, traces, and logs (dev / ops dashboard)."""

from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.config import get_settings
from app.models.user import User

logger = structlog.get_logger(__name__)

router = APIRouter()


class ObservabilitySummary(BaseModel):
    """Safe metadata for wiring a frontend observability page."""

    service_name: str = Field(description="OpenTelemetry service.name")
    metrics_enabled: bool
    prometheus_metrics_path: str = Field(
        default="/metrics",
        description="Prometheus scrape path on this API host (not under /api/v1).",
    )
    otlp_tracing_configured: bool = Field(
        description="Whether an OTLP trace endpoint was configured at startup.",
    )
    otlp_endpoint: str | None = Field(
        default=None,
        description="Configured OTLP endpoint (if any); may be empty when using console exporter.",
    )
    trace_ui_url: str | None = Field(
        default=None,
        description="Optional Jaeger / Tempo UI URL from configuration.",
    )
    log_tail_enabled: bool
    log_file_path: str | None = Field(
        default=None,
        description="Resolved log file path when log tail is enabled.",
    )


def _require_dashboard() -> None:
    if not get_settings().app.observability_dashboard_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Observability dashboard is disabled.",
        )


@router.get(
    "/summary",
    response_model=ObservabilitySummary,
    summary="Observability configuration summary",
)
async def observability_summary(_current: User = Depends(get_current_user)) -> ObservabilitySummary:
    """Return non-secret wiring hints for metrics, tracing, and optional log tail."""
    _require_dashboard()
    app = get_settings().app
    return ObservabilitySummary(
        service_name=app.otel_service_name,
        metrics_enabled=app.metrics_enabled,
        prometheus_metrics_path="/metrics",
        otlp_tracing_configured=bool(app.otel_exporter_otlp_endpoint),
        otlp_endpoint=app.otel_exporter_otlp_endpoint,
        trace_ui_url=app.observability_trace_ui_url,
        log_tail_enabled=app.observability_log_tail_enabled,
        log_file_path=app.log_file_path if app.observability_log_tail_enabled else None,
    )


class LogTailResponse(BaseModel):
    """Last lines of the configured application log file."""

    path: str
    lines: list[str]


@router.get(
    "/logs/tail",
    response_model=LogTailResponse,
    summary="Tail application log file",
)
async def observability_log_tail(
    _current: User = Depends(get_current_user),
    lines: int = Query(200, ge=1, le=2000, description="Number of lines from end of file."),
) -> LogTailResponse:
    """Return the last ``lines`` of the rotating log file (must be explicitly enabled)."""
    _require_dashboard()
    app = get_settings().app
    if not app.observability_log_tail_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Log tail is disabled (set OBSERVABILITY_LOG_TAIL_ENABLED=true).",
        )
    path = Path(app.log_file_path)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log file does not exist yet.",
        )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        logger.warning("observability_log_read_failed", path=str(path), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not read log file.",
        ) from exc
    text = raw.decode("utf-8", errors="replace")
    all_lines = text.splitlines()
    tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
    return LogTailResponse(path=str(path.resolve()), lines=tail)


@router.get(
    "/metrics-text",
    response_class=PlainTextResponse,
    summary="Prometheus metrics (text)",
)
async def observability_metrics_text(_current: User = Depends(get_current_user)) -> PlainTextResponse:
    """Return the current process Prometheus metrics in text format (when metrics are enabled)."""
    _require_dashboard()
    app = get_settings().app
    if not app.metrics_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics are disabled (METRICS_ENABLED=false).",
        )
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Prometheus client is not available.",
        ) from exc

    data = generate_latest()
    body = data.decode("utf-8", errors="replace")
    media = (
        CONTENT_TYPE_LATEST.decode("ascii")
        if isinstance(CONTENT_TYPE_LATEST, bytes)
        else str(CONTENT_TYPE_LATEST)
    )
    return PlainTextResponse(content=body, media_type=media)
