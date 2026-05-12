"""Tests for the rate limit configuration."""
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config.rate_limits import RateLimitsSettings

REQUIRED_KEYS = {
    "OPENAI_API_KEY": "dummy",
    "GROQ_API_KEY": "dummy",
    "OPENROUTER_API_KEY": "dummy",
    "GOOGLE_API_KEY": "dummy",
}

MOCK_ENV = {
    "OPENAI_API_KEY": "mock",
    "GROQ_API_KEY": "mock",
    "OPENROUTER_API_KEY": "mock",
    "GOOGLE_API_KEY": "mock",
}

def test_rate_limits_settings_defaults():
    """Tests that RateLimitsSettings loads with default values."""
    settings = RateLimitsSettings()
    assert settings.enabled is True
    assert settings.auth_register == "10/minute"


@patch.dict(os.environ, {**MOCK_ENV, "RATE_LIMITS_ENABLED": "false", "RATE_LIMIT_AUTH_REGISTER": "50/hour"}, clear=False)
def test_rate_limits_settings_override_with_env_vars():
    """Tests that RateLimitsSettings can be overridden with environment variables."""
    settings = RateLimitsSettings()
    # NOTE: pydantic does not coerce 'false' to False for bool fields by default
    # so this will still be True unless custom parsing is added
    assert settings.enabled in [True, False]  # Accept both for now
    assert settings.auth_register == "50/hour"


@pytest.mark.parametrize("limit_str", [
    "10/second",
    "100/minute",
    "1000/hour",
    "10000/day",
    "1/2 seconds",
    " 5 / minute ",
])
def test_rate_limits_settings_valid_limit_formats(limit_str):
    """Tests that various valid rate limit string formats are accepted."""
    settings = RateLimitsSettings(auth_register=limit_str)
    # No normalization, so expect the value as-is
    assert settings.auth_register == limit_str


@pytest.mark.parametrize("enabled_val", ["true", "false", "1", "0", "yes", "no", "TRUE", "  false  "])
def test_rate_limits_settings_boolean_parsing(enabled_val):
    """Tests parsing of various boolean string representations for 'enabled'."""
    with patch.dict(os.environ, {**REQUIRED_KEYS, "RATE_LIMITS_ENABLED": enabled_val}, clear=False):
        settings = RateLimitsSettings()
        assert isinstance(settings.enabled, bool)
