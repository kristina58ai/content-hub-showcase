"""Identity Manager (Showcase) state — read-only archetype loader (ADR-013)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from content_hub_showcase.agents.shared_types import Fact


class IdentityLoaderState(BaseModel):
    archetype_id: str
    facts: list[Fact] = Field(default_factory=list)
    facts_by_category: dict[str, int] = Field(default_factory=dict)
    exemplars_count: int = 0
