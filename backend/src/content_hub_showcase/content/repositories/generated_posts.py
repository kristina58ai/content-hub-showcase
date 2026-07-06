"""demo_generated_posts repository — TTL 24h with lazy cleanup on read (§B.6.5)."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from content_hub_showcase.content.models import GeneratedPostRecord
from content_hub_showcase.shared.db import connect, utc_now


class GeneratedPostsRepository:
    def __init__(self, db_path: Path, ttl_hours: int = 24) -> None:
        self._db_path = db_path
        self._ttl = timedelta(hours=ttl_hours)

    def save(
        self,
        *,
        post_uuid: str,
        session_id: str,
        archetype_id: str,
        mode: str,
        neutral_body: str | None = None,
        platform_versions: dict[str, Any] | None = None,
    ) -> None:
        now = utc_now()
        expires = now + self._ttl
        with connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO demo_generated_posts
                    (uuid, session_id, archetype_id, mode, neutral_body,
                     platform_versions, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(uuid) DO UPDATE SET
                    neutral_body = excluded.neutral_body,
                    platform_versions = excluded.platform_versions,
                    expires_at = excluded.expires_at
                """,
                (
                    post_uuid,
                    session_id,
                    archetype_id,
                    mode,
                    neutral_body,
                    json.dumps(platform_versions, ensure_ascii=False)
                    if platform_versions is not None
                    else None,
                    now.isoformat(timespec="seconds"),
                    expires.isoformat(timespec="seconds"),
                ),
            )

    def get(self, post_uuid: str) -> GeneratedPostRecord | None:
        self.cleanup_expired()
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM demo_generated_posts WHERE uuid = ?", (post_uuid,)
            ).fetchone()
        if row is None:
            return None
        return GeneratedPostRecord(
            uuid=row["uuid"],
            session_id=row["session_id"],
            archetype_id=row["archetype_id"],
            mode=row["mode"],
            neutral_body=row["neutral_body"],
            platform_versions=json.loads(row["platform_versions"])
            if row["platform_versions"]
            else None,
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )

    def cleanup_expired(self) -> int:
        """Lazy TTL cleanup, invoked on every read (§B.6.5)."""
        now_iso = utc_now().isoformat(timespec="seconds")
        with connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM demo_generated_posts WHERE expires_at < ?", (now_iso,)
            )
        return int(cursor.rowcount)
