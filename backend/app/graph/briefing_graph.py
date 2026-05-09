"""Executive briefing LangGraph: **read this file first** for the full pipeline.

Flow::

    START → guardrails → planner → research → synthesizer → reviewer → END

Branches::

    guardrails  → END on validation_error / guardrail_error
    planner     → END on needs_clarification
                → synthesizer if redo-synth only AND research_output.raw_report present
                → research otherwise
    reviewer    → END on completed / failed (max retries)
                → planner with reviewer feedback otherwise

Node implementations (LLM calls, tools) live in :mod:`app.graph.briefing_nodes`.
Chat turns run this graph via :class:`app.services.chat_service.ChatService`.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.agent_factory import AgentFactory

# --- State --------------------------------------------------------------------

NODE_GUARD = "guardrails"
NODE_PLANNER = "planner"
NODE_RESEARCH = "research"
NODE_SYNTHESIZER = "synthesizer"
NODE_REVIEWER = "reviewer"


class BriefingState(TypedDict, total=False):
    """Graph state passed between nodes."""

    user_message: str
    conversation_history: str
    validation_error: str | None
    planner_output: dict | None
    research_output: dict | None
    synthesizer_output: dict | None
    reviewer_output: dict | None
    review_rejection_notes: str | None
    review_cycle: int
    status: Literal["pending", "guardrail_error", "needs_clarification", "completed", "failed"]
    final_user_message: str | None


def create_initial_briefing_state(
    *,
    user_message: str,
    conversation_history: str = "",
) -> BriefingState:
    """Initial state for :class:`app.services.chat_service.ChatService`."""
    return {
        "user_message": user_message.strip(),
        "conversation_history": (conversation_history or "").strip(),
        "review_cycle": 0,
        "status": "pending",
        "validation_error": None,
        "review_rejection_notes": None,
        "planner_output": None,
        "research_output": None,
        "synthesizer_output": None,
        "reviewer_output": None,
        "final_user_message": None,
    }


# --- Conditional routing (used only by ``build_briefing_graph``) ---


def _after_guard(state: BriefingState):
    if state.get("validation_error"):
        return END
    if state.get("status") == "guardrail_error":
        return END
    return NODE_PLANNER


def _after_planner(state: BriefingState):
    if state.get("status") == "needs_clarification":
        return END
    planner = state.get("planner_output") or {}
    raw = (state.get("research_output") or {}).get("raw_report")
    has_research = bool(str(raw or "").strip())
    if planner.get("post_review_next_agent") == "synthesizer" and has_research:
        return NODE_SYNTHESIZER
    return NODE_RESEARCH


def _after_review(state: BriefingState):
    if state.get("status") in ("completed", "failed"):
        return END
    return NODE_PLANNER


# --- Compile & run ------------------------------------------------------------

def _apply_briefing_topology(g: StateGraph[BriefingState], nodes: dict[str, Any]) -> None:
    """Register briefing nodes and edges on ``g`` (shared by runtime graph and diagram stubs)."""
    g.add_node(NODE_GUARD, nodes["guardrails"])
    g.add_node(NODE_PLANNER, nodes["planner"])
    g.add_node(NODE_RESEARCH, nodes["research"])
    g.add_node(NODE_SYNTHESIZER, nodes["synthesizer"])
    g.add_node(NODE_REVIEWER, nodes["reviewer"])

    g.add_edge(START, NODE_GUARD)
    g.add_conditional_edges(NODE_GUARD, _after_guard, {NODE_PLANNER: NODE_PLANNER, END: END})
    g.add_conditional_edges(
        NODE_PLANNER,
        _after_planner,
        {NODE_RESEARCH: NODE_RESEARCH, NODE_SYNTHESIZER: NODE_SYNTHESIZER, END: END},
    )
    g.add_edge(NODE_RESEARCH, NODE_SYNTHESIZER)
    g.add_edge(NODE_SYNTHESIZER, NODE_REVIEWER)
    g.add_conditional_edges(NODE_REVIEWER, _after_review, {NODE_PLANNER: NODE_PLANNER, END: END})


async def _diagram_stub_node(_state: BriefingState) -> dict[str, Any]:
    """No-op node for structure-only graph visualization."""
    return {}


def build_briefing_graph_for_diagram() -> Any:
    """Compile the briefing graph with stub nodes for Mermaid / PNG export (no API keys)."""
    stub_nodes = {
        "guardrails": _diagram_stub_node,
        "planner": _diagram_stub_node,
        "research": _diagram_stub_node,
        "synthesizer": _diagram_stub_node,
        "reviewer": _diagram_stub_node,
    }
    g = StateGraph(BriefingState)
    _apply_briefing_topology(g, stub_nodes)
    return g.compile()


def build_briefing_graph(factory: AgentFactory) -> Any:
    """Wire nodes and edges; returns a compiled graph (reuse — do not rebuild every request)."""
    # Lazy import keeps this module readable without pulling LLM node code at import time.
    from app.graph.briefing_nodes import build_briefing_nodes

    nodes = build_briefing_nodes(factory)
    g = StateGraph(BriefingState)
    _apply_briefing_topology(g, nodes)
    return g.compile()
