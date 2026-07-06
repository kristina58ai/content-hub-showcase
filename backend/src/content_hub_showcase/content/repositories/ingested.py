"""demo_ingested repository — session-scoped manual posts (VS-5b), TTL 24h lazy."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from content_hub_showcase.content.models import IngestedPost
from content_hub_showcase.shared.db import connect, utc_now


class IngestedRepository:
    def __init__(self, db_path: Path, ttl_hours: int = 24) -> None:
        self._db_path = db_path
        self._ttl = timedelta(hours=ttl_hours)

    def save(self, post: IngestedPost) -> int:
        now = utc_now()
        with connect(self._db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO demo_ingested
                    (session_id, archetype_id, platform, text,
                     views, likes, comments, shares, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post.session_id,
                    post.archetype_id,
                    post.platform,
                    post.text,
                    post.views,
                    post.likes,
                    post.comments,
                    post.shares,
                    now.isoformat(timespec="seconds"),
                    (now + self._ttl).isoformat(timespec="seconds"),
                ),
            )
        return int(cursor.lastrowid or 0)

    def list_for_session(self, session_id: str, archetype_id: str) -> list[IngestedPost]:
        self.cleanup_expired()
        with connect(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM demo_ingested
                WHERE session_id = ? AND archetype_id = ?
                ORDER BY id
                """,
                (session_id, archetype_id),
            ).fetchall()
        return [
            IngestedPost(
                id=row["id"],
                session_id=row["session_id"],
                archetype_id=row["archetype_id"],
                platform=row["platform"],
                text=row["text"],
                views=row["views"],
                likes=row["likes"],
                comments=row["comments"],
                shares=row["shares"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def cleanup_expired(self) -> int:
        now_iso = utc_now().isoformat(timespec="seconds")
        with connect(self._db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM demo_ingested WHERE expires_at < ?", (now_iso,)
            )
        return int(cursor.rowcount)
