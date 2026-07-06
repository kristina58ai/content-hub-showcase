"""Planner + Analyzer graphs on mock LLM (VS-5)."""

from __future__ import annotations

import json

from content_hub_showcase.agents.graphs.analyzer_graph import build_analyzer_graph
from content_hub_showcase.agents.graphs.planner_graph import build_planner_graph
from content_hub_showcase.agents.nodes.planner.nodes import parse_plan_entries
from content_hub_showcase.agents.shared_types import Exemplar, Fact
from content_hub_showcase.content.models import IngestedPost
from content_hub_showcase.content.repositories.ingested import IngestedRepository
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient, LLMProvider

PLAN_JSON = json.dumps(
    [
        {
            "topic": "Suggested topic one",
            "rationale": "Fits the audience",
            "scheduled_for_offset_days": 1,
            "target_platforms": ["x"],
        },
        {
            "topic": "Suggested topic two",
            "rationale": "Trend",
            "scheduled_for_offset_days": 5,
            "target_platforms": ["linkedin", "telegram"],
        },
        {
            "topic": "Suggested topic three",
            "rationale": "Series",
            "scheduled_for_offset_days": 9,
            "target_platforms": ["medium"],
        },
    ]
)


class StubRepo(PersonalityRepository):
    def __init__(self) -> None:  # noqa: D107 — intentionally skips parent init
        pass

    def facts_for(self, archetype_id: str) -> list[Fact]:
        return [Fact(category="interest", subcategory="s", fact="Enjoys testing")]

    def exemplars_all(self, archetype_id: str) -> list[Exemplar]:
        return [
            Exemplar(platform="x", topic="weak", text="weak post", engagement_score=2.0),
            Exemplar(
                platform="linkedin", topic="strong", text="strong post", engagement_score=9.0
            ),
        ]


class StubIngested(IngestedRepository):
    def __init__(self, posts: list[IngestedPost] | None = None) -> None:  # noqa: D107
        self._posts = posts or []

    def list_for_session(self, session_id: str, archetype_id: str) -> list[IngestedPost]:
        return [p for p in self._posts if p.session_id == session_id]


class RoutedLLM(LLMProvider):
    name = "routed"

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        if "Planner Briefer" in prompt:
            return "Author context summary."
        if "Planner Researcher" in prompt:
            return "- angle A\n- angle B"
        if "Planner Generator" in prompt:
            return PLAN_JSON
        if "Planner Critic" in prompt:
            return PLAN_JSON
        if "Analyst agent" in prompt:
            return "- pattern: stories win"
        if "Analyzer Critic" in prompt:
            return "- validated: stories win"
        if "Editor agent" in prompt:
            return "- remember: lead with stories"
        return "unexpected"


def _llm() -> LLMClient:
    return LLMClient([RoutedLLM()], wait_min=0.001, wait_max=0.002)


async def test_planner_graph_produces_entries() -> None:
    graph = build_planner_graph(StubRepo(), _llm())
    state = await graph.ainvoke({"archetype_id": "test_persona"})
    assert len(state["entries"]) == 3
    assert state["entries"][0].topic == "Suggested topic one"
    events = state["provider_events"]
    assert any(e.startswith("plan_briefer") for e in events)
    assert any(e.startswith("plan_critic") for e in events)


async def test_analyzer_graph_full_cycle_includes_ingested() -> None:
    ingested = StubIngested(
        [
            IngestedPost(
                session_id="s-1",
                archetype_id="test_persona",
                platform="threads",
                text="manually added post",
                views=1000,
                likes=50,
            )
        ]
    )
    planner = build_planner_graph(StubRepo(), _llm())
    graph = build_analyzer_graph(StubRepo(), ingested, _llm(), planner)
    state = await graph.ainvoke({"archetype_id": "test_persona", "session_id": "s-1"})

    assert len(state["exemplars"]) == 2
    assert len(state["ingested"]) == 1
    assert "ingested this session" in state["rows_text"]
    assert state["validated_patterns"].startswith("- validated")
    assert state["rag_suggestions"].startswith("- remember")
    assert len(state["plan_suggestions"]) == 3


async def test_analyzer_without_session_has_no_ingested() -> None:
    planner = build_planner_graph(StubRepo(), _llm())
    graph = build_analyzer_graph(StubRepo(), StubIngested(), _llm(), planner)
    state = await graph.ainvoke({"archetype_id": "test_persona"})
    assert state["ingested"] == []


class TestParsePlanEntries:
    def test_valid(self) -> None:
        assert len(parse_plan_entries(PLAN_JSON)) == 3

    def test_with_noise(self) -> None:
        assert len(parse_plan_entries(f"Sure!\n{PLAN_JSON}\nDone.")) == 3

    def test_invalid_items_dropped(self) -> None:
        raw = '[{"topic": "ok", "target_platforms": ["x"]}, {"nope": 1}, "garbage"]'
        entries = parse_plan_entries(raw)
        assert len(entries) == 1
        assert entries[0].topic == "ok"

    def test_garbage_empty(self) -> None:
        assert parse_plan_entries("no json here") == []
