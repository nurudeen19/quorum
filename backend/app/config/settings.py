"""Assessment API settings: domain sections are mixins; use properties for grouped access."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import cast

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.app_settings import AppSettings
from app.config.agents import AgentsConfig
from app.config.cache import CacheSettings
from app.config.guardrails import GuardrailsSettings
from app.config.rate_limits import RateLimitsSettings


class Settings(
    AppSettings,
    GuardrailsSettings,
    AgentsConfig,
    RateLimitsSettings,
    CacheSettings,
    BaseSettings,
):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def app(self) -> AppSettings:
        return cast(AppSettings, self)

    @property
    def guardrails(self) -> GuardrailsSettings:
        return cast(GuardrailsSettings, self)

    @property
    def agents(self) -> AgentsConfig:
        return cast(AgentsConfig, self)

    @property
    def rate_limits(self) -> RateLimitsSettings:
        return cast(RateLimitsSettings, self)

    @property
    def cache(self) -> CacheSettings:
        return cast(CacheSettings, self)


@lru_cache
def get_settings() -> Settings:
    return Settings()

