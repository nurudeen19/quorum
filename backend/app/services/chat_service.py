"""Chat orchestration: **conversations** own message threads; users have many conversations.
The **briefing graph** runs per turn to produce assistant replies, taking the conversation history as context. The graph state is streamed back to the client for a live-updating UI, and the final assistant reply is persisted to the DB as a new message in the conversation.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import structlog
import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.base import ConversationHistorySnapshot
from app.config import get_settings
from app.core.agent_factory import AgentFactory
from app.core.bootstrap import get_bootstrap
from app.graph.briefing_graph import (
    BriefingState,
    build_briefing_graph,
    create_initial_briefing_state,
)
from app.models.message import MessageRole
from app.services.exceptions import ConversationNotFoundError
from app.services.history_service import HistoryService

logger = structlog.get_logger(__name__)

_RECURSION_LIMIT = 200


def build_chat_graph_run_config(
    *,
    user_id: UUID | None = None,
    conversation_id: UUID | None = None,
) -> dict[str, Any]:
    """LangGraph ``RunnableConfig`` fragment: recursion limit + LangSmith run metadata/tags."""
    cfg: dict[str, Any] = {"recursion_limit": _RECURSION_LIMIT}
    if user_id is not None and conversation_id is not None:
        cfg["metadata"] = {
            "user_id": str(user_id),
            "conversation_id": str(conversation_id),
        }
        cfg["tags"] = ["chat", "executive_briefing"]
        cfg["run_name"] = f"chat:{conversation_id}"
    return cfg


def format_history_for_chat(snap: ConversationHistorySnapshot) -> str:
    """Turn cache/DB snapshot into prior context for the assistant pipeline."""
    parts: list[str] = []
    if snap.agent_summary and str(snap.agent_summary).strip():
        parts.append(f"[Conversation summary for agents]\n{snap.agent_summary.strip()}")
    for m in snap.messages:
        parts.append(f"{m.role}: {m.content}")
    return "\n".join(parts).strip()


def chat_stream_state_payload(state: BriefingState) -> dict[str, Any]:
    """SSE-friendly snapshot of pipeline state (trim huge blobs)."""
    d: dict[str, Any] = dict(state)
    ro = d.get("research_output")
    if isinstance(ro, dict):
        raw = ro.get("raw_report")
        if isinstance(raw, str) and len(raw) > 800:
            d = {
                **d,
                "research_output": {
                    **ro,
                    "raw_report": raw[:800] + "…(truncated for stream)",
                },
            }
    return d


def assistant_reply_from_briefing_state(state: BriefingState) -> str:
    """User-visible assistant text from a completed briefing graph state."""
    final = state.get("final_user_message")
    if final and str(final).strip():
        return str(final)
    err = state.get("validation_error")
    if err and str(err).strip():
        return str(err)
    return "The briefing could not produce a response."


class ChatService:
    """Binds chat messages to user-owned conversations and runs the briefing graph per turn."""

    def __init__(self) -> None:
        self._lazy_lock = asyncio.Lock()

    async def _graph_and_factory(self) -> tuple[Any, AgentFactory]:
        """Prefer startup graph; otherwise build once and attach to bootstrap for reuse."""
        b = get_bootstrap()
        if b.executive_briefing_graph is not None and b.agent_factory is not None:
            return b.executive_briefing_graph, b.agent_factory

        async with self._lazy_lock:
            if b.executive_briefing_graph is not None and b.agent_factory is not None:
                return b.executive_briefing_graph, b.agent_factory
            settings = get_settings()
            factory = AgentFactory(settings.agents)
            graph = build_briefing_graph(factory)
            b.agent_factory = factory
            b.executive_briefing_graph = graph
            return graph, factory

    async def resolve_or_create_conversation(
        self,
        session: AsyncSession,
        history: HistoryService,
        *,
        user_id: UUID,
        conversation_id: UUID | None,
    ) -> UUID:
        """Pick the conversation for this message: continue an existing thread or open a new one.
        Raises:
            ConversationNotFoundError: No row for this user and id.
        """
        start = time.time()
        if conversation_id is None:
            conv = await history.create_conversation(session, user_id, title=None)
            await session.flush()
            logger.info(
                "chat_resolve_or_create_conversation_new",
                user_id=str(user_id),
                conversation_id=str(conv.id),
                duration_ms=int((time.time() - start) * 1000),
            )
            return conv.id
        conv = await history.get_conversation(session, user_id, conversation_id)
        if conv is None:
            logger.warning(
                "chat_resolve_or_create_conversation_not_found",
                user_id=str(user_id),
                conversation_id=str(conversation_id),
                duration_ms=int((time.time() - start) * 1000),
            )
            raise ConversationNotFoundError(conversation_id)
        logger.info(
            "chat_resolve_or_create_conversation_existing",
            user_id=str(user_id),
            conversation_id=str(conv.id),
            duration_ms=int((time.time() - start) * 1000),
        )
        return conv.id

    async def begin_user_turn(
        self,
        session: AsyncSession,
        history: HistoryService,
        *,
        user_id: UUID,
        conversation_id: UUID | None,
        user_content: str,
        conversation_title: str | None = None,
    ) -> tuple[UUID, str]:
        """Start a user turn: conversation selection, history retrieval, then store the user line.

        Returns:
            ``(conversation_id, conversation_history_text)`` for the graph (history excludes
            ``user_content``, which is passed separately as ``user_message``).
        """
        start = time.time()
        cid = await self.resolve_or_create_conversation(
            session,
            history,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        snap = await history.get_history(session, cid)
        history_text = format_history_for_chat(snap)
        await history.record_message(
            session,
            cid,
            MessageRole.user,
            user_content,
            conversation_title=conversation_title,
        )
        logger.info(
            "chat_begin_user_turn",
            user_id=str(user_id),
            conversation_id=str(cid),
            content_preview=user_content[:20],
            duration_ms=int((time.time() - start) * 1000),
        )
        return cid, history_text

    async def record_assistant_turn(
        self,
        session: AsyncSession,
        history: HistoryService,
        *,
        conversation_id: UUID,
        state: BriefingState,
    ) -> None:
        """Persist assistant reply from a finished briefing state."""
        start = time.time()
        reply = assistant_reply_from_briefing_state(state)
        await history.record_message(
            session,
            conversation_id,
            MessageRole.assistant,
            reply,
        )
        logger.info(
            "chat_record_assistant_turn",
            conversation_id=str(conversation_id),
            reply_preview=reply[:50],
            duration_ms=int((time.time() - start) * 1000),
        )

    async def invoke_briefing(
        self,
        *,
        user_message: str,
        conversation_history: str = "",
        user_id: UUID | None = None,
        conversation_id: UUID | None = None,
    ) -> BriefingState:
        """Run the briefing pipeline to completion (non-streaming)."""
        graph, fac = await self._graph_and_factory()
        initial = create_initial_briefing_state(
            user_message=user_message,
            conversation_history=conversation_history,
        )
        run_config = build_chat_graph_run_config(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        try:
            return await graph.ainvoke(initial, config=run_config)
        except Exception:
            logger.exception("chat_briefing_invoke_failed", factory_id=id(fac))
            return {
                **initial,
                "status": "failed",
                "final_user_message": (
                    "Something went wrong while preparing your briefing. Please try again shortly."
                ),
            }

    async def stream_briefing_values(
        self,
        *,
        user_message: str,
        conversation_history: str = "",
        user_id: UUID | None = None,
        conversation_id: UUID | None = None,
    ) -> AsyncIterator[BriefingState]:
        """Yield full pipeline state after each step (last yield is final)."""
        graph, _fac = await self._graph_and_factory()
        initial = create_initial_briefing_state(
            user_message=user_message,
            conversation_history=conversation_history,
        )
        run_config = build_chat_graph_run_config(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        try:
            async for state in graph.astream(
                initial,
                stream_mode="values",
                config=run_config,
            ):
                yield state
        except Exception:
            logger.exception("chat_briefing_stream_failed")
            yield {
                **initial,
                "status": "failed",
                "final_user_message": (
                    "Something went wrong while preparing your briefing. Please try again shortly."
                ),
            }

    @staticmethod
    def sse_event(payload: dict[str, Any]) -> str:
        """Format one Server-Sent Event line."""
        return f"data: {json.dumps(payload, default=str)}\n\n"


_chat_service: ChatService | None = None


def get_chat_service() -> ChatService:
    """Singleton for FastAPI ``Depends``."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
