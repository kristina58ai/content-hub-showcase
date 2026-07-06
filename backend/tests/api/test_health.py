"""Health/version endpoints + response envelope (§B.7.2)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == {"status": "ok"}
    assert payload["meta"]["request_id"].startswith("req-")
    assert "timestamp" in payload["meta"]


def test_version_returns_version(client: TestClient) -> None:
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json()["data"]["version"]


def test_unknown_route_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/nope")
    assert response.status_code == 404
