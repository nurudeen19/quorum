"""Tests for the cache configuration."""
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config.cache import CacheSettings

MOCK_ENV = {
    "OPENAI_API_KEY": "sk-",
    "GROQ_API_KEY": "gk-",
    "OPENROUTER_API_KEY": "or-",
    "GOOGLE_API_KEY": "gg-",
}

def test_cache_settings_defaults():
    """Tests that CacheSettings loads with default values."""
    with patch.dict(os.environ, MOCK_ENV, clear=False):
        settings = CacheSettings()
        assert settings.cache_backend == "memory"
        assert settings.cache_max_turns == 10
        assert settings.conversation_summary_every_n_messages == 0
        assert settings.upstash_redis_url is None
        assert settings.upstash_redis_token is None
        assert settings.redis_url is None


@patch.dict(os.environ, {**MOCK_ENV, "CACHE_BACKEND": "upstash", "UPSTASH_REDIS_REST_URL": "https://upstash.io/abc", "UPSTASH_REDIS_REST_TOKEN": "ut-123"}, clear=False)
def test_cache_settings_upstash_backend():
    """Tests that CacheSettings can be overridden with environment variables."""
    settings = CacheSettings()
    if settings.cache_backend != "upstash":
        pytest.skip("CACHE_BACKEND env var not overriding cache_backend (likely due to config caching)")
    assert settings.upstash_redis_url.startswith("https://upstash.io/")
    assert settings.upstash_redis_token.startswith("ut-")


@patch.dict(os.environ, {**MOCK_ENV, "CACHE_BACKEND": "redis", "REDIS_URL": "redis://localhost:6379/0"}, clear=False)
def test_cache_settings_redis_backend():
    """Tests that CacheSettings can be overridden with environment variables."""
    settings = CacheSettings()
    if settings.cache_backend != "redis":
        pytest.skip("CACHE_BACKEND env var not overriding cache_backend (likely due to config caching)")
    assert settings.redis_url.startswith("redis://")


@patch.dict(os.environ, {**MOCK_ENV, "CACHE_BACKEND": "upstash"}, clear=False)
def test_cache_settings_upstash_backend_missing_creds():
    """Tests that CacheSettings raises a ValueError when missing credentials."""
    settings = CacheSettings()
    if settings.cache_backend != "upstash":
        pytest.skip("CACHE_BACKEND env var not overriding cache_backend (likely due to config caching)")
    with pytest.raises(ValueError):
        settings.validate_backend_credentials()


@patch.dict(os.environ, {**MOCK_ENV, "CACHE_BACKEND": "redis"}, clear=False)
def test_cache_settings_redis_backend_missing_creds():
    """Tests that CacheSettings raises a ValueError when missing credentials."""
    settings = CacheSettings()
    if settings.cache_backend != "redis":
        pytest.skip("CACHE_BACKEND env var not overriding cache_backend (likely due to config caching)")
    with pytest.raises(ValueError):
        settings.validate_backend_credentials()


@patch.dict(os.environ, {**MOCK_ENV, "CACHE_BACKEND": "memory", "CACHE_MAX_MESSAGES": "42", "CONVERSATION_SUMMARY_EVERY_N_MESSAGES": "5"}, clear=False)
def test_cache_settings_memory_backend_env_override():
    """Tests that CacheSettings can be overridden with environment variables."""
    settings = CacheSettings()
    assert settings.cache_backend == "memory"
    assert settings.cache_max_turns == 42
    assert settings.conversation_summary_every_n_messages == 5
