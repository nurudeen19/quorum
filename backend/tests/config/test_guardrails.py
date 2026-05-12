"""Tests for the guardrails configuration."""
import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config.guardrails import GuardrailsSettings

MOCK_ENV = {
    "OPENAI_API_KEY": "mock",
    "GROQ_API_KEY": "mock",
    "OPENROUTER_API_KEY": "mock",
    "GOOGLE_API_KEY": "mock",
}

def test_guardrails_settings_defaults():
    """Tests that GuardrailsSettings loads with default values."""
    with patch.dict(os.environ, MOCK_ENV, clear=False):
        config = GuardrailsSettings()
        assert config.hf_token.get_secret_value() == ""
        assert config.enable_promtpt_guard is True
        assert config.model_id == "meta-llama/Llama-Prompt-Guard-2-86M"
        assert config.device == "cpu"
        assert config.malicious_probability_threshold == 0.3
        assert config.max_user_input_chars == 1000
        assert config.min_user_input_chars == 2
        assert config.max_user_estimated_tokens == 12000
        assert config.classify_user_feedback is False
        assert config.briefing_max_review_cycles == 5

@patch.dict(
    os.environ,
    {
        **MOCK_ENV,
        "HF_TOKEN": "mock-hf-token",
        "ENABLE_PROMPT_GUARD": "false",
        "PROMPT_GUARD_MODEL_ID": "mock-model",
        "PROMPT_GUARD_DEVICE": "cuda:0",
        "PROMPT_GUARD_MALICIOUS_PROBABILITY_THRESHOLD": "0.9",
        "MAX_USER_INPUT_CHARS": "2048",
        "MIN_USER_INPUT_CHARS": "10",
        "MAX_USER_ESTIMATED_TOKENS": "24000",
        "PROMPT_GUARD_CLASSIFY_USER_FEEDBACK": "true",
        "BRIEFING_MAX_REVIEW_CYCLES": "7",
    },
    clear=False,
)
def test_guardrails_settings_env_override():
    config = GuardrailsSettings()
    assert config.hf_token.get_secret_value() == "mock-hf-token"
    assert config.enable_promtpt_guard is False
    assert config.model_id == "mock-model"
    assert config.device == "cuda:0"
    assert config.malicious_probability_threshold == 0.9
    assert config.max_user_input_chars == 2048
    assert config.min_user_input_chars == 10
    assert config.max_user_estimated_tokens == 24000
    assert config.classify_user_feedback is True
    assert config.briefing_max_review_cycles == 7
