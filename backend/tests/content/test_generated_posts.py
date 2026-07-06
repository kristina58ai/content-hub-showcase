"""demo_generated_posts repository: roundtrip + lazy TTL cleanup (§B.6.5)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from content_hub_showcase.content.repositories.generated_posts import (
    GeneratedPostsRepository,
)


def test_save_and_get_roundtrip(migrated_db: Path) -> None:
    repo = GeneratedPostsRepository(migrated_db)
    repo.save(
        post_uuid="u-1",
        session_id="s-1",
        archetype_id="ai_engineer",
        mode="from_idea",
        neutral_body="Neutral text",
        platform_versions={"linkedin": {"adapted_body": "LI text", "hashtags": ["#ai"]}},
    )
    record = repo.get("u-1")
    assert record is not None
    assert record.session_id == "s-1"
    assert record.neutral_body == "Neutral text"
    assert record.platform_versions is not None
    assert record.platform_versions["linkedin"]["hashtags"] == ["#ai"]
    assert record.created_at <= record.expires_at


def test_get_missing_returns_none(migrated_db: Path) -> None:
    assert GeneratedPostsRepository(migrated_db).get("nope") is None


def test_save_upserts_on_uuid_conflict(migrated_db: Path) -> None:
    repo = GeneratedPostsRepository(migrated_db)
    repo.save(post_uuid="u-2", session_id="s", archetype_id="doctor", mode="from_idea")
    repo.save(
        post_uuid="u-2",
        session_id="s",
        archetype_id="doctor",
        mode="from_idea",
        neutral_body="updated",
    )
    record = repo.get("u-2")
    assert record is not None
    assert record.neutral_body == "updated"


def test_expired_posts_cleaned_lazily_on_read(migrated_db: Path) -> None:
    repo = GeneratedPostsRepository(migrated_db)
    repo.save(post_uuid="u-3", session_id="s", archetype_id="marketer", mode="from_plan")

    conn = sqlite3.connect(migrated_db)
    try:
        conn.execute(
            "UPDATE demo_generated_posts SET expires_at = '2000-01-01T00:00:00+00:00' "
            "WHERE uuid = 'u-3'"
        )
        conn.commit()
    finally:
        conn.close()

    assert repo.get("u-3") is None  # lazy cleanup removed it

    conn = sqlite3.connect(migrated_db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM demo_generated_posts WHERE uuid = 'u-3'"
        ).fetchone()[0]
    finally:
        conn.close()
    assert count == 0
