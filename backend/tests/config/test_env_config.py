import os
import pytest
from pydantic import ValidationError
from app.config.settings import Settings
from app.config.app_settings import AppSettings
from app.config.cache import CacheSettings
from app.config.guardrails import GuardrailsSettings
from app.config.rate_limits import RateLimitsSettings

@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # Clear relevant env vars before each test
    keys = [
        'APP_NAME', 'DEBUG', 'ENVIRONMENT', 'DATABASE_URL', 'JWT_SECRET',
        'CACHE_BACKEND', 'CACHE_MAX_MESSAGES', 'UPSTASH_REDIS_REST_URL', 'UPSTASH_REDIS_REST_TOKEN', 'REDIS_URL',
        'HF_TOKEN', 'ENABLE_PROMPT_GUARD', 'PROMPT_GUARD_MODEL_ID', 'PROMPT_GUARD_DEVICE',
        'PROMPT_GUARD_MALICIOUS_PROBABILITY_THRESHOLD', 'MAX_USER_INPUT_CHARS', 'MIN_USER_INPUT_CHARS', 'MAX_USER_ESTIMATED_TOKENS',
        'RATE_LIMITS_ENABLED', 'RATE_LIMIT_AUTH_REGISTER',
    ]
    for k in keys:
        monkeypatch.delenv(k, raising=False)


def test_env_vars_loaded(monkeypatch):
    monkeypatch.setenv('APP_NAME', 'EnvTestApp')
    monkeypatch.setenv('DEBUG', 'true')
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///test.db')
    monkeypatch.setenv('JWT_SECRET', 'envsecret')
    settings = Settings()
    assert settings.app_name == 'EnvTestApp'
    assert settings.debug is True
    assert settings.database_url == 'sqlite:///test.db'
    assert settings.jwt_secret == 'envsecret'


def test_env_override(monkeypatch):
    monkeypatch.setenv('APP_NAME', 'OverrideApp')
    monkeypatch.setenv('DEBUG', 'false')
    settings = Settings()
    assert settings.app_name == 'OverrideApp'
    assert settings.debug is False


def test_cache_backend_validation(monkeypatch):
    monkeypatch.setenv('CACHE_BACKEND', 'upstash')
    monkeypatch.setenv('UPSTASH_REDIS_REST_URL', 'https://upstash.example')
    monkeypatch.setenv('UPSTASH_REDIS_REST_TOKEN', 'token')
    settings = Settings()
    assert settings.cache_backend == 'upstash'
    assert settings.upstash_redis_url == 'https://upstash.example'
    assert settings.upstash_redis_token == 'token'

    # Missing required for upstash
    monkeypatch.delenv('UPSTASH_REDIS_REST_TOKEN')
    with pytest.raises(ValidationError):
        Settings()

    # Redis backend requires redis_url
    monkeypatch.setenv('CACHE_BACKEND', 'redis')
    monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379/0')
    settings = Settings()
    assert settings.cache_backend == 'redis'
    assert settings.redis_url == 'redis://localhost:6379/0'
    monkeypatch.delenv('REDIS_URL')
    with pytest.raises(ValidationError):
        Settings()


def test_guardrails_threshold_validation(monkeypatch):
    monkeypatch.setenv('PROMPT_GUARD_MALICIOUS_PROBABILITY_THRESHOLD', '1.1')
    with pytest.raises(ValidationError):
        Settings()
    monkeypatch.setenv('PROMPT_GUARD_MALICIOUS_PROBABILITY_THRESHOLD', '0.2')
    settings = Settings()
    assert settings.malicious_probability_threshold == 0.2


def test_min_max_input_chars(monkeypatch):
    monkeypatch.setenv('MAX_USER_INPUT_CHARS', '100')
    monkeypatch.setenv('MIN_USER_INPUT_CHARS', '10')
    settings = Settings()
    assert settings.max_user_input_chars == 100
    assert settings.min_user_input_chars == 10


def test_rate_limits(monkeypatch):
    monkeypatch.setenv('RATE_LIMITS_ENABLED', 'true')
    monkeypatch.setenv('RATE_LIMIT_AUTH_REGISTER', '2/minute')
    settings = Settings()
    assert settings.enabled is True
    assert settings.auth_register == '2/minute'


def test_invalid_types(monkeypatch):
    monkeypatch.setenv('MAX_USER_INPUT_CHARS', 'notanint')
    with pytest.raises(ValidationError):
        Settings()
    monkeypatch.setenv('MAX_USER_INPUT_CHARS', '1000')
    monkeypatch.setenv('DEBUG', 'notabool')
    with pytest.raises(ValidationError):
        Settings()
