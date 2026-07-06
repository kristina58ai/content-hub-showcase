"""Application settings loaded from environment / .env (Pydantic Settings)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- LLM (generation only; embeddings are local per ADR-017) ---
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    llm_primary_provider: Literal["groq", "openrouter", "fake"] = "groq"
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    # --- Embeddings (ADR-017) ---
    local_embed_model: str = "Qwen/Qwen3-Embedding-0.6B"
    embedding_provider: Literal["local", "fake"] = "local"

    # --- LangGraph checkpointer (ADR-009) ---
    redis_url: str = "redis://localhost:6379"
    checkpoint_ttl_hours: int = 24
    # redis = production (fails loudly if Redis is down, §B.10.1); memory = tests only.
    checkpointer_backend: Literal["redis", "memory"] = "redis"

    # Mirrored into os.environ so LangGraph sees it even when set via .env only.
    langgraph_strict_msgpack: str = ""

    # --- App ---
    log_level: str = "INFO"
    cors_allowed_origins: list[str] = ["http://localhost:3000"]
    data_dir: Path = Path("data")
    archetypes_dir: Path = Path("data/demo_archetypes")
    app_version: str = "0.1.0"

    # --- Rate limits (§B.7.6) ---
    rate_limit_generations_per_hour: int = 5
    rate_limit_reads_per_hour: int = 100
    rate_limit_archetype_switches_per_hour: int = 20
    rate_limit_concurrent_generations: int = 3

    @property
    def showcase_db_path(self) -> Path:
        return self.data_dir / "showcase.db"

    @property
    def chroma_demo_dir(self) -> Path:
        # Spec names the artifact chroma_demo.sqlite3; Chroma's PersistentClient
        # persists a directory (containing chroma.sqlite3 + index segments).
        return self.data_dir / "chroma_demo"

    @property
    def chroma_session_dir(self) -> Path:
        # Session-scoped ingest data (VS-5b) — separate store so pre-loaded
        # demo data is never polluted (ADR-016).
        return self.data_dir / "chroma_session"


def validate_strict_msgpack() -> None:
    """ADR-009: refuse to start unless LANGGRAPH_STRICT_MSGPACK=true (anti-RCE)."""
    value = os.environ.get("LANGGRAPH_STRICT_MSGPACK", "")
    if value.strip().lower() != "true":
        raise RuntimeError(
            "LANGGRAPH_STRICT_MSGPACK=true is mandatory (ADR-009). "
            "Set it in the environment before starting the app."
        )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.langgraph_strict_msgpack and "LANGGRAPH_STRICT_MSGPACK" not in os.environ:
        os.environ["LANGGRAPH_STRICT_MSGPACK"] = settings.langgraph_strict_msgpack
    return settings
