"""Structlog logging setup for the app."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog
from structlog.stdlib import ProcessorFormatter
from structlog.typing import Processor

from app.config import AppSettings, get_settings


def _shared_pre_chain(*, include_format_exc_info: bool = False) -> list[Processor]:
    """Processors applied to every event (and to foreign stdlib records via ``ProcessorFormatter``)."""
    chain: list[Processor] = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]
    if include_format_exc_info:
        chain.append(structlog.processors.format_exc_info)
    return chain


def _formatter(renderer: Processor, *, include_format_exc_info: bool = False) -> ProcessorFormatter:
    """Build a stdlib formatter that renders structlog events with ``renderer``."""
    return ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=_shared_pre_chain(include_format_exc_info=include_format_exc_info),
    )


def setup_logging(settings: AppSettings | None = None) -> None:
    """Configure structlog and stdlib logging using AppSettings.

    - ``console``: human-readable logs to stdout only.
    - ``json``: one JSON object per line to the rotating log file only (no console).
    - ``both``: human-readable stdout **and** JSON lines in the log file (typical for local dev).

    Earlier versions sent console-formatted text to *both* destinations; file now uses JSON when
    ``both`` or ``json`` so the log file is machine-parseable.
    """
    if settings is None:
        settings = get_settings().app

    log_level = settings.log_level.upper()
    log_mode = settings.log_mode.lower()
    handlers: list[logging.Handler] = []

    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()

    structlog.reset_defaults()

    shared = _shared_pre_chain()

    if log_mode in ("console", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(_formatter(structlog.dev.ConsoleRenderer()))
        handlers.append(console_handler)

    if log_mode in ("json", "both"):
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            max_bytes = settings.log_max_size_mb * 1024 * 1024
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=settings.log_backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(
                _formatter(structlog.processors.JSONRenderer(), include_format_exc_info=True)
            )
            handlers.append(file_handler)
        except OSError as exc:
            logging.basicConfig(level=log_level)
            logging.getLogger(__name__).error(
                "Failed to create rotating log file handler: %s",
                exc,
            )

    if not handlers:
        # Misconfigured LOG_MODE — fall back to console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(_formatter(structlog.dev.ConsoleRenderer()))
        handlers.append(console_handler)

    logging.basicConfig(level=log_level, handlers=handlers)

    structlog.configure(
        processors=shared + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
