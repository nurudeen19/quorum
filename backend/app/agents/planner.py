"""Planner agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.config.agents import AgentName
from app.schema.agents import PlannerResponse
from app.tools.search_tools import tavily_web_search, brave_web_search

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class PlannerAgent:
    """Planner role configuration."""

    role: AgentName = "planner"
    name = "planner_agent"
    description = "Breaks user goals into a concrete execution plan."
    instructions = (
        "You are the planning agent. Break the user request into a concise, "
        "ordered plan that downstream agents can execute."
    )
    tools = (tavily_web_search, brave_web_search)
    response_model = PlannerResponse
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
