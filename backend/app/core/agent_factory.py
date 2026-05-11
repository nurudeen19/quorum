"""Central factory for creating LangChain agents."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, cast

import structlog
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.agents.planner import PlannerAgent
from app.agents.research import ResearchAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.synthesizer import SynthesizerAgent
from app.config.agents import AgentName, AgentsConfig, ModelProvider
from app.core.exceptions import StartupConfigurationError

logger = structlog.get_logger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def configure_langsmith_tracing(agents: AgentsConfig) -> None:
    """Configure LangSmith tracing once at app startup (one-time setup)."""
    if not agents.langsmith_tracing_enabled:
        return
    if not agents.langsmith_api_key or not str(agents.langsmith_api_key).strip():
        raise StartupConfigurationError(
            "LANGSMITH_TRACING_ENABLED is true but LANGSMITH_API_KEY is missing or empty."
        )
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = agents.langsmith_api_key.strip()
    os.environ["LANGCHAIN_PROJECT"] = agents.langsmith_project
    logger.info("langsmith_tracing_enabled", project=agents.langsmith_project)


@dataclass(frozen=True, slots=True)
class BriefingAgents:
    """References to the pre-built briefing LangGraph agents (owned by each role class)."""

    planner_primary: Any
    planner_rework: Any
    research: Any
    synthesizer: Any
    reviewer: Any


class AgentFactory:
    """Builds chat models and ``create_agent`` graphs; briefing graphs are created via role classes."""

    def __init__(self, agents: AgentsConfig) -> None:
        self._agents = agents
        self._briefing_agents = BriefingAgents(
            planner_primary=PlannerAgent.ensure_primary_graph(self),
            planner_rework=PlannerAgent.ensure_rework_graph(self),
            research=ResearchAgent.ensure_graph(self),
            synthesizer=SynthesizerAgent.ensure_graph(self),
            reviewer=ReviewerAgent.ensure_graph(self),
        )

    @property
    def agents_config(self) -> AgentsConfig:
        """Settings bundle used for models and optional system-prompt overrides."""
        return self._agents

    @property
    def briefing_agents(self) -> BriefingAgents:
        """Pre-built ``create_agent`` graphs (singletons on each role class)."""
        return self._briefing_agents

    def create_agent(
        self,
        *,
        role: AgentName,
        name: str,
        instructions: str,
        tools: tuple[Any, ...] | None = None,
        response_format: type[BaseModel] | None,
    ) -> Any:
        """Wire ``create_agent`` with a model for ``role``; ``name``/instructions come from the caller."""
        model = self._build_model(role)
        return create_agent(
            name=name,
            model=model,
            tools=list(tools) if tools else None,
            system_prompt=instructions,
            response_format=response_format,
        )

    def build_model_for_role(self, role: AgentName) -> BaseChatModel:
        """Return a chat model for ad-hoc completions (e.g. conversation summarization)."""
        return self._build_model(role)

    def _build_model(self, role: AgentName) -> BaseChatModel:
        llm = self._agents.get_llm_config(role)
        primary = self._build_provider_model(
            provider=llm.model_provider,
            model_name=llm.model.strip(),
            temperature=llm.temperature,
            max_tokens=llm.max_tokens,
        )
        if not llm.fallback_model or not llm.fallback_model_provider:
            return primary

        fallback = self._build_provider_model(
            provider=llm.fallback_model_provider,
            model_name=llm.fallback_model.strip(),
            temperature=llm.temperature,
            max_tokens=llm.max_tokens,
        )
        return primary.with_fallbacks([fallback])

    def _build_provider_model(
        self,
        *,
        provider: ModelProvider,
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> BaseChatModel:
        if provider == "openai":
            return ChatOpenAI(
                model=model_name,
                api_key=cast(str, self._agents.openai_api_key),
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if provider == "groq":
            return ChatGroq(
                model=model_name,
                api_key=cast(str, self._agents.groq_api_key),
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if provider == "google":
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=cast(str, self._agents.google_api_key),
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if provider == "openrouter":
            return ChatOpenAI(
                model=model_name,
                api_key=cast(str, self._agents.openrouter_api_key),
                base_url=OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": "https://github.com/quorum",
                    "X-Title": "Quorum API",
                },
                temperature=temperature,
                max_tokens=max_tokens,
            )

        raise ValueError(f"Unsupported model provider: {provider}")
