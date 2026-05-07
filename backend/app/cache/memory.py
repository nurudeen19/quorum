"""In-process rolling conversation cache."""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from typing import Any
from uuid import UUID

from app.cache.base import (
    CachedMessage,
    ConversationCache,
    ConversationHistorySnapshot,
)


class InMemoryConversationCache(ConversationCache):
    """Holds agent summary + deque of messages; deque maxlen enforces turn budget."""

    def __init__(self, max_message_slots: int) -> None:
        self._max_message_slots = max_message_slots
        self._rows: dict[UUID, dict[str, Any]] = defaultdict(self._new_bucket)
        self._lock = asyncio.Lock()

    def _new_bucket(self) -> dict[str, Any]:
        return {
            "agent_summary": None,
            "messages": deque(maxlen=self._max_message_slots),
        }

    async def get(self, conversation_id: UUID) -> ConversationHistorySnapshot:
        async with self._lock:
            bucket = self._rows.get(conversation_id)
            if not bucket:
                return ConversationHistorySnapshot()
            msgs = bucket["messages"]
            return ConversationHistorySnapshot(
                agent_summary=bucket["agent_summary"],
                messages=list(msgs) if msgs else [],
            )

    async def append(self, conversation_id: UUID, message: CachedMessage) -> None:
        async with self._lock:
            self._rows[conversation_id]["messages"].append(message)

    async def set_agent_summary(
        self, conversation_id: UUID, summary: str | None
    ) -> None:
        async with self._lock:
            self._rows[conversation_id]["agent_summary"] = summary

    async def clear(self, conversation_id: UUID) -> None:
        async with self._lock:
            self._rows.pop(conversation_id, None)
