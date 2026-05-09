"""Synchronous checks run during application bootstrap before serving traffic."""

from __future__ import annotations

import structlog

from app.config.settings import Settings

logger = structlog.get_logger(__name__)

_DEFAULT_JWT_SECRET = "change-me"
_PRODUCTION_LIKE_ENVS = frozenset({"production", "prod", "staging"})


class StartupConfigurationError(RuntimeError):
    """Raised when required settings or wiring are invalid for the current environment."""


def validate_deployment_settings(settings: Settings) -> None:
    """Fail fast on dangerous or incomplete configuration.

    Pydantic already validates agent API keys on ``Settings`` construction. This layer adds
    environment-aware rules (database, JWT, LangSmith, Hugging Face prompt guard, email).

    Args:
        settings: Fully loaded application settings.

    Raises:
        StartupConfigurationError: When a required value is missing or unsafe.
    """
    app = settings.app
    env = (app.environment or "local").strip().lower()
    is_prod_like = env in _PRODUCTION_LIKE_ENVS

    if is_prod_like and not (app.database_url and app.database_url.strip()):
        raise StartupConfigurationError(
            "DATABASE_URL is required when ENVIRONMENT is production, prod, or staging."
        )

    if is_prod_like and app.jwt_secret.strip() == _DEFAULT_JWT_SECRET:
        raise StartupConfigurationError(
            "JWT_SECRET must not use the default value in production-like environments."
        )

    if settings.enable_promtpt_guard:
        token = settings.hf_token.get_secret_value() if settings.hf_token else ""
        if not token.strip():
            raise StartupConfigurationError(
                "ENABLE_PROMPT_GUARD is true but HF_TOKEN (or HUGGING_FACE_HUB_TOKEN) is missing."
            )

    if is_prod_like and not (app.mailtrap_api_token and app.mailtrap_api_token.strip()):
        logger.warning(
            "mailtrap_token_missing_in_production",
            environment=env,
            hint="Email verification and password reset will fail without MAILTRAP_API_TOKEN.",
        )


def verify_briefing_graph_wiring() -> None:
    """Ensure the executive briefing LangGraph compiles (catches topology / import errors)."""
    from app.graph.briefing_graph import build_briefing_graph_for_diagram

    build_briefing_graph_for_diagram()
    logger.info("briefing_graph_startup_check_ok")
