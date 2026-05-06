"""Structlog logging setup for the app."""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import structlog
from app.config import get_settings, AppSettings

def setup_logging(settings: AppSettings | None = None) -> None:
    """Configure structlog and stdlib logging using AppSettings."""
    if settings is None:
        settings = get_settings().app

    log_level = settings.log_level.upper()
    log_mode = settings.log_mode.lower()  # "console", "json", or "both"
    handlers: list[logging.Handler] = []

    # Prevent duplicate handlers if setup_logging is called multiple times
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()

    if log_mode in ("console", "both"):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(console_handler)

    if log_mode in ("json", "both"):
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Use RotatingFileHandler for size-based rotation
            max_bytes = settings.log_max_size_mb * 1024 * 1024  # Convert MB to bytes
            file_handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=settings.log_backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            handlers.append(file_handler)
        except Exception as exc:
            # Fallback to console if file handler fails
            logging.basicConfig(level=log_level)
            logging.getLogger(__name__).error(f"Failed to create rotating log file handler: {exc}")

    logging.basicConfig(level=log_level, handlers=handlers)

    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if log_mode == "console":
        processors.append(structlog.dev.ConsoleRenderer())
    elif log_mode == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:  # both
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
