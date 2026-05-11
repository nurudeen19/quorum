"""Research agent definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from app.config.agents import AgentName, AgentsConfig, resolved_system_prompt
from app.schema.agents import ResearchResponse
from app.tools.search_tools import tavily_web_search, brave_web_search

if TYPE_CHECKING:
    from app.core.agent_factory import AgentFactory


class ResearchAgent:
    """Research role configuration."""

    role: AgentName = "research"
    name = "research_agent"
    description = "Runs live web search to profile attendees and companies for the briefing."
    instructions: str = """
You are the research agent for executive pre-meeting briefings. Execute the planner's research_queries using web search tools.

Identity and scope are strict:
- Only collect information that clearly matches each attendee based on the planner's disambiguation context (company, role, region, division, product, or other identifiers).
- Exclude information about same-name individuals without a credible connection to the target attendee or organization.
- If identity confidence is weak or evidence conflicts, omit uncertain material and explain the limitation in caveats.
- Do not pad the report with unrelated profiles or speculative matches.

Evidence quality requirements:
- Prefer primary, reputable, or mainstream sources.
- Attribute material claims with source and date in raw_report.
- Include URLs and/or outlet + headline in source_summary for key evidence.
- Never invent citations, affiliations, achievements, or relationships.
- Flag stale information, weak sources, conflicting claims, or missing verification in caveats.

Structure raw_report by attendee and company using short, scannable sections with dated facts tied to identifiable context.
""".strip()
    tools = (tavily_web_search, brave_web_search)
    response_model = ResearchResponse

    _graph: ClassVar[Any | None] = None

    @classmethod
    def resolve_instructions(cls, cfg: AgentsConfig) -> str:
        """System prompt for the research role."""
        return resolved_system_prompt(cfg.research_system_prompt, cls.instructions)

    @classmethod
    def ensure_graph(cls, factory: AgentFactory) -> Any:
        """Singleton LangGraph agent for research."""
        if cls._graph is None:
            cls._graph = factory.create_agent(
                role=cls.role,
                name=cls.name,
                instructions=cls.resolve_instructions(factory.agents_config),
                tools=cls.tools or None,
                response_format=cls.response_model,
            )
        return cls._graph
