"""Synthesizer agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.agents.prompts import SYNTHESIZER_DEFAULT, synthesizer_instructions
from app.config.agents import AgentName
from app.schema.agents import SynthesizerResponse

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class SynthesizerAgent:
    """Synthesizer role configuration."""

    role: AgentName = "synthesizer"
    name = "synthesizer_agent"
    description = "Produces the polished two-minute executive briefing memo in Markdown."
    instructions = SYNTHESIZER_DEFAULT
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
            resolved = synthesizer_instructions(factory.agents_config)
            self.__class__._instance = factory.create_agent(
                role=self.role,
                name=self.name,
                instructions=resolved,
                tools=self.tools or None,
                response_format=self.response_model,
            )
        return self.__class__._instance
