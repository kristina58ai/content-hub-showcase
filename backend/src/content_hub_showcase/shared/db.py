"""SQLite access helpers (stdlib sqlite3; STRICT schema managed by Alembic)."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    """Canonical timestamp format for showcase.db (ISO-8601 UTC, second precision)."""
    return utc_now().isoformat(timespec="seconds")
