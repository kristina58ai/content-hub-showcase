"""Shared literals + Pydantic models used across the 4 agent networks (ADR-013/ADR-014)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Platform = Literal["telegram", "x", "linkedin", "medium", "threads"]
PLATFORMS: tuple[Platform, ...] = ("telegram", "x", "linkedin", "medium", "threads")

ArchetypeId = Literal["ai_engineer", "marketer", "doctor"]
ARCHETYPE_IDS: tuple[ArchetypeId, ...] = ("ai_engineer", "marketer", "doctor")

GenerationMode = Literal["from_idea", "from_plan"]

NetworkName = Literal["planner", "post_generator", "analyzer", "identity_manager"]
NETWORKS: tuple[NetworkName, ...] = (
    "planner",
    "post_generator",
    "analyzer",
    "identity_manager",
)


class Fact(BaseModel):
    """One personality fact stored in the Personality Chroma collection."""

    category: str = Field(description="interest/goal/character/project/taboo/style_marker")
    subcategory: str = ""
    fact: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class Exemplar(BaseModel):
    """Successful post used as a few-shot example (Exemplars collection)."""

    platform: Platform
    topic: str
    text: str
    engagement_score: float = 0.0
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0


class PlanEntry(BaseModel):
    """Pre-loaded content-plan entry for a demo archetype."""

    topic: str
    rationale: str = ""
    scheduled_for_offset_days: int = 0
    target_platforms: list[Platform] = Field(default_factory=list)


class PostVersion(BaseModel):
    """Per-platform adaptation of a generated post."""

    platform: Platform
    adapted_body: str
    platform_title: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    category: str | None = None
