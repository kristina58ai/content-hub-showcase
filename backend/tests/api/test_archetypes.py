"""Archetype endpoints over a seeded tmp Chroma + JSON sources (VS-1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content_hub_showcase.shared.config import Settings
from content_hub_showcase.shared.embeddings import FakeEmbeddingProvider
from content_hub_showcase.shared.vector_db import (
    COLLECTION_EXEMPLARS,
    COLLECTION_PERSONALITY,
    ChromaClient,
)
from tests.conftest import apply_migrations, build_test_client

TEST_ARCHETYPE = {
    "archetype_id": "test_persona",
    "display_name": "Test Persona",
    "emoji": "🧪",
    "tagline": "Testing things",
    "description": "A synthetic archetype for tests.",
    "personality": [
        {"category": "interest", "subcategory": "s", "fact": "Loves pytest", "confidence": 0.9},
        {"category": "goal", "subcategory": "s", "fact": "Reach green CI", "confidence": 0.8},
        {"category": "taboo", "subcategory": "s", "fact": "Never skips tests", "confidence": 1.0},
    ],
    "exemplars": [
        {
            "platform": "x",
            "topic": "testing",
            "text": "Short post about tests",
            "engagement_score": 5.0,
            "views": 100,
            "likes": 10,
            "comments": 1,
            "shares": 2,
        },
        {
            "platform": "linkedin",
            "topic": "quality",
            "text": "Longer professional post about quality",
            "engagement_score": 6.0,
            "views": 200,
            "likes": 20,
            "comments": 2,
            "shares": 3,
        },
    ],
    "plan": [
        {
            "topic": "Write more tests",
            "rationale": "Coverage",
            "scheduled_for_offset_days": 0,
            "target_platforms": ["x"],
        },
        {
            "topic": "Refactor fixtures",
            "rationale": "Maintainability",
            "scheduled_for_offset_days": 3,
            "target_platforms": ["linkedin", "x"],
        },
    ],
}


def seed(settings: Settings, archetypes_dir: Path) -> None:
    archetypes_dir.mkdir(parents=True, exist_ok=True)
    (archetypes_dir / "test_persona.json").write_text(
        json.dumps(TEST_ARCHETYPE), encoding="utf-8"
    )

    provider = FakeEmbeddingProvider()
    chroma = ChromaClient(settings.chroma_demo_dir)
    facts = TEST_ARCHETYPE["personality"]
    chroma.add(
        COLLECTION_PERSONALITY,
        ids=[f"test_persona-fact-{i}" for i in range(len(facts))],
        documents=[f["fact"] for f in facts],
        embeddings=provider.embed_documents([f["fact"] for f in facts]),
        metadatas=[
            {
                "archetype": "test_persona",
                "category": f["category"],
                "subcategory": f["subcategory"],
                "confidence": f["confidence"],
                "embedding_model": provider.model_tag,
            }
            for f in facts
        ],
    )
    exemplars = TEST_ARCHETYPE["exemplars"]
    chroma.add(
        COLLECTION_EXEMPLARS,
        ids=[f"test_persona-ex-{i}" for i in range(len(exemplars))],
        documents=[e["text"] for e in exemplars],
        embeddings=provider.embed_documents([e["text"] for e in exemplars]),
        metadatas=[
            {
                "archetype": "test_persona",
                "platform": e["platform"],
                "topic": e["topic"],
                "engagement_score": e["engagement_score"],
                "views": e["views"],
                "likes": e["likes"],
                "comments": e["comments"],
                "shares": e["shares"],
                "embedding_model": provider.model_tag,
            }
            for e in exemplars
        ],
    )


@pytest.fixture()
def archetype_client(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):  # type: ignore[no-untyped-def]
    apply_migrations(settings.showcase_db_path)
    archetypes_dir = tmp_path / "archetypes"
    seed(settings, archetypes_dir)
    client = build_test_client(
        monkeypatch, settings.data_dir, ARCHETYPES_DIR=str(archetypes_dir)
    )
    with client:
        yield client


def test_list_archetypes(archetype_client) -> None:  # type: ignore[no-untyped-def]
    response = archetype_client.get("/api/v1/archetypes")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["archetype_id"] == "test_persona"
    assert data[0]["display_name"] == "Test Persona"


def test_archetype_detail_returns_facts_and_plan(archetype_client) -> None:  # type: ignore[no-untyped-def]
    response = archetype_client.get("/api/v1/archetypes/test_persona")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data["facts"]) == 3
    assert data["facts_by_category"] == {"interest": 1, "goal": 1, "taboo": 1}
    assert data["exemplars_count"] == 2
    assert len(data["plan"]) == 2
    assert data["plan"][0]["topic"] == "Write more tests"


def test_unknown_archetype_404_envelope(archetype_client) -> None:  # type: ignore[no-untyped-def]
    response = archetype_client.get("/api/v1/archetypes/ghost")
    assert response.status_code == 404
    assert response.json()["error"]["type"] == "not_found"


def test_path_traversal_id_rejected(archetype_client) -> None:  # type: ignore[no-untyped-def]
    response = archetype_client.get("/api/v1/archetypes/..%2Fsecrets")
    assert response.status_code == 404
