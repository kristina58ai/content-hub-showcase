"""Content domain models (showcase.db records)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from content_hub_showcase.agents.shared_types import Platform


class IngestedPost(BaseModel):
    """Row of demo_ingested — manually ingested post + metrics (VS-5b, ADR-016)."""

    id: int | None = None
    session_id: str
    archetype_id: str
    platform: Platform
    text: str
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    created_at: str = ""


class GeneratedPostRecord(BaseModel):
    """Row of demo_generated_posts (TTL 24h, session-scoped)."""

    uuid: str
    session_id: str
    archetype_id: str
    mode: str
    neutral_body: str | None = None
    platform_versions: dict[str, Any] | None = None
    created_at: str
    expires_at: str
