"""Abstract conversation cache and cached message shape."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CachedMessage(BaseModel):
    """Single message in the rolling tail."""

    role: str = Field(description="user | assistant | system")
    content: str
    created_at: datetime


class ConversationHistorySnapshot(BaseModel):
    """Agent-facing bundle: optional long-context summary plus recent turns.

    The summary is not intended for end-user display; it supplements the tail for agents.
    """

    agent_summary: str | None = None
    messages: list[CachedMessage] = Field(default_factory=list)


class ConversationCache(ABC):
    """Cache: ``append`` enforces max turn window; ``get`` only reads."""

    @abstractmethod
    async def get(self, conversation_id: UUID) -> ConversationHistorySnapshot:
        """Return cached agent summary (if any) and message tail. No trimming logic."""

    @abstractmethod
    async def append(self, conversation_id: UUID, message: CachedMessage) -> None:
        """Append one message and enforce max size (turn limit × 2 message slots)."""

    @abstractmethod
    async def set_agent_summary(
        self, conversation_id: UUID, summary: str | None
    ) -> None:
        """Store optional rolling summary for agent context (persisted copy lives in DB)."""

    @abstractmethod
    async def clear(self, conversation_id: UUID) -> None:
        """Remove cached summary and messages for a conversation."""

    async def aclose(self) -> None:
        """Optional cleanup (e.g. HTTP client). Default: no-op."""
        return
