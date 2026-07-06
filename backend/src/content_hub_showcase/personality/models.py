"""Personality domain models (demo archetypes, §B.6.1)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from content_hub_showcase.agents.shared_types import Fact, PlanEntry


class ArchetypeSummary(BaseModel):
    archetype_id: str
    display_name: str
    emoji: str = ""
    tagline: str = ""
    description: str = ""


class ArchetypeDetail(ArchetypeSummary):
    facts: list[Fact] = Field(default_factory=list)
    facts_by_category: dict[str, int] = Field(default_factory=dict)
    exemplars_count: int = 0
    plan: list[PlanEntry] = Field(default_factory=list)
