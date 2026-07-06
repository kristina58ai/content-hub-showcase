"""Session-scoped manual data ingestion (VS-5b, ADR-016).

Timestamps are TEXT ISO-8601 UTC (TIMESTAMP is invalid inside STRICT tables).
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE demo_ingested (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id   TEXT NOT NULL,
            archetype_id TEXT NOT NULL,
            platform     TEXT NOT NULL,
            text         TEXT NOT NULL,
            views        INTEGER NOT NULL DEFAULT 0,
            likes        INTEGER NOT NULL DEFAULT 0,
            comments     INTEGER NOT NULL DEFAULT 0,
            shares       INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at   TEXT NOT NULL
        ) STRICT
        """
    )
    op.execute("CREATE INDEX idx_ingested_session ON demo_ingested(session_id, archetype_id)")
    op.execute("CREATE INDEX idx_ingested_expires ON demo_ingested(expires_at)")


def downgrade() -> None:
    op.execute("DROP TABLE demo_ingested")
