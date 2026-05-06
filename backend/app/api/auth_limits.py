"""Dynamic SlowAPI limit strings from ``RateLimitsSettings``."""

from __future__ import annotations

from app.config import get_settings


def rate_auth_register() -> str:
    return get_settings().rate_limits.auth_register


def rate_auth_login() -> str:
    return get_settings().rate_limits.auth_login


def rate_auth_refresh() -> str:
    return get_settings().rate_limits.auth_refresh


def rate_auth_verify() -> str:
    return get_settings().rate_limits.auth_verify


def rate_auth_forgot_password() -> str:
    return get_settings().rate_limits.auth_forgot_password


def rate_auth_reset_password() -> str:
    return get_settings().rate_limits.auth_reset_password


def rate_auth_logout() -> str:
    return get_settings().rate_limits.auth_logout
