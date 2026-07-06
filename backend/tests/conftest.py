"""Shared test fixtures. No real API keys / network calls anywhere (§B.14.3)."""

from __future__ import annotations

import os

# Must be set before any content_hub_showcase import (main validates at import).
os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")
os.environ.setdefault("LLM_PRIMARY_PROVIDER", "fake")
os.environ.setdefault("EMBEDDING_PROVIDER", "fake")

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from content_hub_showcase.shared.config import Settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path / "data",
        llm_primary_provider="fake",
        embedding_provider="fake",
    )


def apply_migrations(db_path: Path) -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    command.upgrade(cfg, "head")


@pytest.fixture()
def migrated_db(settings: Settings) -> Path:
    apply_migrations(settings.showcase_db_path)
    return settings.showcase_db_path


def build_test_client(
    monkeypatch: pytest.MonkeyPatch, data_dir: Path, **env: str
) -> TestClient:
    from content_hub_showcase.shared import config as config_module

    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("LLM_PRIMARY_PROVIDER", "fake")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "fake")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    config_module.get_settings.cache_clear()

    from content_hub_showcase.api import deps

    deps.reset_dependency_caches()

    from content_hub_showcase.main import create_app

    return TestClient(create_app())


@pytest.fixture()
def client(
    settings: Settings, migrated_db: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[TestClient]:
    from content_hub_showcase.shared import config as config_module

    test_client = build_test_client(monkeypatch, settings.data_dir)
    with test_client:
        yield test_client
    config_module.get_settings.cache_clear()
