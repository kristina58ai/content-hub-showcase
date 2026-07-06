"""Cached application dependencies (embedded Chroma, embedder, services)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from content_hub_showcase.content.repositories.generated_posts import (
    GeneratedPostsRepository,
)
from content_hub_showcase.content.repositories.ingested import IngestedRepository
from content_hub_showcase.content.service import GenerationService, IngestService
from content_hub_showcase.learning.service import LearningService
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.personality.service import ArchetypeService
from content_hub_showcase.shared.config import get_settings
from content_hub_showcase.shared.embeddings import EmbeddingProvider, build_embedding_provider
from content_hub_showcase.shared.llm_client import build_llm_client
from content_hub_showcase.shared.vector_db import ChromaClient


@lru_cache
def get_chroma_client() -> ChromaClient:
    return ChromaClient(get_settings().chroma_demo_dir)


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return build_embedding_provider(get_settings())


@lru_cache
def get_personality_repository() -> PersonalityRepository:
    return PersonalityRepository(get_chroma_client(), get_embedding_provider())


@lru_cache
def get_archetype_service() -> ArchetypeService:
    return ArchetypeService(get_settings().archetypes_dir, get_personality_repository())


def _build_checkpointer() -> Any:
    settings = get_settings()
    if settings.checkpointer_backend == "memory":
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver()
    from content_hub_showcase.agents.checkpointer import build_async_checkpointer

    return build_async_checkpointer(settings)


@lru_cache
def get_generation_service() -> GenerationService:
    from content_hub_showcase.agents.graphs.post_generator_graph import (
        build_post_generator_graph,
    )

    settings = get_settings()
    checkpointer = _build_checkpointer()
    graph = build_post_generator_graph(
        get_personality_repository(), build_llm_client(settings), checkpointer
    )
    return GenerationService(
        graph,
        GeneratedPostsRepository(settings.showcase_db_path),
        max_concurrent_per_ip=settings.rate_limit_concurrent_generations,
        checkpointer=checkpointer,
    )


@lru_cache
def get_ingested_repository() -> IngestedRepository:
    return IngestedRepository(get_settings().showcase_db_path)


@lru_cache
def get_ingest_service() -> IngestService:
    return IngestService(
        get_ingested_repository(),
        ChromaClient(get_settings().chroma_session_dir),
        get_embedding_provider(),
    )


@lru_cache
def get_learning_service() -> LearningService:
    from content_hub_showcase.agents.graphs.analyzer_graph import build_analyzer_graph
    from content_hub_showcase.agents.graphs.planner_graph import build_planner_graph

    llm = build_llm_client(get_settings())
    planner = build_planner_graph(get_personality_repository(), llm)
    analyzer = build_analyzer_graph(
        get_personality_repository(), get_ingested_repository(), llm, planner
    )
    return LearningService(analyzer)


def reset_dependency_caches() -> None:
    """Test helper: dependencies are settings-bound, so tests must reset both."""
    get_chroma_client.cache_clear()
    get_embedding_provider.cache_clear()
    get_personality_repository.cache_clear()
    get_archetype_service.cache_clear()
    get_generation_service.cache_clear()
    get_ingested_repository.cache_clear()
    get_ingest_service.cache_clear()
    get_learning_service.cache_clear()
