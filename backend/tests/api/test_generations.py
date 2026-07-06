"""Generations API: create run, SSE stream format, result, status (VS-2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from content_hub_showcase.shared.config import Settings
from tests.api.test_archetypes import seed
from tests.conftest import apply_migrations, build_test_client


@pytest.fixture()
def gen_client(
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


def _parse_frames(text: str) -> list[tuple[str, dict[str, Any]]]:
    frames: list[tuple[str, dict[str, Any]]] = []
    for block in text.strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) >= 2 and lines[0].startswith("event: "):
            frames.append(
                (
                    lines[0].removeprefix("event: "),
                    json.loads(lines[1].removeprefix("data: ")),
                )
            )
    return frames


def test_create_generation_returns_run_and_stream_url(gen_client) -> None:  # type: ignore[no-untyped-def]
    response = gen_client.post(
        "/api/v1/generations",
        json={"archetype_id": "test_persona", "topic": "why testing matters"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["run_id"]
    assert data["stream_url"].endswith(f"/generations/{data['run_id']}/stream")


def test_unknown_archetype_404(gen_client) -> None:  # type: ignore[no-untyped-def]
    response = gen_client.post(
        "/api/v1/generations", json={"archetype_id": "ghost", "topic": "anything here"}
    )
    assert response.status_code == 404


def test_short_topic_validation_400(gen_client) -> None:  # type: ignore[no-untyped-def]
    response = gen_client.post(
        "/api/v1/generations", json={"archetype_id": "test_persona", "topic": "ab"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["type"] == "validation_error"


def test_stream_emits_spec_events_and_result_persists(gen_client) -> None:  # type: ignore[no-untyped-def]
    created = gen_client.post(
        "/api/v1/generations",
        json={
            "archetype_id": "test_persona",
            "topic": "streaming test topic",
            "platforms": ["x", "linkedin"],
        },
    ).json()["data"]
    run_id = created["run_id"]

    with gen_client.stream("GET", f"/api/v1/generations/{run_id}/stream") as stream:
        body = "".join(chunk for chunk in stream.iter_text())
    frames = _parse_frames(body)
    names = [name for name, _ in frames]

    assert "agent_started" in names
    assert "agent_completed" in names
    assert "graph_transition" in names
    assert names[-1] == "generation_complete"
    started_agents = {d["agent"] for n, d in frames if n == "agent_started"}
    assert {
        "briefer",
        "researcher",
        "writer",
        "social_writer",
        "finalizer",
    } <= started_agents

    complete = frames[-1][1]
    assert complete["run_id"] == run_id
    assert set(complete["result"]["platform_versions"]) == {"x", "linkedin"}

    result = gen_client.get(f"/api/v1/generations/{run_id}/result")
    assert result.status_code == 200
    record = result.json()["data"]
    assert record["archetype_id"] == "test_persona"
    assert set(record["platform_versions"]) == {"x", "linkedin"}

    status = gen_client.get(f"/api/v1/generations/{run_id}/status")
    assert status.json()["data"]["status"] == "complete"


def test_stream_unknown_run_404(gen_client) -> None:  # type: ignore[no-untyped-def]
    response = gen_client.get("/api/v1/generations/nope/stream")
    assert response.status_code == 404


def test_result_unknown_run_404(gen_client) -> None:  # type: ignore[no-untyped-def]
    response = gen_client.get("/api/v1/generations/nope/result")
    assert response.status_code == 404
