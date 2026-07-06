"""Planner network state (ADR-013/ADR-014)."""

from __future__ import annotations

import operator
from typing import Annotated

from pydantic import BaseModel, Field

from content_hub_showcase.agents.shared_types import PlanEntry


class PlannerState(BaseModel):
    archetype_id: str
    context: str = ""
    angles: str = ""
    draft: str = ""
    entries: list[PlanEntry] = Field(default_factory=list)
    provider_events: Annotated[list[str], operator.add] = Field(default_factory=list)
