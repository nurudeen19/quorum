"""Rate limiting toggle"""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, Field


class RateLimitsSettings(BaseModel):
    enabled: bool = Field(default=True, alias="RATE_LIMITS_ENABLED")
