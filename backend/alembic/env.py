"""Alembic environment — raw-SQL migrations over sqlite (no ORM models)."""

from __future__ import annotations

import os
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine

config = context.config


def _database_url() -> str:
    override = os.environ.get("SHOWCASE_DB_URL", "")
    if override:
        return override
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("sqlalchemy.url is not configured")
    return url


def run_migrations_offline() -> None:
    context.configure(url=_database_url(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _database_url()
    if url.startswith("sqlite:///"):
        db_file = Path(url.removeprefix("sqlite:///"))
        db_file.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
