"""Build cache implementation from settings."""

from __future__ import annotations

from app.cache.base import ConversationCache
from app.cache.memory import InMemoryConversationCache
from app.cache.redis_backend import RedisConversationCache
from app.cache.upstash import UpstashConversationCache
from app.config.cache import CacheSettings


def build_conversation_cache(settings: CacheSettings) -> ConversationCache:
    """Instantiate cache backend from configuration."""
    backend = settings.cache_backend
    turns = settings.cache_max_turns
    max_message_slots = turns * 2

    if backend == "memory":
        return InMemoryConversationCache(max_message_slots)

    if backend == "upstash":
        if not settings.upstash_redis_url or not settings.upstash_redis_token:
            raise ValueError(
                "UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN are required when "
                "CACHE_BACKEND is upstash"
            )
        return UpstashConversationCache(
            url=settings.upstash_redis_url,
            token=settings.upstash_redis_token,
            max_message_slots=max_message_slots,
        )

    if backend == "redis":
        if not settings.redis_url or not settings.redis_url.strip():
            raise ValueError("REDIS_URL is required when CACHE_BACKEND is redis")
        return RedisConversationCache(settings.redis_url, max_message_slots)

    raise ValueError(f"Unknown cache backend: {backend}")
