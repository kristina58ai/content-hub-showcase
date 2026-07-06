"""Analyzer network state — demo learning cycle (§B.3.6, ADR-016)."""

from __future__ import annotations

import operator
from typing import Annotated

from pydantic import BaseModel, Field

from content_hub_showcase.agents.shared_types import Exemplar, PlanEntry
from content_hub_showcase.content.models import IngestedPost


class AnalyzerState(BaseModel):
    archetype_id: str
    session_id: str = ""

    exemplars: list[Exemplar] = Field(default_factory=list)
    ingested: list[IngestedPost] = Field(default_factory=list)
    rows_text: str = ""

    patterns: str = ""
    validated_patterns: str = ""
    rag_suggestions: str = ""
    plan_suggestions: list[PlanEntry] = Field(default_factory=list)
    provider_events: Annotated[list[str], operator.add] = Field(default_factory=list)
