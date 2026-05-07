"""Agent definitions, one file per role."""

from typing import TypeAlias

from app.agents.planner import PlannerAgent
from app.agents.research import ResearchAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.synthesizer import SynthesizerAgent
from app.config.agents import AgentName

PLANNER_AGENT = PlannerAgent()
RESEARCH_AGENT = ResearchAgent()
REVIEWER_AGENT = ReviewerAgent()
SYNTHESIZER_AGENT = SynthesizerAgent()

AgentDefinition: TypeAlias = PlannerAgent | ResearchAgent | ReviewerAgent | SynthesizerAgent

AGENT_DEFINITIONS: dict[AgentName, AgentDefinition] = {
    "planner": PLANNER_AGENT,
    "research": RESEARCH_AGENT,
    "reviewer": REVIEWER_AGENT,
    "synthesizer": SYNTHESIZER_AGENT,
}

__all__ = [
    "PlannerAgent",
    "ResearchAgent",
    "ReviewerAgent",
    "SynthesizerAgent",
    "PLANNER_AGENT",
    "RESEARCH_AGENT",
    "REVIEWER_AGENT",
    "SYNTHESIZER_AGENT",
    "AgentDefinition",
    "AGENT_DEFINITIONS",
]
