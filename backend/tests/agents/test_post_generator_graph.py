"""PostGenerator graph: full mock-LLM flow, parallel fan-out, JSON parsing."""

from __future__ import annotations

import json

from content_hub_showcase.agents.graphs.post_generator_graph import (
    build_post_generator_graph,
)
from content_hub_showcase.agents.nodes.post_generator.social_writer import (
    parse_post_version,
)
from content_hub_showcase.agents.shared_types import Exemplar, Fact
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient, LLMProvider


class StubRepository(PersonalityRepository):
    def __init__(self) -> None:  # noqa: D107 — intentionally skips parent init
        pass

    def search_facts(self, archetype_id: str, query: str, k: int = 8) -> list[Fact]:
        return [Fact(category="interest", subcategory="s", fact="Loves testing")]

    def exemplars_for(
        self,
        archetype_id: str,
        query: str,
        k: int = 3,
        platform: str | None = None,
    ) -> list[Exemplar]:
        return [
            Exemplar(
                platform=platform or "x",
                topic="testing",
                text="Past great post",
                engagement_score=7.0,
            )
        ]


class RoutedFakeLLM(LLMProvider):
    """Returns node-appropriate canned output keyed off the prompt text."""

    name = "routed-fake"

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        if "Briefer agent" in prompt:
            return "BRIEF: take the failure-story angle."
        if "Researcher agent" in prompt:
            return "- point one\n- point two\n- point three"
        # "Social Writer agent" contains "Writer agent" — check the specific one first.
        if "Social Writer agent" not in prompt and "Writer agent" in prompt:
            return "NEUTRAL BODY about the topic, written in the author's voice."
        if "Social Writer agent" in prompt:
            return json.dumps(
                {
                    "adapted_body": "Adapted body!",
                    "platform_title": None,
                    "hashtags": ["#demo"],
                    "mentions": [],
                    "category": "testing",
                }
            )
        return "unexpected prompt"


async def test_full_flow_two_platforms() -> None:
    graph = build_post_generator_graph(
        StubRepository(), LLMClient([RoutedFakeLLM()])
    )
    state = await graph.ainvoke(
        {
            "archetype_id": "test_persona",
            "topic": "why tests matter",
            "platforms": ["x", "linkedin"],
        }
    )
    assert state["brief"].startswith("BRIEF")
    assert "point one" in state["research_notes"]
    assert state["neutral_body"].startswith("NEUTRAL BODY")
    versions = state["platform_versions"]
    assert set(versions) == {"x", "linkedin"}
    for version in versions.values():
        assert version.adapted_body == "Adapted body!"
        assert version.hashtags == ["#demo"]
    events = state["provider_events"]
    assert any(e.startswith("briefer:") for e in events)
    assert any(e.startswith("social_writer[x]") for e in events)
    assert any(e.startswith("social_writer[linkedin]") for e in events)
    assert "finalizer:ok" in events


async def test_default_platforms_all_five() -> None:
    graph = build_post_generator_graph(StubRepository(), LLMClient([RoutedFakeLLM()]))
    state = await graph.ainvoke(
        {"archetype_id": "test_persona", "topic": "five platforms"}
    )
    assert set(state["platform_versions"]) == {
        "telegram",
        "x",
        "linkedin",
        "medium",
        "threads",
    }


class TestParsePostVersion:
    def test_valid_json(self) -> None:
        raw = (
            '{"adapted_body": "Hi", "platform_title": "T", "hashtags": ["#a"], '
            '"mentions": [], "category": "c"}'
        )
        version = parse_post_version(raw, "medium")
        assert version.adapted_body == "Hi"
        assert version.platform_title == "T"

    def test_json_with_surrounding_noise(self) -> None:
        raw = 'Sure! Here it is:\n{"adapted_body": "Clean", "hashtags": []}\nHope it helps.'
        version = parse_post_version(raw, "x")
        assert version.adapted_body == "Clean"

    def test_garbage_falls_back_to_raw_truncated(self) -> None:
        raw = "not json at all " * 50
        version = parse_post_version(raw, "x")
        assert version.adapted_body == raw.strip()[:280]
        assert version.hashtags == []
