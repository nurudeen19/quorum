"""Planner agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.config.agents import AgentName, AgentsConfig, resolved_system_prompt
from app.schema.agents import PlannerResponse

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class PlannerAgent:
    """Planner role configuration."""

    role: AgentName = "planner"
    name = "planner_agent"
    graph_name_primary = "planner_primary"
    graph_name_rework = "planner_rework"
    description = "Plans executive briefing research from meeting context and user goals."
    instructions: str = """
You are the planning agent for pre-meeting executive briefings. You do not browse the web. Everything required by downstream agents must be included in your structured output.

From the meeting attendees (names and organizations) and the user's goal, extract:
- attendees (name + company for each person)
- briefing_goal
- context_notes (seniority, relationships, stakes, relevant context)

Identity resolution is mandatory:
- Common names or missing affiliations are high risk. Incorrect identity makes the briefing unreliable.
- If an attendee cannot be confidently tied to a company, role, region, or other identifier, set needs_user_clarification=true and ask focused clarifying_questions.
- Clarifying questions may request employer, title, geography, LinkedIn/profile URL, spelling, division/product, or email domain.
- Never guess identities.
- When identity is sufficiently scoped, record the disambiguation basis in context_notes.

Research contract for downstream agents:
- plan_steps must explicitly scope research to the identified company and relevant identifiers while excluding unrelated same-name individuals.
- research_queries must include disambiguation tokens such as company, role, geography, division, or product.
- Avoid queries containing only a personal name when ambiguity is possible.

Set needs_user_clarification=true only when a safe and properly scoped briefing cannot be produced.
""".strip()
    rework_instructions: str = """
You are revising a plan after a failed quality review. You receive reviewer feedback and prior artifacts (planner output, research, synthesizer memo). Downstream agents do not see chat history, so all decisions, corrections, and constraints must be captured in structured fields and post_review_rationale.

Set post_review_next_agent:
- "research" when facts, sources, coverage, identity resolution, or scope are incomplete, incorrect, or potentially tied to the wrong person/company.
- "synthesizer" when the evidence is sufficient but the memo needs improvements in structure, focus, tone, clarity, prioritization, or citation usage.

If routing back to research:
- tighten plan_steps and research_queries with explicit disambiguation tokens such as company, role, region, division, product, or email domain.
- exclude unrelated same-name individuals and off-scope entities.
- avoid queries that contain only a personal name when ambiguity is possible.

If identity ambiguity remains unresolved:
- add focused clarifying_questions when user input is required to safely continue.
- otherwise constrain research as tightly as possible using available context.
""".strip()
    tools = ()
    response_model = PlannerResponse

    _graph_primary: ClassVar[Any | None] = None
    _graph_rework: ClassVar[Any | None] = None

    @classmethod
    def resolve_primary_instructions(cls, cfg: AgentsConfig) -> str:
        """System prompt for the initial planning pass."""
        return resolved_system_prompt(cfg.planner_system_prompt, cls.instructions)

    @classmethod
    def resolve_rework_instructions(cls, cfg: AgentsConfig) -> str:
        """System prompt when routing back from a failed review."""
        return resolved_system_prompt(cfg.planner_rework_system_prompt, cls.rework_instructions)

    @classmethod
    def ensure_primary_graph(cls, factory: AgentFactory) -> Any:
        """Singleton LangGraph agent for the first planning pass."""
        if cls._graph_primary is None:
            cls._graph_primary = factory.create_agent(
                role=cls.role,
                name=cls.graph_name_primary,
                instructions=cls.resolve_primary_instructions(factory.agents_config),
                tools=cls.tools or None,
                response_format=cls.response_model,
            )
        return cls._graph_primary

    @classmethod
    def ensure_rework_graph(cls, factory: AgentFactory) -> Any:
        """Singleton LangGraph agent for post-review plan revision."""
        if cls._graph_rework is None:
            cls._graph_rework = factory.create_agent(
                role=cls.role,
                name=cls.graph_name_rework,
                instructions=cls.resolve_rework_instructions(factory.agents_config),
                tools=cls.tools or None,
                response_format=cls.response_model,
            )
        return cls._graph_rework
