"""Tests for the main settings composition."""
import os
from unittest.mock import patch
import pytest

from app.config.settings import Settings

MOCK_ENV = {
    "OPENAI_API_KEY": "mock",
    "GROQ_API_KEY": "mock",
    "OPENROUTER_API_KEY": "mock",
    "GOOGLE_API_KEY": "mock",
}

def test_settings_defaults():
    """Tests that the default settings are correctly composed."""
    with patch.dict(os.environ, MOCK_ENV, clear=False):
        settings = Settings()
        # Check that all required keys are present
        assert hasattr(settings, "app")
        assert hasattr(settings, "agents")
        assert hasattr(settings, "cache")
        assert hasattr(settings, "guardrails")
        assert hasattr(settings, "rate_limits")

@patch.dict(os.environ, {**MOCK_ENV, "APP_NAME": "MockApp", "OPENAI_API_KEY": "mock-key"}, clear=False)
def test_settings_env_override():
    """Tests that environment variable overrides are correctly propagated."""
    settings = Settings()
    assert settings.app.app_name == "MockApp"
    assert settings.agents.openai_api_key == "mock-key"
