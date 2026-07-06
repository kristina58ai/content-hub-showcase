"""LangGraph checkpointer factory — ShallowRedisSaver over Redis (ADR-009).

Latest-checkpoint-only storage with native TTL: the LangGraph 1.1 recommended
setup for short-lived recruiter sessions. Dev uses local Docker Redis;
production uses Upstash Free via REDIS_URL.
"""

from __future__ import annotations

from typing import Any

from content_hub_showcase.shared.config import Settings


def thread_id(network: str, session_id: str, timestamp: str) -> str:
    """Per-session thread isolation: {network}_{session_id}_{timestamp} (§B.6.4)."""
    return f"{network}_{session_id}_{timestamp}"


def _ttl_config(settings: Settings) -> dict[str, Any]:
    return {"default_ttl": settings.checkpoint_ttl_hours * 60, "refresh_on_read": True}


def build_checkpointer(settings: Settings) -> Any:
    """Sync shallow Redis checkpointer (sync graph flows / scripts)."""
    from langgraph.checkpoint.redis import ShallowRedisSaver

    saver = ShallowRedisSaver(redis_url=settings.redis_url, ttl=_ttl_config(settings))
    saver.setup()
    return saver


def build_async_checkpointer(settings: Settings) -> Any:
    """Async shallow Redis checkpointer for astream flows.

    The sync ShallowRedisSaver raises NotImplementedError from aget_tuple, so
    async graphs must use this variant. Index setup is async — the caller must
    `await saver.asetup()` once before first use (GenerationService does this
    lazily). Fails loudly if Redis is down (§B.10.1).
    """
    from langgraph.checkpoint.redis.ashallow import AsyncShallowRedisSaver

    return AsyncShallowRedisSaver(redis_url=settings.redis_url, ttl=_ttl_config(settings))
