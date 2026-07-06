"""Settings + mandatory security flag validation (ADR-009)."""

from __future__ import annotations

from pathlib import Path

import pytest

from content_hub_showcase.shared.config import Settings, validate_strict_msgpack


class TestValidateStrictMsgpack:
    def test_passes_when_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANGGRAPH_STRICT_MSGPACK", "true")
        validate_strict_msgpack()

    def test_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANGGRAPH_STRICT_MSGPACK", "True")
        validate_strict_msgpack()

    def test_fails_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LANGGRAPH_STRICT_MSGPACK", raising=False)
        with pytest.raises(RuntimeError, match="LANGGRAPH_STRICT_MSGPACK"):
            validate_strict_msgpack()

    def test_fails_when_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LANGGRAPH_STRICT_MSGPACK", "false")
        with pytest.raises(RuntimeError, match="mandatory"):
            validate_strict_msgpack()


class TestSettings:
    def test_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # conftest exports fake-mode env for the suite; defaults are tested clean.
        monkeypatch.delenv("LLM_PRIMARY_PROVIDER", raising=False)
        monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
        settings = Settings(_env_file=None)
        assert settings.llm_primary_provider == "groq"
        assert settings.local_embed_model == "Qwen/Qwen3-Embedding-0.6B"
        assert settings.checkpoint_ttl_hours == 24
        assert settings.rate_limit_generations_per_hour == 5
        assert settings.rate_limit_reads_per_hour == 100
        assert settings.rate_limit_archetype_switches_per_hour == 20

    def test_derived_paths(self, tmp_path: Path) -> None:
        settings = Settings(_env_file=None, data_dir=tmp_path)
        assert settings.showcase_db_path == tmp_path / "showcase.db"
        assert settings.chroma_demo_dir == tmp_path / "chroma_demo"
        assert settings.chroma_session_dir == tmp_path / "chroma_session"
