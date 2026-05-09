"""Upstash Redis cache: agent summary string + message LIST tail."""

from __future__ import annotations

import json
from uuid import UUID

import structlog
from upstash_redis.asyncio import Redis

from app.cache.base import (
    CachedMessage,
    ConversationCache,
    ConversationHistorySnapshot,
)

logger = structlog.get_logger(__name__)


class UpstashConversationCache(ConversationCache):
    """LIST for messages (RPUSH + LTRIM); STRING for agent summary."""

    def __init__(
        self,
        *,
        url: str,
        token: str,
        max_message_slots: int,
    ) -> None:
        self._redis = Redis(url=url.rstrip("/"), token=token)
        self._capacity = max_message_slots

    def _messages_key(self, conversation_id: UUID) -> str:
        return f"conversation:{conversation_id}:messages"

    def _summary_key(self, conversation_id: UUID) -> str:
        return f"conversation:{conversation_id}:agent_summary"

    async def get(self, conversation_id: UUID) -> ConversationHistorySnapshot:
        mk = self._messages_key(conversation_id)
        sk = self._summary_key(conversation_id)
        raw_result = await self._redis.lrange(mk, -self._capacity, -1)
        summary_raw = await self._redis.get(sk)
        summary: str | None
        if summary_raw is None or summary_raw == "":
            summary = None
        elif isinstance(summary_raw, str):
            summary = summary_raw
        else:
            summary = str(summary_raw)

        if not isinstance(raw_result, list):
            return ConversationHistorySnapshot(agent_summary=summary, messages=[])

        out: list[CachedMessage] = []
        for item in raw_result:
            if not isinstance(item, str):
                continue
            try:
                obj = json.loads(item)
                out.append(CachedMessage.model_validate(obj))
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("cache_deserialize_failed", error=str(exc))
        return ConversationHistorySnapshot(agent_summary=summary, messages=out)

    async def append(self, conversation_id: UUID, message: CachedMessage) -> None:
        mk = self._messages_key(conversation_id)
        encoded = message.model_dump_json()
        await self._redis.rpush(mk, encoded)
        await self._redis.ltrim(mk, -self._capacity, -1)

    async def set_agent_summary(
        self, conversation_id: UUID, summary: str | None
    ) -> None:
        sk = self._summary_key(conversation_id)
        if summary is None or not summary.strip():
            await self._redis.delete(sk)
        else:
            await self._redis.set(sk, summary)

    async def clear(self, conversation_id: UUID) -> None:
        await self._redis.delete(self._messages_key(conversation_id))
        await self._redis.delete(self._summary_key(conversation_id))

    async def verify_connectivity(self) -> None:
        await self._redis.ping()

    async def aclose(self) -> None:
        await self._redis.close()
