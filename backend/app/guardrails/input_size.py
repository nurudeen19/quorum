"""Hard limits on user text length before any model work."""

from __future__ import annotations

from app.config.settings import Settings


def validate_input_size(text: str, settings: Settings) -> str | None:
    """Return a user-facing error string, or ``None`` if within limits."""
    max_chars = settings.guardrails.max_user_input_chars
    if len(text) > max_chars:
        return (
            f"Message is too long ({len(text)} characters). "
            f"Please shorten to under {max_chars} characters and try again."
        )
    est_tokens = max(len(text) // 4, 1)
    max_tok = settings.guardrails.max_user_estimated_tokens
    if est_tokens > max_tok:
        return (
            "Message appears to exceed safe token limits for this service. "
            "Please shorten your question and try again."
        )
    min_chars = settings.guardrails.min_user_input_chars
    if len(text.strip()) < min_chars:
        return f"Message is too short (minimum {min_chars} characters)."
    return None
