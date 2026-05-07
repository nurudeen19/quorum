"""Conversation history cache strategies."""

from __future__ import annotations

from app.cache.base import (
    CachedMessage,
    ConversationCache,
    ConversationHistorySnapshot,
)
from app.cache.factory import build_conversation_cache

_cache_singleton: ConversationCache | None = None


def set_conversation_cache(cache: ConversationCache | None) -> None:
    """Register global cache (typically at bootstrap)."""
    global _cache_singleton
    _cache_singleton = cache


def get_conversation_cache() -> ConversationCache:
    """Return cache registered at startup."""
    if _cache_singleton is None:
        raise RuntimeError("Conversation cache is not initialized")
    return _cache_singleton


__all__ = [
    "CachedMessage",
    "ConversationCache",
    "ConversationHistorySnapshot",
    "build_conversation_cache",
    "get_conversation_cache",
    "set_conversation_cache",
]
