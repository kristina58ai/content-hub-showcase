"""Identity Manager graph: loads facts + exemplar stats through LangGraph."""

from __future__ import annotations

from content_hub_showcase.agents.graphs.identity_manager_graph import (
    build_identity_manager_graph,
)
from content_hub_showcase.agents.shared_types import Fact
from content_hub_showcase.personality.repository import PersonalityRepository


class StubRepository(PersonalityRepository):
    """In-memory stand-in — no Chroma, no embeddings."""

    def __init__(self) -> None:  # noqa: D107 — intentionally skips parent init
        self._facts = [
            Fact(category="interest", subcategory="a", fact="Likes graphs", confidence=0.9),
            Fact(category="interest", subcategory="b", fact="Likes tests", confidence=0.8),
            Fact(category="goal", subcategory="c", fact="Ship the demo", confidence=0.7),
        ]

    def facts_for(self, archetype_id: str) -> list[Fact]:
        return self._facts if archetype_id == "test_persona" else []

    def exemplars_count(self, archetype_id: str) -> int:
        return 2 if archetype_id == "test_persona" else 0


def test_graph_loads_facts_and_counts() -> None:
    graph = build_identity_manager_graph(StubRepository())
    state = graph.invoke({"archetype_id": "test_persona"})
    assert len(state["facts"]) == 3
    assert state["facts_by_category"] == {"interest": 2, "goal": 1}
    assert state["exemplars_count"] == 2


def test_graph_unknown_archetype_is_empty() -> None:
    graph = build_identity_manager_graph(StubRepository())
    state = graph.invoke({"archetype_id": "nobody"})
    assert state["facts"] == []
    assert state["exemplars_count"] == 0
