"""Hard limits on user text length before any model work."""

from __future__ import annotations

import structlog
logger = structlog.get_logger(__name__)

from app.config.settings import Settings


def validate_input_size(text: str, settings: Settings) -> str | None:
    """Return a user-facing error string, or ``None`` if within limits."""
    try:
        max_chars = settings.guardrails.max_user_input_chars
        if len(text) > max_chars:
            logger.warning(
                "input_too_long",
                length=len(text),
                max_chars=max_chars,
            )
            return (
                f"Message is too long ({len(text)} characters). "
                f"Please shorten to under {max_chars} characters and try again."
            )
        est_tokens = max(len(text) // 4, 1)
        max_tok = settings.guardrails.max_user_estimated_tokens
        if est_tokens > max_tok:
            logger.warning(
                "input_too_many_tokens",
                estimated_tokens=est_tokens,
                max_tokens=max_tok,
            )
            return (
                "Message appears to exceed safe token limits for this service. "
                "Please shorten your question and try again."
            )
        min_chars = settings.guardrails.min_user_input_chars
        if len(text.strip()) < min_chars:
            logger.warning(
                "input_too_short",
                length=len(text.strip()),
                min_chars=min_chars,
            )
            return f"Message is too short (minimum {min_chars} characters)."
        return None
    except Exception as exc:
        logger.error("input_size_validation_failed", error=str(exc))
        return "An internal error occurred while validating your message length. Please try again."
