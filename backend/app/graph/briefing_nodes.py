"""Graph node callables (guardrails → planner → research → synthesizer → reviewer).

See :mod:`app.graph.briefing_graph` for how these connect.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agents.planner import PlannerAgent
from app.agents.research import ResearchAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.synthesizer import SynthesizerAgent
from app.config.agents import AgentsConfig
from app.config.settings import Settings, get_settings
from app.core.agent_factory import AgentFactory
from app.graph.briefing_graph import BriefingState
from app.guardrails.input_size import validate_input_size
from app.guardrails.prompt_guard import classify_prompt, is_prompt_guard_loaded
from app.schema.agents import PlannerResponse, ResearchResponse, ReviewerResponse, SynthesizerResponse

logger = logging.getLogger(__name__)

_RESEARCH_STRUCTURE_USER = (
    "Based strictly on the conversation and tool results above, emit one structured research "
    "response. Include only evidence scoped to the planner's attendees and companies; exclude "
    "unrelated same-name individuals. Attribute claims to sources in raw_report and "
    "source_summary. Use caveats for uncertainty, conflicts, or deliberately omitted ambiguous hits."
)


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

    def _cfg(self) -> AgentsConfig:
        return self._factory.agents_config

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
        llm = self._factory.build_model_for_role("planner")
        structured = llm.with_structured_output(PlannerResponse)
        messages, is_rework = _planner_messages(state, self._cfg())

        out: PlannerResponse = await structured.ainvoke(messages)
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
        task = json.dumps(po, indent=2, default=str)[:80_000]
        cfg = self._cfg()
        llm = self._factory.build_model_for_role("research")
        messages = await _invoke_tools_until_done(
            llm,
            system_prompt=ResearchAgent.resolve_instructions(cfg),
            human_task="Execute the planner output below. Use tools for live web search.\n\n" + task,
            tools=ResearchAgent.tools,
        )
        parse_llm = self._factory.build_model_for_role("research")
        structured = parse_llm.with_structured_output(ResearchResponse)
        research_out: ResearchResponse = await structured.ainvoke(
            messages + [HumanMessage(content=_RESEARCH_STRUCTURE_USER)]
        )
        return {"research_output": research_out.model_dump()}

    async def synthesizer(self, state: BriefingState) -> dict[str, Any]:
        po = state.get("planner_output") or {}
        ro = state.get("research_output") or {}
        cfg = self._cfg()
        llm = self._factory.build_model_for_role("synthesizer")
        structured = llm.with_structured_output(SynthesizerResponse)
        payload = json.dumps({"planner": po, "research": ro}, indent=2, default=str)[:100_000]
        out: SynthesizerResponse = await structured.ainvoke(
            [
                SystemMessage(content=SynthesizerAgent.resolve_instructions(cfg)),
                HumanMessage(
                    content="Produce the executive briefing memo from this JSON:\n\n" + payload
                ),
            ]
        )
        return {"synthesizer_output": out.model_dump()}

    async def reviewer(self, state: BriefingState) -> dict[str, Any]:
        po = state.get("planner_output") or {}
        ro = state.get("research_output") or {}
        so = state.get("synthesizer_output") or {}
        cfg = self._cfg()
        llm = self._factory.build_model_for_role("reviewer")
        structured = llm.with_structured_output(ReviewerResponse)
        bundle = json.dumps(
            {"planner": po, "research": ro, "synthesizer": so},
            indent=2,
            default=str,
        )[:120_000]
        verdict: ReviewerResponse = await structured.ainvoke(
            [
                SystemMessage(content=ReviewerAgent.resolve_instructions(cfg)),
                HumanMessage(
                    content=(
                        "Evaluate whether the synthesizer memo is acceptable for an executive reader. "
                        "Confirm alignment with planner scope (meeting subject, each attendee name "
                        "and company, briefing_goal, context_notes/disambiguation), accuracy vs "
                        "research, citations/source list coherence, and tone.\n\n"
                        f"{bundle}"
                    )
                ),
            ]
        )
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


def _planner_messages(state: BriefingState, cfg: AgentsConfig) -> tuple[list[Any], bool]:
    history = (state.get("conversation_history") or "").strip() or "(no prior conversation)"
    user_msg = (state.get("user_message") or "").strip()
    rejection = (state.get("review_rejection_notes") or "").strip()

    if rejection:
        system = PlannerAgent.resolve_rework_instructions(cfg)
        human = _planner_rework_human(user_msg=user_msg, rejection=rejection, state=state)
        return ([SystemMessage(content=system), HumanMessage(content=human)], True)

    system = PlannerAgent.resolve_primary_instructions(cfg)
    human = (
        "Conversation history (only you see this—encode needed facts into your plan):\n"
        f"{history}\n\n"
        "Current user message (meeting subject, attendees with companies, goals):\n"
        f"{user_msg}"
    )
    return ([SystemMessage(content=system), HumanMessage(content=human)], False)


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


async def _invoke_tools_until_done(
    llm: Any,
    *,
    system_prompt: str,
    human_task: str,
    tools: tuple[Any, ...],
    max_steps: int = 12,
) -> list[Any]:
    messages: list[Any] = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_task),
    ]
    model = llm.bind_tools(list(tools))
    for _ in range(max_steps):
        ai = await model.ainvoke(messages)
        messages.append(ai)
        if not isinstance(ai, AIMessage) or not ai.tool_calls:
            break
        for tc in ai.tool_calls:
            name = tc["name"] if isinstance(tc, dict) else getattr(tc, "name", "")
            tc_id = tc["id"] if isinstance(tc, dict) else getattr(tc, "id", "")
            args = tc["args"] if isinstance(tc, dict) else getattr(tc, "args", {})
            tool_fn = next((t for t in tools if getattr(t, "name", None) == name), None)
            if tool_fn is None:
                messages.append(
                    ToolMessage(content=f"Unknown tool {name}", tool_call_id=tc_id)
                )
                continue
            try:
                out = await asyncio.to_thread(tool_fn.invoke, args)
            except Exception as exc:
                out = f"Tool error: {exc}"
                logger.warning(
                    "briefing_tool_invoke_failed",
                    extra={"tool": name, "error_type": type(exc).__name__},
                )
            messages.append(ToolMessage(content=str(out), tool_call_id=tc_id))
    return messages
