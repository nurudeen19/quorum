"""Redis (TCP): agent summary STRING + message LIST tail."""

from __future__ import annotations

import json
from uuid import UUID

import redis.asyncio as aioredis
import structlog

from app.cache.base import (
    CachedMessage,
    ConversationCache,
    ConversationHistorySnapshot,
)

logger = structlog.get_logger(__name__)


class RedisConversationCache(ConversationCache):
    """LIST for messages; STRING key for agent summary."""

    def __init__(self, redis_url: str, max_message_slots: int) -> None:
        self._redis_url = redis_url
        self._capacity = max_message_slots
        self._client: aioredis.Redis | None = None

    async def _conn(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                self._redis_url,
                decode_responses=True,
            )
        return self._client

    def _messages_key(self, conversation_id: UUID) -> str:
        return f"conversation:{conversation_id}:messages"

    def _summary_key(self, conversation_id: UUID) -> str:
        return f"conversation:{conversation_id}:agent_summary"

    async def get(self, conversation_id: UUID) -> ConversationHistorySnapshot:
        r = await self._conn()
        mk = self._messages_key(conversation_id)
        sk = self._summary_key(conversation_id)
        raw_result = await r.lrange(mk, -self._capacity, -1)
        summary_raw = await r.get(sk)
        summary: str | None
        if summary_raw is None or summary_raw == "":
            summary = None
        else:
            summary = str(summary_raw)

        if not raw_result:
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
        r = await self._conn()
        mk = self._messages_key(conversation_id)
        encoded = message.model_dump_json()
        await r.rpush(mk, encoded)
        await r.ltrim(mk, -self._capacity, -1)

    async def set_agent_summary(
        self, conversation_id: UUID, summary: str | None
    ) -> None:
        r = await self._conn()
        sk = self._summary_key(conversation_id)
        if summary is None or not str(summary).strip():
            await r.delete(sk)
        else:
            await r.set(sk, summary)

    async def clear(self, conversation_id: UUID) -> None:
        r = await self._conn()
        await r.delete(self._messages_key(conversation_id))
        await r.delete(self._summary_key(conversation_id))

    async def verify_connectivity(self) -> None:
        r = await self._conn()
        await r.ping()

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
