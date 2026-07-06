"""Archetype service — JSON sources for display data, Identity Manager graph for RAG."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from content_hub_showcase.agents.graphs.identity_manager_graph import (
    build_identity_manager_graph,
)
from content_hub_showcase.agents.shared_types import PlanEntry
from content_hub_showcase.personality.models import ArchetypeDetail, ArchetypeSummary
from content_hub_showcase.personality.repository import PersonalityRepository


class ArchetypeService:
    def __init__(self, archetypes_dir: Path, repository: PersonalityRepository) -> None:
        self._archetypes_dir = archetypes_dir
        self._graph = build_identity_manager_graph(repository)

    def _load_source(self, archetype_id: str) -> dict[str, Any] | None:
        # IDs come from the URL path — never treat them as file paths.
        if not archetype_id.replace("_", "").isalnum():
            return None
        source = self._archetypes_dir / f"{archetype_id}.json"
        if not source.is_file():
            return None
        with source.open(encoding="utf-8") as fh:
            data: dict[str, Any] = json.load(fh)
        return data

    def _summary(self, data: dict[str, Any]) -> ArchetypeSummary:
        return ArchetypeSummary(
            archetype_id=data["archetype_id"],
            display_name=data.get("display_name", data["archetype_id"]),
            emoji=data.get("emoji", ""),
            tagline=data.get("tagline", ""),
            description=data.get("description", ""),
        )

    def has(self, archetype_id: str) -> bool:
        return self._load_source(archetype_id) is not None

    def plan(self, archetype_id: str) -> list[PlanEntry] | None:
        source = self._load_source(archetype_id)
        if source is None:
            return None
        return [PlanEntry(**entry) for entry in source.get("plan", [])]

    def list_archetypes(self) -> list[ArchetypeSummary]:
        summaries: list[ArchetypeSummary] = []
        for json_file in sorted(self._archetypes_dir.glob("*.json")):
            with json_file.open(encoding="utf-8") as fh:
                summaries.append(self._summary(json.load(fh)))
        return summaries

    def get_detail(self, archetype_id: str) -> ArchetypeDetail | None:
        source = self._load_source(archetype_id)
        if source is None:
            return None
        # Identity Manager network in Showcase = read-only archetype loader (§B.3.1).
        state = self._graph.invoke({"archetype_id": archetype_id})
        return ArchetypeDetail(
            **self._summary(source).model_dump(),
            facts=state["facts"],
            facts_by_category=state["facts_by_category"],
            exemplars_count=state["exemplars_count"],
            plan=[PlanEntry(**entry) for entry in source.get("plan", [])],
        )
