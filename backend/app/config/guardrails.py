"""Guardrails settings"""
from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field, SecretStr


class GuardrailsSettings(BaseModel):
    # ========================
    # HuggingFace Configuration
    # ========================
    hf_token: SecretStr = Field(default=SecretStr(""), alias="HF_TOKEN")
    
    # ========================
    # Prompt Guard Settings
    # ========================
    enable_promtpt_guard: bool = Field(default=True, alias="ENABLE_PROMPT_GUARD")
    model_id: str = Field(default="meta-llama/Llama-Prompt-Guard-2-86M", alias="PROMPT_GUARD_MODEL_ID")
    device: int | str = Field(default="cpu", alias="PROMPT_GUARD_DEVICE")
    malicious_probability_threshold: float = Field(
        default=0.3, 
        ge=0.0, 
        le=1.0, 
        alias="PROMPT_GUARD_MALICIOUS_PROBABILITY_THRESHOLD"
    )
    
    # ========================
    # Input Validation Limits
    # ========================
    max_user_input_chars: int = Field(default=1000, ge=256, alias="MAX_USER_INPUT_CHARS")
    min_user_input_chars: int = Field(default=2, ge=0, alias="MIN_USER_INPUT_CHARS")
