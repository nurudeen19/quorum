"""Cache backend configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


CacheBackend = Literal["memory", "upstash", "redis"]


class CacheSettings(BaseModel):
    """Conversation history cache settings."""

    model_config = ConfigDict(extra="ignore")

    cache_backend: CacheBackend = Field(default="memory", alias="CACHE_BACKEND")
    cache_max_turns: int = Field(
        default=10,
        ge=1,
        le=250,
        alias="CACHE_MAX_MESSAGES",
        description="Rolling window measured in message turns (user+assistant pair ≈ 2 messages).",
    )
    conversation_summary_every_n_messages: int = Field(
        default=0,
        ge=0,
        alias="CONVERSATION_SUMMARY_EVERY_N_MESSAGES",
        description="When >0, refresh Conversation.summary after every N new DB messages.",
    )

    upstash_redis_url: str | None = Field(default=None, alias="UPSTASH_REDIS_REST_URL")
    upstash_redis_token: str | None = Field(default=None, alias="UPSTASH_REDIS_REST_TOKEN")

    redis_url: str | None = Field(default=None, alias="REDIS_URL")

    @model_validator(mode="after")
    def validate_backend_credentials(self) -> CacheSettings:
        """Require credentials for remote backends."""
        if self.cache_backend == "upstash":
            if self.upstash_redis_url and self.upstash_redis_token:
                return self
            raise ValueError(
                "UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN are required when "
                "CACHE_BACKEND is upstash"
            )
        if self.cache_backend == "redis":
            if self.redis_url and self.redis_url.strip():
                return self
            raise ValueError("REDIS_URL is required when CACHE_BACKEND is redis")
        return self
