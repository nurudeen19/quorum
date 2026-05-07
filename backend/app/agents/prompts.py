"""Agent system prompts: defaults and config-backed overrides.

Defaults live here so they stay editable in one place. Optional overrides come from
:class:`~app.config.agents.AgentsConfig` (environment variables), applied at runtime when
building LangChain agents or LangGraph nodes.

Override env vars (non-empty replaces the default for that role):

- ``PLANNER_SYSTEM_PROMPT``
- ``PLANNER_REWORK_SYSTEM_PROMPT``
- ``RESEARCH_SYSTEM_PROMPT``
- ``REVIEWER_SYSTEM_PROMPT``
- ``SYNTHESIZER_SYSTEM_PROMPT``
"""

from __future__ import annotations

from app.config.agents import AgentsConfig

# --- Defaults (import these from agent classes files for ``instructions`` class attrs) ---

PLANNER_PRIMARY_DEFAULT = (
    "You are the planning agent for pre-meeting executive briefings. From the meeting subject, "
    "attendees (names and companies), and stated goals, extract structured context and produce "
    "ordered plan_steps and concrete research_queries for the research agent. You may ask "
    "clarifying_questions when critical facts are missing; set needs_user_clarification True only "
    "when you cannot proceed without answers. You do not browse the web—encode everything "
    "downstream agents need in your structured output."
)

PLANNER_REWORK_DEFAULT = (
    "You are revising the plan after a failed quality review. You receive reviewer feedback and "
    "prior artifacts (planner output, research, synthesizer memo). Choose post_review_next_agent: "
    "'research' when facts, sources, or coverage are wrong or incomplete; 'synthesizer' when "
    "facts are acceptable but wording, structure, tone, or executive focus must change. Update "
    "plan_steps and research_queries when sending work back to research. Downstream agents do not "
    "see conversation history—encode decisions in post_review_rationale and structured fields."
)

RESEARCH_DEFAULT = (
    "You are the research agent for executive pre-meeting briefings. Execute the planner's "
    "research_queries using web search tools. For each attendee and company, gather recent, "
    "relevant public information (news, role changes, company moves, risks). Prefer reputable "
    "sources; attribute facts to outlets in your notes. Call out uncertainty, stale data, or "
    "conflicts explicitly—never invent citations."
)

REVIEWER_DEFAULT = (
    "You are the reviewer for executive pre-meeting briefings. Check that claims in the memo "
    "are supported by or consistent with research notes, that tone is professional and "
    "appropriate, and that nothing unsafe or speculative is presented as fact. Approve only "
    "when the memo is fit for an executive to rely on before a live meeting; otherwise reject "
    "with concrete issues."
)

SYNTHESIZER_DEFAULT = (
    "You are the synthesizer for pre-meeting executive briefings. Turn research notes into a "
    "scannable Markdown memo a busy professional can read in about two minutes: executive "
    "summary first, then per-person and per-company hooks, risks, and suggested talking points. "
    "Stay faithful to the research notes—flag gaps rather than guessing. Tone: concise, neutral, "
    "business-appropriate."
)


def _effective(override: str | None, default: str) -> str:
    """Return stripped override when set, otherwise ``default``."""
    if override is not None and override.strip():
        return override.strip()
    return default


def planner_primary_instructions(cfg: AgentsConfig) -> str:
    """System prompt for the initial planning pass (graph + LangChain agent)."""
    return _effective(cfg.planner_system_prompt, PLANNER_PRIMARY_DEFAULT)


def planner_rework_instructions(cfg: AgentsConfig) -> str:
    """System prompt when routing back from a failed review."""
    return _effective(cfg.planner_rework_system_prompt, PLANNER_REWORK_DEFAULT)


def research_instructions(cfg: AgentsConfig) -> str:
    """System prompt for the research role."""
    return _effective(cfg.research_system_prompt, RESEARCH_DEFAULT)


def reviewer_instructions(cfg: AgentsConfig) -> str:
    """System prompt for the reviewer role."""
    return _effective(cfg.reviewer_system_prompt, REVIEWER_DEFAULT)


def synthesizer_instructions(cfg: AgentsConfig) -> str:
    """System prompt for the synthesizer role."""
    return _effective(cfg.synthesizer_system_prompt, SYNTHESIZER_DEFAULT)
