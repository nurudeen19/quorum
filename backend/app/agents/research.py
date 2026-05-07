"""Research agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.agents.prompts import RESEARCH_DEFAULT, research_instructions
from app.config.agents import AgentName
from app.schema.agents import ResearchResponse
from app.tools.search_tools import tavily_web_search, brave_web_search

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class ResearchAgent:
    """Research role configuration."""

    role: AgentName = "research"
    name = "research_agent"
    description = "Runs live web search to profile attendees and companies for the briefing."
    instructions = RESEARCH_DEFAULT
    tools = (tavily_web_search, brave_web_search)
    response_model = ResearchResponse
    _instance: ClassVar[Any | None] = None

    def __init__(self, factory: AgentFactory | None = None) -> None:
        """Optionally initialize singleton during construction."""
        if factory is not None and self.__class__._instance is None:
            self.get_or_create(factory)

    def get_or_create(self, factory: AgentFactory) -> Any:
        """Return singleton agent instance for this role."""
        if self.__class__._instance is None:
            resolved = research_instructions(factory.agents_config)
            self.__class__._instance = factory.create_agent(
                role=self.role,
                name=self.name,
                instructions=resolved,
                tools=self.tools or None,
                response_format=self.response_model,
            )
        return self.__class__._instance
