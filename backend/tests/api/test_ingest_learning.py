"""Ingest + plan + learning-cycle endpoints (VS-5, VS-5b)."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from content_hub_showcase.shared.config import Settings
from tests.api.test_archetypes import seed
from tests.conftest import apply_migrations, build_test_client

SESSION = str(uuid.uuid4())
HEADERS = {"X-Session-Id": SESSION}


@pytest.fixture()
def vs5_client(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):  # type: ignore[no-untyped-def]
    apply_migrations(settings.showcase_db_path)
    archetypes_dir = tmp_path / "archetypes"
    seed(settings, archetypes_dir)
    client = build_test_client(
        monkeypatch,
        settings.data_dir,
        ARCHETYPES_DIR=str(archetypes_dir),
        CHECKPOINTER_BACKEND="memory",
    )
    with client:
        yield client


def test_plan_endpoint_returns_preloaded_plan(vs5_client) -> None:  # type: ignore[no-untyped-def]
    response = vs5_client.get("/api/v1/archetypes/test_persona/plan")
    assert response.status_code == 200
    plan = response.json()["data"]
    assert len(plan) == 2
    assert plan[0]["topic"] == "Write more tests"


def test_plan_unknown_archetype_404(vs5_client) -> None:  # type: ignore[no-untyped-def]
    assert vs5_client.get("/api/v1/archetypes/ghost/plan").status_code == 404


def test_ingest_validates_and_stores(vs5_client) -> None:  # type: ignore[no-untyped-def]
    response = vs5_client.post(
        "/api/v1/demo/ingest",
        headers=HEADERS,
        json={
            "archetype": "test_persona",
            "platform": "x",
            "text": "My manually added post about testing things properly.",
            "views": 500,
            "likes": 40,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["session_scoped"] is True
    assert data["embedded"] is True
    assert data["ingested_id"] >= 1


def test_ingest_rejects_short_text(vs5_client) -> None:  # type: ignore[no-untyped-def]
    response = vs5_client.post(
        "/api/v1/demo/ingest",
        headers=HEADERS,
        json={"archetype": "test_persona", "platform": "x", "text": "short"},
    )
    assert response.status_code == 400


def test_ingest_unknown_archetype_404(vs5_client) -> None:  # type: ignore[no-untyped-def]
    response = vs5_client.post(
        "/api/v1/demo/ingest",
        headers=HEADERS,
        json={
            "archetype": "ghost",
            "platform": "x",
            "text": "Long enough text for validation.",
        },
    )
    assert response.status_code == 404


def test_learning_cycle_sees_session_ingested_post(vs5_client) -> None:  # type: ignore[no-untyped-def]
    ingest = vs5_client.post(
        "/api/v1/demo/ingest",
        headers=HEADERS,
        json={
            "archetype": "test_persona",
            "platform": "threads",
            "text": "Session-scoped ingested post that must join the learning cycle.",
            "views": 900,
            "likes": 90,
        },
    )
    assert ingest.status_code == 200

    response = vs5_client.post(
        "/api/v1/archetypes/test_persona/learning-cycle", headers=HEADERS
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["inputs"]["exemplars"] == 2
    assert data["inputs"]["ingested_this_session"] == 1
    assert "patterns" in data
    assert isinstance(data["plan_suggestions"], list)


def test_learning_cycle_other_session_isolated(vs5_client) -> None:  # type: ignore[no-untyped-def]
    other = {"X-Session-Id": str(uuid.uuid4())}
    response = vs5_client.post(
        "/api/v1/archetypes/test_persona/learning-cycle", headers=other
    )
    assert response.status_code == 200
    assert response.json()["data"]["inputs"]["ingested_this_session"] == 0
