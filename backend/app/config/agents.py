
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AgentName = Literal["planner", "research", "reviewer", "synthesizer"]
ModelProvider = Literal["openai", "groq", "openrouter", "google"]


class AgentLLMConfig(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    model: str = Field(default="gpt-4o-mini")
    model_provider: ModelProvider = Field(default="openai")
    fallback_model: str | None = None
    fallback_model_provider: ModelProvider | None = None

    @field_validator("model_provider", mode="before")
    @classmethod
    def normalize_model_provider(cls, value: object) -> ModelProvider:
        if not isinstance(value, str):
            raise TypeError("model_provider must be a string")
        normalized = value.strip().lower()
        allowed: tuple[ModelProvider, ...] = ("openai", "groq", "openrouter", "google")
        if normalized not in allowed:
            raise ValueError(f"model_provider must be one of {allowed}, got {value!r}")
        return normalized  # type: ignore[return-value]

    @field_validator("fallback_model_provider", mode="before")
    @classmethod
    def normalize_fallback_model_provider(cls, value: object) -> ModelProvider | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        if not isinstance(value, str):
            raise TypeError("fallback_model_provider must be a string or empty")
        normalized = value.strip().lower()
        allowed: tuple[ModelProvider, ...] = ("openai", "groq", "openrouter", "google")
        if normalized not in allowed:
            raise ValueError(f"fallback_model_provider must be one of {allowed}, got {value!r}")
        return normalized  # type: ignore[return-value]

    @model_validator(mode="after")
    def fallback_pair(self) -> AgentLLMConfig:
        a, b = self.fallback_model, self.fallback_model_provider
        if (a is None or not str(a).strip()) and b is None:
            return self
        if (a is None or not str(a).strip()) or b is None:
            raise ValueError("fallback_model and fallback_model_provider must both be set or both omitted")
        if str(a).strip() == self.model.strip() and b == self.model_provider:
            raise ValueError("fallback_model must differ from the primary model (or use a different provider)")
        return self


class AgentsConfig(BaseModel):
    """Agent configuration with defaults.
    Example env vars for overrides (optional):
        PLANNER_MODEL, PLANNER_TEMPERATURE, RESEARCH_MODEL, REVIEWER_MAX_TOKENS, etc.
    """
    model_config = ConfigDict(extra="ignore")

    # ========================
    # API Keys - LLM Providers
    # ========================
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    openrouter_api_key: str | None = Field(default=None, alias="OPENROUTER_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    
    # ========================
    # API Keys - Search/Research Tools
    # ========================
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    brave_search_api_key: str | None = Field(default=None, alias="BRAVE_SEARCH_API_KEY")

    # ========================
    # LangSmith Tracing
    # ========================
    langsmith_tracing_enabled: bool = Field(default=False, alias="LANGSMITH_TRACING_ENABLED")
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="quorum", alias="LANGSMITH_PROJECT")

    # ========================
    # Planner Agent Configuration
    # ========================
    planner_temperature: float = Field(default=0.7, ge=0.0, le=2.0, alias="PLANNER_TEMPERATURE")
    planner_max_tokens: int = Field(default=2000, ge=1, alias="PLANNER_MAX_TOKENS")
    planner_model: str = Field(default="llama-3.3-70b-versatile", alias="PLANNER_MODEL")
    planner_model_provider: ModelProvider = Field(default="groq", alias="PLANNER_MODEL_PROVIDER")
    planner_fallback_model: str | None = Field(default="gpt-4o-mini", alias="PLANNER_FALLBACK_MODEL")
    planner_fallback_model_provider: ModelProvider | None = Field(default="openai", alias="PLANNER_FALLBACK_MODEL_PROVIDER")

    # ========================
    # Research Agent Configuration
    # ========================
    research_temperature: float = Field(default=0.5, ge=0.0, le=2.0, alias="RESEARCH_TEMPERATURE")
    research_max_tokens: int = Field(default=3000, ge=1, alias="RESEARCH_MAX_TOKENS")
    research_model: str = Field(default="gpt-4o-mini", alias="RESEARCH_MODEL")
    research_model_provider: ModelProvider = Field(default="openai", alias="RESEARCH_MODEL_PROVIDER")
    research_fallback_model: str | None = Field(default=None, alias="RESEARCH_FALLBACK_MODEL")
    research_fallback_model_provider: ModelProvider | None = Field(default=None, alias="RESEARCH_FALLBACK_MODEL_PROVIDER")

    # ========================
    # Reviewer Agent Configuration
    # ========================
    reviewer_temperature: float = Field(default=0.2, ge=0.0, le=2.0, alias="REVIEWER_TEMPERATURE")
    reviewer_max_tokens: int = Field(default=1000, ge=1, alias="REVIEWER_MAX_TOKENS")
    reviewer_model: str = Field(default="llama-3.3-70b-versatile", alias="REVIEWER_MODEL")
    reviewer_model_provider: ModelProvider = Field(default="groq", alias="REVIEWER_MODEL_PROVIDER")
    reviewer_fallback_model: str | None = Field(default=None, alias="REVIEWER_FALLBACK_MODEL")
    reviewer_fallback_model_provider: ModelProvider | None = Field(default=None, alias="REVIEWER_FALLBACK_MODEL_PROVIDER")

    # ========================
    # Synthesizer Agent Configuration
    # ========================
    synthesizer_temperature: float = Field(default=0.5, ge=0.0, le=2.0, alias="SYNTHESIZER_TEMPERATURE")
    synthesizer_max_tokens: int = Field(default=3000, ge=1, alias="SYNTHESIZER_MAX_TOKENS")
    synthesizer_model: str = Field(default="llama-3.3-70b-versatile", alias="SYNTHESIZER_MODEL")
    synthesizer_model_provider: ModelProvider = Field(default="groq", alias="SYNTHESIZER_MODEL_PROVIDER")
    synthesizer_fallback_model: str | None = Field(default=None, alias="SYNTHESIZER_FALLBACK_MODEL")
    synthesizer_fallback_model_provider: ModelProvider | None = Field(default=None, alias="SYNTHESIZER_FALLBACK_MODEL_PROVIDER")

    def _llm(self, role: AgentName) -> AgentLLMConfig:
        return AgentLLMConfig(
            temperature=getattr(self, f"{role}_temperature"),
            max_tokens=getattr(self, f"{role}_max_tokens"),
            model=getattr(self, f"{role}_model"),
            model_provider=getattr(self, f"{role}_model_provider"),
            fallback_model=getattr(self, f"{role}_fallback_model"),
            fallback_model_provider=getattr(self, f"{role}_fallback_model_provider"),
        )

    def _provider_api_key(self, provider: ModelProvider) -> str | None:
        if provider == "openai":
            return self.openai_api_key
        if provider == "groq":
            return self.groq_api_key
        if provider == "openrouter":
            return self.openrouter_api_key
        return self.google_api_key

    @model_validator(mode="after")
    def validate_provider_keys(self) -> "AgentsConfig":
        """Ensure primary and configured fallback providers have API keys."""
        for role in ("planner", "research", "reviewer", "synthesizer"):
            model_provider = getattr(self, f"{role}_model_provider")
            model_provider_key = self._provider_api_key(model_provider)
            if not model_provider_key or not model_provider_key.strip():
                raise ValueError(
                    f"{role}_model_provider is '{model_provider}' but its API key is missing."
                )

            fallback_model = getattr(self, f"{role}_fallback_model")
            fallback_provider = getattr(self, f"{role}_fallback_model_provider")
            if not fallback_model or not str(fallback_model).strip() or fallback_provider is None:
                continue
            provider_key = self._provider_api_key(fallback_provider)
            if provider_key and provider_key.strip():
                continue
            raise ValueError(
                f"{role}_fallback_model_provider is '{fallback_provider}' but its API key is missing."
            )
        return self

    def get_llm_config(self, role: AgentName) -> AgentLLMConfig:
        """Return the LLM configuration bundle for a pipeline role."""
        return self._llm(role)

    @property
    def planner(self) -> AgentLLMConfig:
        return self._llm("planner")

    @property
    def research(self) -> AgentLLMConfig:
        return self._llm("research")

    @property
    def reviewer(self) -> AgentLLMConfig:
        return self._llm("reviewer")

    @property
    def synthesizer(self) -> AgentLLMConfig:
        return self._llm("synthesizer")
