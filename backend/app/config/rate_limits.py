"""Rate limiting configuration (SlowAPI)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RateLimitsSettings(BaseModel):
    """Per-route limit strings (see SlowAPI / limits: "N/unit")."""

    model_config = ConfigDict(populate_by_name=True)

    enabled: bool = Field(default=True, alias="RATE_LIMITS_ENABLED")
    auth_register: str = Field(default="10/minute", alias="RATE_LIMIT_AUTH_REGISTER")
    auth_login: str = Field(default="20/minute", alias="RATE_LIMIT_AUTH_LOGIN")
    auth_refresh: str = Field(default="30/minute", alias="RATE_LIMIT_AUTH_REFRESH")
    auth_verify: str = Field(default="30/minute", alias="RATE_LIMIT_AUTH_VERIFY")
    auth_forgot_password: str = Field(default="5/minute", alias="RATE_LIMIT_AUTH_FORGOT_PASSWORD")
    auth_reset_password: str = Field(default="10/minute", alias="RATE_LIMIT_AUTH_RESET_PASSWORD")
    auth_logout: str = Field(default="30/minute", alias="RATE_LIMIT_AUTH_LOGOUT")

    # Chat endpoints
    chat_list: str = Field(default="60/minute", alias="RATE_LIMIT_CHAT_LIST")
    chat_messages: str = Field(default="60/minute", alias="RATE_LIMIT_CHAT_MESSAGES")
    chat_feedback: str = Field(default="30/minute", alias="RATE_LIMIT_CHAT_FEEDBACK")
    chat_delete: str = Field(default="30/minute", alias="RATE_LIMIT_CHAT_DELETE")
    chat_stream: str = Field(default="30/hour", alias="RATE_LIMIT_CHAT_STREAM")
