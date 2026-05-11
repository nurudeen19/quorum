"""Graph node callables (guardrails → planner → research → synthesizer → reviewer).

See :mod:`app.graph.briefing_graph` for how these connect.

**Reusable briefing agents**
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.config.settings import Settings, get_settings
from app.core.agent_factory import AgentFactory
from app.graph.briefing_graph import BriefingState
from app.guardrails.input_size import validate_input_size
from app.guardrails.prompt_guard import classify_prompt, is_prompt_guard_loaded
from app.schema.agents import PlannerResponse, ResearchResponse, ReviewerResponse, SynthesizerResponse

logger = logging.getLogger(__name__)

_CONTEXT_SNIP_CAP = 12_000

TStruct = TypeVar("TStruct", bound=BaseModel)


def _agent_structured(result: Any, model: type[TStruct]) -> TStruct:
    """Extract Pydantic output from a LangChain ``create_agent`` graph result."""
    if not isinstance(result, dict):
        raise TypeError(f"Expected dict agent result, got {type(result).__name__}")
    sr = result.get("structured_response")
    if isinstance(sr, model):
        return sr
    if sr is not None:
        return model.model_validate(sr)
    raise ValueError(
        "Briefing agent returned no structured_response; check model/tool configuration and logs."
    )


def _research_human_task(state: BriefingState, planner_output: dict[str, Any]) -> str:
    """Planner JSON is authoritative; user text and history add spellings and clarifications."""
    body = json.dumps(planner_output, indent=2, default=str)[:80_000]
    lines = [
        "Execute the planner output below. Use web search tools as needed, then respond with the "
        "structured research fields (raw_report, source_summary, caveats) grounded in tool results.",
        "",
        "Planner output (authoritative scope for who and what to research):",
        body,
    ]
    user_msg = (state.get("user_message") or "").strip()
    if user_msg:
        lines.extend(
            ["", "Current user message (verbatim phrasing and spellings):", user_msg[:_CONTEXT_SNIP_CAP]]
        )
    history = (state.get("conversation_history") or "").strip()
    if history:
        lines.extend(
            [
                "",
                "Prior conversation (context only; if this conflicts with the planner, follow the planner):",
                history[:_CONTEXT_SNIP_CAP],
            ]
        )
    return "\n".join(lines)


def _synthesizer_payload(
    state: BriefingState, planner: dict[str, Any], research: dict[str, Any]
) -> dict[str, Any]:
    payload: dict[str, Any] = {"planner": planner, "research": research}
    user_msg = (state.get("user_message") or "").strip()
    if user_msg:
        payload["user_message"] = user_msg[:_CONTEXT_SNIP_CAP]
    history = (state.get("conversation_history") or "").strip()
    if history:
        payload["conversation_history"] = history[:_CONTEXT_SNIP_CAP]
    return payload


def _reviewer_bundle(
    state: BriefingState,
    planner: dict[str, Any],
    research: dict[str, Any],
    synthesizer: dict[str, Any],
) -> dict[str, Any]:
    bundle: dict[str, Any] = {
        "planner": planner,
        "research": research,
        "synthesizer": synthesizer,
    }
    user_msg = (state.get("user_message") or "").strip()
    if user_msg:
        bundle["user_message"] = user_msg[:_CONTEXT_SNIP_CAP]
    return bundle


def build_briefing_nodes(factory: AgentFactory) -> dict[str, Any]:
    """Return ``node_id → async callable`` for :func:`~app.graph.briefing_graph.build_briefing_graph`."""
    h = _BriefingNodes(factory)
    return {
        "guardrails": h.guardrails,
        "planner": h.planner,
        "research": h.research,
        "synthesizer": h.synthesizer,
        "reviewer": h.reviewer,
    }


class _BriefingNodes:
    def __init__(self, factory: AgentFactory) -> None:
        self._factory = factory

    def _settings(self) -> Settings:
        return get_settings()

    async def guardrails(self, state: BriefingState) -> dict[str, Any]:
        s = self._settings()
        text = (state.get("user_message") or "").strip()
        err = validate_input_size(text, s)
        if err:
            return {
                "validation_error": err,
                "status": "guardrail_error",
                "final_user_message": err,
            }
        if s.enable_promtpt_guard and is_prompt_guard_loaded():
            safe, denial = classify_prompt(text, settings=s)
            if not safe:
                msg = denial or "This message could not be accepted."
                return {
                    "validation_error": msg,
                    "status": "guardrail_error",
                    "final_user_message": msg,
                }
        elif s.enable_promtpt_guard:
            logger.warning(
                "briefing_prompt_guard_enabled_but_not_loaded",
                extra={"event": "briefing_prompt_guard_skip"},
            )
        return {"validation_error": None}

    async def planner(self, state: BriefingState) -> dict[str, Any]:
        ba = self._factory.briefing_agents
        rejection = (state.get("review_rejection_notes") or "").strip()
        if rejection:
            agent = ba.planner_rework
            user_msg = (state.get("user_message") or "").strip()
            human = _planner_rework_human(user_msg=user_msg, rejection=rejection, state=state)
            is_rework = True
        else:
            agent = ba.planner_primary
            human = _planner_primary_human(state)
            is_rework = False

        result = await agent.ainvoke({"messages": [HumanMessage(content=human)]})
        out = _agent_structured(result, PlannerResponse)
        if is_rework:
            out = _normalize_planner_rework(out)

        if not is_rework and out.needs_user_clarification:
            bullets = "\n".join(f"- {q}" for q in out.clarifying_questions)
            return {
                "planner_output": out.model_dump(),
                "status": "needs_clarification",
                "final_user_message": (
                    "Before I can research and draft your briefing, I need a bit more detail:\n"
                    + bullets
                ),
            }

        return {"planner_output": out.model_dump(), "status": "pending"}

    async def research(self, state: BriefingState) -> dict[str, Any]:
        po = state.get("planner_output") or {}
        human = _research_human_task(state, po)
        result = await self._factory.briefing_agents.research.ainvoke({"messages": [HumanMessage(content=human)]})
        research_out = _agent_structured(result, ResearchResponse)
        return {"research_output": research_out.model_dump()}

    async def synthesizer(self, state: BriefingState) -> dict[str, Any]:
        po = state.get("planner_output") or {}
        ro = state.get("research_output") or {}
        payload = json.dumps(
            _synthesizer_payload(state, po, ro),
            indent=2,
            default=str,
        )[:100_000]
        human = (
            "Produce the executive briefing memo from this JSON. "
            "Treat planner as authoritative for scope; use user_message for verbatim "
            "names/spelling when they clarify attendees.\n\n"
            + payload
        )
        result = await self._factory.briefing_agents.synthesizer.ainvoke({"messages": [HumanMessage(content=human)]})
        out = _agent_structured(result, SynthesizerResponse)
        return {"synthesizer_output": out.model_dump()}

    async def reviewer(self, state: BriefingState) -> dict[str, Any]:
        po = state.get("planner_output") or {}
        ro = state.get("research_output") or {}
        so = state.get("synthesizer_output") or {}
        bundle = json.dumps(
            _reviewer_bundle(state, po, ro, so),
            indent=2,
            default=str,
        )[:120_000]
        human = (
            "Evaluate whether the synthesizer memo is acceptable for an executive reader. "
            "Confirm alignment with planner scope (meeting subject, each attendee name "
            "and company, briefing_goal, context_notes/disambiguation) and with "
            "user_message when present, accuracy vs research, citations/source list "
            "coherence, and tone.\n\n"
            f"{bundle}"
        )
        result = await self._factory.briefing_agents.reviewer.ainvoke({"messages": [HumanMessage(content=human)]})
        verdict = _agent_structured(result, ReviewerResponse)
        return _review_updates(
            verdict=verdict,
            synthesizer_output=so,
            previous_review_cycle=int(state.get("review_cycle") or 0),
            max_cycles=self._settings().briefing_max_review_cycles,
        )


def _review_updates(
    *,
    verdict: ReviewerResponse,
    synthesizer_output: dict[str, Any],
    previous_review_cycle: int,
    max_cycles: int,
) -> dict[str, Any]:
    memo_md = str(synthesizer_output.get("executive_briefing_markdown") or "")
    failed_attempt_number = previous_review_cycle + 1
    ok = verdict.approved and verdict.tone_and_safety_ok

    if ok:
        return {
            "reviewer_output": verdict.model_dump(),
            "status": "completed",
            "final_user_message": memo_md,
            "review_rejection_notes": None,
        }

    if failed_attempt_number > max_cycles:
        return {
            "reviewer_output": verdict.model_dump(),
            "status": "failed",
            "final_user_message": (
                "The briefing could not pass automated review after multiple attempts. "
                "Please try again with clearer attendee names/companies or narrow goals.\n\n"
                f"Reviewer notes: {verdict.issues}"
            ),
            "review_rejection_notes": None,
        }

    return {
        "reviewer_output": verdict.model_dump(),
        "review_rejection_notes": verdict.issues,
        "review_cycle": failed_attempt_number,
        "status": "pending",
    }


def _planner_primary_human(state: BriefingState) -> str:
    history = (state.get("conversation_history") or "").strip() or "(no prior conversation)"
    user_msg = (state.get("user_message") or "").strip()
    return (
        "Conversation history (only you see this—encode needed facts into your plan):\n"
        f"{history}\n\n"
        "Current user message (meeting subject, attendees with companies, goals):\n"
        f"{user_msg}"
    )


def _planner_rework_human(
    *,
    user_msg: str,
    rejection: str,
    state: BriefingState,
) -> str:
    po = state.get("planner_output") or {}
    sync = state.get("synthesizer_output") or {}
    research = state.get("research_output") or {}
    ctx = json.dumps(
        {
            "previous_planner": po,
            "research": research,
            "synthesizer": sync,
            "reviewer_feedback": rejection,
        },
        indent=2,
        default=str,
    )[:60_000]
    return (
        "Revision context (JSON):\n"
        f"{ctx}\n\n"
        f"Original user request (still authoritative):\n{user_msg}\n\n"
        "Return structured output including post_review_next_agent and rationale."
    )


def _normalize_planner_rework(out: PlannerResponse) -> PlannerResponse:
    return out.model_copy(
        update={
            "needs_user_clarification": False,
            "clarifying_questions": [],
            "post_review_next_agent": out.post_review_next_agent or "research",
            "post_review_rationale": out.post_review_rationale
            or "Address reviewer feedback in the next iteration.",
        }
    )
