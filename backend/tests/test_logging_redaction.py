"""Test that logging never emits sensitive values (secrets, tokens, passwords, API keys, etc)."""

import io
import logging
import os
import structlog
import pytest
from unittest.mock import patch
from app.core.logging_config import setup_logging, REDACTED_TEXT


@pytest.fixture(autouse=True)
def _setup_logging():
    # Patch required env vars for config to avoid ValidationError
    with patch.dict(os.environ, {"GROQ_API_KEY": "dummy", "PLANNER_MODEL_PROVIDER": "openai", "OPENAI_API_KEY": "dummy"}, clear=False):
        setup_logging()  # Use default settings
        yield

@pytest.mark.parametrize("key,value", [
    ("jwt_secret", "supersecret"),
    ("api_key", "12345"),
    ("password", "hunter2"),
    ("access_token", "tok-abc"),
    ("refreshToken", "tok-def"),
    ("mailtrap_api_token", "tok-mail"),
    ("session_id", "sess-xyz"),
    ("user_credential", "cred-foo"),
    ("auth_code", "code-bar"),
])
def test_sensitive_keys_are_redacted(key, value):
    buf = io.StringIO()
    logger = structlog.get_logger("test.redact")
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logger.bind(**{key: value})
    # structlog emits via stdlib, so use stdlib logger
    std_logger = logging.getLogger("test.redact")
    std_logger.handlers.clear()
    std_logger.addHandler(handler)
    std_logger.setLevel(logging.INFO)
    logger.info("test event")
    output = buf.getvalue()
    assert REDACTED_TEXT in output, f"{key} was not redacted: {output}"
    assert value not in output, f"Sensitive value leaked for {key}: {output}"
