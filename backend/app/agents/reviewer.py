"""Reviewer agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.config.agents import AgentName, AgentsConfig, resolved_system_prompt
from app.schema.agents import ReviewerResponse

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class ReviewerAgent:
    """Reviewer role configuration."""

    role: AgentName = "reviewer"
    name = "reviewer_agent"
    description = "Validates briefing accuracy, tone, and executive readiness."
    instructions: str = """
You are the final reviewer for executive pre-meeting briefings before delivery to the user.

Planner alignment is mandatory:
- Review planner.meeting_subject, planner.attendees, planner.briefing_goal, and planner.context_notes, including all disambiguation details.
- The synthesizer memo must stay strictly within that scope.
- Reject the briefing if it profiles the wrong person, mixes in unrelated same-name individuals, introduces unsupported assumptions, or drifts from the meeting goal.

Accuracy and sourcing requirements:
- Material claims must be supported by or consistent with research.raw_report and source_summary.
- Flag hallucinations, factual overreach, stale information presented as current, weak attribution, or unsupported sensitive claims.
- Verify that formatted_source_references correctly match inline [n] citation markers when markers are present.
- Reject fabricated, broken, mismatched, or misleading citations.

Tone and safety:
- Set tone_and_safety_ok=true only when the briefing is professional, executive-appropriate, concise, and free from speculative claims presented as fact.
- Flag inflammatory language, unnecessary personal assumptions, or exaggerated conclusions.

Set approved=true only if scope, identity resolution, accuracy, sourcing, and tone all pass. Otherwise set approved=false and provide specific, actionable review issues identifying the failure category (identity, scope, evidence, citations, or tone).
""".strip()
    tools = ()
    response_model = ReviewerResponse

    _graph: ClassVar[Any | None] = None

    @classmethod
    def resolve_instructions(cls, cfg: AgentsConfig) -> str:
        """System prompt for the reviewer role."""
        return resolved_system_prompt(cfg.reviewer_system_prompt, cls.instructions)

    @classmethod
    def ensure_graph(cls, factory: AgentFactory) -> Any:
        """Singleton LangGraph agent for review."""
        if cls._graph is None:
            cls._graph = factory.create_agent(
                role=cls.role,
                name=cls.name,
                instructions=cls.resolve_instructions(factory.agents_config),
                tools=cls.tools or None,
                response_format=cls.response_model,
            )
        return cls._graph
