"""Reviewer agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.config.agents import AgentName
from app.schema.agents import ReviewerResponse
from app.tools.search_tools import tavily_web_search

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class ReviewerAgent:
    """Reviewer role configuration."""

    role: AgentName = "reviewer"
    name = "reviewer_agent"
    description = "Reviews outputs for quality, grounding, and clarity."
    instructions = (
        "You are the reviewer agent. Validate quality and factual grounding. "
        "If quality is not enough, provide explicit fixes."
    )
    tools = (tavily_web_search,)
    response_model = ReviewerResponse
    _instance: ClassVar[Any | None] = None

    def __init__(self, factory: AgentFactory | None = None) -> None:
        """Optionally initialize singleton during construction."""
        if factory is not None and self.__class__._instance is None:
            self.get_or_create(factory)

    def get_or_create(self, factory: AgentFactory) -> Any:
        """Return singleton agent instance for this role."""
        if self.__class__._instance is None:
            self.__class__._instance = factory.create_or_get_agent(
                role=self.role,
                name=self.name,
                instructions=self.instructions,
                tool_names=self.tools,
                response_format=self.response_model,
            )
        return self.__class__._instance
