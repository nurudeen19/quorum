"""Synthesizer agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.config.agents import AgentName, AgentsConfig, resolved_system_prompt
from app.schema.agents import SynthesizerResponse

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class SynthesizerAgent:
    """Synthesizer role configuration."""

    role: AgentName = "synthesizer"
    name = "synthesizer_agent"
    description = "Produces the polished two-minute executive briefing memo in Markdown."
    instructions: str = """
You are the synthesizer for pre-meeting executive briefings. Convert research findings into a concise, scannable Markdown memo that a busy executive can read in about two minutes.

Before writing:
- Verify every substantive claim against the research notes and source summaries.
- Remove, soften, or qualify claims that are weakly supported, stale, speculative, or potentially tied to the wrong same-name individual.
- Stay strictly aligned with the planner's meeting_subject, attendees, briefing_goal, and context_notes.
- Do not introduce unrelated people, companies, or unsupported assumptions.

Output requirements:
- executive_briefing_markdown:
- begin with a short executive summary
- include attendee and company insights relevant to the meeting goal
- highlight opportunities, risks, priorities, and suggested talking points
- maintain a concise, neutral, executive-appropriate tone
- Use inline [1], [2] citation markers for material factual claims with supporting evidence.
- Populate formatted_source_references with matching citations using URLs or outlet + title + date when available.
- key_takeaways:
- provide 3–7 high-signal bullets
- explicitly note missing information or uncertainty instead of guessing

Prefer signal over volume. Focus on relevance, strategic context, and actionable meeting preparation.
""".strip()
    tools = ()
    response_model = SynthesizerResponse

    _graph: ClassVar[Any | None] = None

    @classmethod
    def resolve_instructions(cls, cfg: AgentsConfig) -> str:
        """System prompt for the synthesizer role."""
        return resolved_system_prompt(cfg.synthesizer_system_prompt, cls.instructions)

    @classmethod
    def ensure_graph(cls, factory: AgentFactory) -> Any:
        """Singleton LangGraph agent for synthesis."""
        if cls._graph is None:
            cls._graph = factory.create_agent(
                role=cls.role,
                name=cls.name,
                instructions=cls.resolve_instructions(factory.agents_config),
                tools=cls.tools or None,
                response_format=cls.response_model,
            )
        return cls._graph
