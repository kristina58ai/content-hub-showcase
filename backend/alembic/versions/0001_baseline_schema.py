"""Baseline schema: demo_visitors + demo_generated_posts (STRICT, §B.6.2).

Note: SQLite STRICT tables reject the TIMESTAMP column type (allowed types:
INT/INTEGER/REAL/TEXT/BLOB/ANY), so timestamp columns are TEXT holding
ISO-8601 UTC strings — the spec's STRICT intent is preserved.
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE demo_visitors (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id        TEXT UNIQUE NOT NULL,
            archetype_used    TEXT,
            generations_count INTEGER NOT NULL DEFAULT 0,
            ip_address        TEXT,
            user_agent        TEXT,
            started_at        TEXT NOT NULL,
            last_activity     TEXT NOT NULL
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_visitors_session ON demo_visitors(session_id)")
    op.execute("CREATE INDEX idx_visitors_last_activity ON demo_visitors(last_activity)")

    op.execute(
        """
        CREATE TABLE demo_generated_posts (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid              TEXT UNIQUE NOT NULL,
            session_id        TEXT NOT NULL,
            archetype_id      TEXT NOT NULL,
            mode              TEXT NOT NULL,
            neutral_body      TEXT,
            platform_versions TEXT,
            created_at        TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at        TEXT NOT NULL
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_demo_posts_session ON demo_generated_posts(session_id)")
    op.execute("CREATE INDEX idx_demo_posts_expires ON demo_generated_posts(expires_at)")


def downgrade() -> None:
    op.execute("DROP TABLE demo_generated_posts")
    op.execute("DROP TABLE demo_visitors")
