"""Synthesizer agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.config.agents import AgentName
from app.schema.agents import SynthesizerResponse

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class SynthesizerAgent:
    """Synthesizer role configuration."""

    role: AgentName = "synthesizer"
    name = "synthesizer_agent"
    description = "Builds the final user-facing answer from prior outputs."
    instructions = (
        "You are the synthesizer agent. Combine prior context into a clear, "
        "actionable final response. Do not fabricate sources."
    )
    tools = ()
    response_model = SynthesizerResponse
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
