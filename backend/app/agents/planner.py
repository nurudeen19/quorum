"""Planner agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.agents.prompts import PLANNER_PRIMARY_DEFAULT, PLANNER_REWORK_DEFAULT, planner_primary_instructions
from app.config.agents import AgentName
from app.schema.agents import PlannerResponse

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class PlannerAgent:
    """Planner role configuration."""

    role: AgentName = "planner"
    name = "planner_agent"
    description = "Plans executive briefing research from meeting context and user goals."
    instructions = PLANNER_PRIMARY_DEFAULT
    rework_instructions = PLANNER_REWORK_DEFAULT
    tools = ()
    response_model = PlannerResponse
    _instance: ClassVar[Any | None] = None

    def __init__(self, factory: AgentFactory | None = None) -> None:
        """Optionally initialize singleton during construction."""
        if factory is not None and self.__class__._instance is None:
            self.get_or_create(factory)

    def get_or_create(self, factory: AgentFactory) -> Any:
        """Return singleton agent instance for this role."""
        if self.__class__._instance is None:
            resolved = planner_primary_instructions(factory.agents_config)
            self.__class__._instance = factory.create_agent(
                role=self.role,
                name=self.name,
                instructions=resolved,
                tools=self.tools or None,
                response_format=self.response_model,
            )
        return self.__class__._instance
