"""Middleware stack: rate limits (§B.7.6), anti-abuse (§B.9.1), session tracking."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest

from content_hub_showcase.shared.config import Settings
from tests.conftest import apply_migrations, build_test_client


def test_read_rate_limit_envelope(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    apply_migrations(settings.showcase_db_path)
    client = build_test_client(
        monkeypatch, settings.data_dir, RATE_LIMIT_READS_PER_HOUR="1"
    )
    with client:
        assert client.get("/api/v1/does-not-exist").status_code == 404
        response = client.get("/api/v1/does-not-exist")
        assert response.status_code == 429
        body = response.json()
        assert body["error"]["type"] == "rate_limit_exceeded"
        assert body["error"]["details"]["limit_type"] == "reads_per_hour"
        assert int(response.headers["Retry-After"]) >= 1


def test_health_is_never_rate_limited(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    apply_migrations(settings.showcase_db_path)
    client = build_test_client(
        monkeypatch, settings.data_dir, RATE_LIMIT_READS_PER_HOUR="1"
    )
    with client:
        for _ in range(5):
            assert client.get("/api/v1/health").status_code == 200


def test_blocked_user_agent_gets_403(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, migrated_db: Path
) -> None:
    client = build_test_client(monkeypatch, settings.data_dir)
    with client:
        response = client.get(
            "/api/v1/version", headers={"User-Agent": "python-requests/2.32"}
        )
        assert response.status_code == 403
        assert response.json()["error"]["type"] == "forbidden"


def test_oversized_body_rejected(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, migrated_db: Path
) -> None:
    client = build_test_client(monkeypatch, settings.data_dir)
    with client:
        response = client.post(
            "/api/v1/anything",
            content=b"x",
            headers={"Content-Length": str(64 * 1024)},
        )
        assert response.status_code == 400
        assert response.json()["error"]["type"] == "validation_error"


def test_session_tracked_in_demo_visitors(
    settings: Settings, monkeypatch: pytest.MonkeyPatch, migrated_db: Path
) -> None:
    session_id = str(uuid.uuid4())
    client = build_test_client(monkeypatch, settings.data_dir)
    with client:
        # /version is untracked; a 404 route still passes through session middleware.
        client.get("/api/v1/whatever", headers={"X-Session-Id": session_id})
    conn = sqlite3.connect(migrated_db)
    try:
        row = conn.execute(
            "SELECT session_id, ip_address, started_at FROM demo_visitors WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] == session_id
    # Raw IP is never stored — only a 16-char hash (§B.11.1).
    assert len(row[1]) == 16
    assert "T" in row[2]  # ISO-8601
