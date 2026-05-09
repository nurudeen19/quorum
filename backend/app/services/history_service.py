"""Conversation history: PostgreSQL persistence + cache + optional background writes."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.base import CachedMessage, ConversationCache, ConversationHistorySnapshot
from app.config import get_settings
from app.core.agent_factory import AgentFactory
from app.core.bootstrap import get_bootstrap
from app.core.database import get_session_factory
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole

logger = structlog.get_logger(__name__)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


class HistoryService:
    """Load and record messages with cache-first reads."""

    def __init__(
        self,
        cache: ConversationCache,
        *,
        max_turns: int,
        summary_every_n_messages: int,
    ) -> None:
        self._cache = cache
        self._max_turns = max_turns
        self._message_capacity = max_turns * 2
        self._summary_interval = summary_every_n_messages

    async def _sync_agent_summary_to_cache(
        self, session: AsyncSession, conversation_id: UUID
    ) -> None:
        """Copy DB ``Conversation.summary`` into cache (agent context, not user API)."""
        summary = await session.scalar(
            select(Conversation.summary).where(Conversation.id == conversation_id)
        )
        await self._cache.set_agent_summary(conversation_id, summary)

    async def create_conversation(
        self, session: AsyncSession, user_id: UUID, title: str | None = None
    ) -> Conversation:
        """Persist a new conversation for the user."""
        conv = Conversation(user_id=user_id, title=title)
        session.add(conv)
        await session.flush()
        return conv

    async def get_conversation(
        self, session: AsyncSession, user_id: UUID, conversation_id: UUID
    ) -> Conversation | None:
        """Return conversation if it belongs to the user."""
        stmt = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    async def get_history(
        self, session: AsyncSession, conversation_id: UUID
    ) -> ConversationHistorySnapshot:
        """Return agent snapshot: optional summary + message tail. Cache enforces max turns on append only."""
        snap = await self._cache.get(conversation_id)
        if snap.messages:
            return snap

        conv_summary = await session.scalar(
            select(Conversation.summary).where(Conversation.id == conversation_id)
        )
        await self._cache.set_agent_summary(conversation_id, conv_summary)

        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(self._message_capacity)
        )
        rows = list((await session.scalars(stmt)).all())
        chronological = list(reversed(rows))
        for m in chronological:
            cm = CachedMessage(
                role=m.role.value,
                content=m.content,
                created_at=_ensure_utc(m.created_at),
            )
            await self._cache.append(conversation_id, cm)
        return await self._cache.get(conversation_id)

    async def record_message(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
    ) -> Message:
        """Insert message, update message tail in cache, sync agent summary field into cache."""
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        session.add(msg)
        await session.flush()
        created = msg.created_at or datetime.now(timezone.utc)
        cm = CachedMessage(
            role=msg.role.value,
            content=msg.content,
            created_at=_ensure_utc(created),
        )
        await self._cache.append(conversation_id, cm)
        await self._sync_agent_summary_to_cache(session, conversation_id)
        await self._maybe_schedule_summary(session, conversation_id)
        return msg

    async def _maybe_schedule_summary(
        self, session: AsyncSession, conversation_id: UUID
    ) -> None:
        if self._summary_interval <= 0:
            return
        total = await session.scalar(
            select(func.count())
            .select_from(Message)
            .where(Message.conversation_id == conversation_id)
        )
        if total and total % self._summary_interval == 0:
            self.dispatch_summary_refresh(conversation_id)

    def dispatch_summary_refresh(self, conversation_id: UUID) -> asyncio.Task[None]:
        """Background: refresh DB summary and push to cache for agents."""

        async def _run() -> None:
            try:
                factory = get_session_factory()
                if factory is None:
                    logger.warning("summary_skipped_no_database")
                    return
                settings = get_settings()
                bs = get_bootstrap()
                factory = bs.agent_factory
                if factory is not None:
                    llm = factory.build_model_for_role("synthesizer")
                else:
                    llm = AgentFactory(settings.agents).build_model_for_role("synthesizer")
                async with factory() as session:
                    msgs = list(
                        (
                            await session.scalars(
                                select(Message)
                                .where(Message.conversation_id == conversation_id)
                                .order_by(Message.created_at)
                            )
                        ).all()
                    )
                if not msgs:
                    return
                transcript = "\n".join(f"{m.role.value}: {m.content}" for m in msgs)
                out = await llm.ainvoke(
                    [
                        SystemMessage(
                            content=(
                                "Summarize the following dialogue in 2–5 concise sentences. "
                                "This summary is for downstream agents, not end users. "
                                "Capture facts, decisions, and open questions."
                            )
                        ),
                        HumanMessage(content=transcript[:120_000]),
                    ]
                )
                summary_text = getattr(out, "content", None) or str(out)
                async with factory() as session:
                    async with session.begin():
                        await session.execute(
                            update(Conversation)
                            .where(Conversation.id == conversation_id)
                            .values(summary=summary_text)
                        )
                await self._cache.set_agent_summary(conversation_id, summary_text)
            except Exception:
                logger.exception(
                    "conversation_summary_failed",
                    conversation_id=str(conversation_id),
                )

        return asyncio.create_task(_run())

    def dispatch_record_message(
        self,
        conversation_id: UUID,
        role: MessageRole | str,
        content: str,
    ) -> asyncio.Task[None]:
        """Fire-and-forget persist + cache append + summary sync (does not block caller)."""
        role_enum = role if isinstance(role, MessageRole) else MessageRole(str(role))

        async def _run() -> None:
            try:
                factory = get_session_factory()
                if factory is None:
                    logger.warning("history_dispatch_skipped_no_database")
                    return
                async with factory() as session:
                    async with session.begin():
                        msg = Message(
                            conversation_id=conversation_id,
                            role=role_enum,
                            content=content,
                        )
                        session.add(msg)
                        await session.flush()
                    created = msg.created_at or datetime.now(timezone.utc)
                    cm = CachedMessage(
                        role=msg.role.value,
                        content=msg.content,
                        created_at=_ensure_utc(created),
                    )
                    await self._cache.append(conversation_id, cm)
                    await self._sync_agent_summary_to_cache(session, conversation_id)
                    await self._maybe_schedule_summary(session, conversation_id)
            except Exception:
                logger.exception(
                    "history_background_write_failed",
                    conversation_id=str(conversation_id),
                )

        return asyncio.create_task(_run())
