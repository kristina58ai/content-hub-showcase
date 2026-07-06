"""PostGenerator state: Pydantic schema with reducers for parallel fan-out (ADR-013)."""

from __future__ import annotations

import operator
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from content_hub_showcase.agents.shared_types import (
    PLATFORMS,
    Exemplar,
    Fact,
    GenerationMode,
    Platform,
    PostVersion,
)


def merge_versions(
    left: dict[str, PostVersion], right: dict[str, PostVersion]
) -> dict[str, PostVersion]:
    """Reducer: parallel social_writer branches each contribute one platform."""
    return {**left, **right}


class PostGeneratorState(BaseModel):
    # --- inputs ---
    archetype_id: str
    topic: str
    mode: GenerationMode = "from_idea"
    platforms: list[Platform] = Field(default_factory=lambda: list(PLATFORMS))
    research_depth: Literal["low", "medium", "deep"] = "low"
    # Set per-branch by the Send fan-out; None outside social_writer branches.
    platform: Platform | None = None

    # --- accumulated by nodes ---
    brief: str = ""
    facts: Annotated[list[Fact], operator.add] = Field(default_factory=list)
    exemplars: Annotated[list[Exemplar], operator.add] = Field(default_factory=list)
    research_notes: str = ""
    neutral_body: str = ""
    platform_versions: Annotated[dict[str, PostVersion], merge_versions] = Field(
        default_factory=dict
    )
    provider_events: Annotated[list[str], operator.add] = Field(default_factory=list)
