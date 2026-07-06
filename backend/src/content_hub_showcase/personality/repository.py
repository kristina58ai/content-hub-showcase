"""Personality repository — RAG access to the precomputed demo Chroma (ADR-011)."""

from __future__ import annotations

from typing import Any

from content_hub_showcase.agents.shared_types import Exemplar, Fact
from content_hub_showcase.shared.embeddings import EmbeddingProvider
from content_hub_showcase.shared.vector_db import (
    COLLECTION_EXEMPLARS,
    COLLECTION_PERSONALITY,
    ChromaClient,
    VectorHit,
)


def _fact_from_hit(hit: VectorHit) -> Fact:
    return Fact(
        category=str(hit.metadata.get("category", "")),
        subcategory=str(hit.metadata.get("subcategory", "")),
        fact=hit.document,
        confidence=float(hit.metadata.get("confidence", 0.8)),
    )


def _exemplar_from_hit(hit: VectorHit) -> Exemplar:
    return Exemplar(
        platform=hit.metadata.get("platform", "x"),
        topic=str(hit.metadata.get("topic", "")),
        text=hit.document,
        engagement_score=float(hit.metadata.get("engagement_score", 0.0)),
        views=int(hit.metadata.get("views", 0)),
        likes=int(hit.metadata.get("likes", 0)),
        comments=int(hit.metadata.get("comments", 0)),
        shares=int(hit.metadata.get("shares", 0)),
    )


class PersonalityRepository:
    """Archetype-scoped reads over Personality/Exemplars collections."""

    def __init__(self, chroma: ChromaClient, embedder: EmbeddingProvider) -> None:
        self._chroma = chroma
        self._embedder = embedder

    def facts_for(self, archetype_id: str) -> list[Fact]:
        hits = self._chroma.get_all(
            COLLECTION_PERSONALITY, where={"archetype": archetype_id}
        )
        return [_fact_from_hit(hit) for hit in hits]

    def search_facts(self, archetype_id: str, query: str, k: int = 8) -> list[Fact]:
        embedding = self._embedder.embed_query(query)
        hits = self._chroma.query(
            COLLECTION_PERSONALITY,
            embedding=embedding,
            n_results=k,
            where={"archetype": archetype_id},
        )
        return [_fact_from_hit(hit) for hit in hits]

    def exemplars_for(
        self,
        archetype_id: str,
        query: str,
        k: int = 3,
        platform: str | None = None,
    ) -> list[Exemplar]:
        where: dict[str, Any] = {"archetype": archetype_id}
        if platform:
            where = {"$and": [{"archetype": archetype_id}, {"platform": platform}]}
        embedding = self._embedder.embed_query(query)
        hits = self._chroma.query(
            COLLECTION_EXEMPLARS, embedding=embedding, n_results=k, where=where
        )
        return [_exemplar_from_hit(hit) for hit in hits]

    def exemplars_all(self, archetype_id: str) -> list[Exemplar]:
        hits = self._chroma.get_all(
            COLLECTION_EXEMPLARS, where={"archetype": archetype_id}
        )
        return [_exemplar_from_hit(hit) for hit in hits]

    def exemplars_count(self, archetype_id: str) -> int:
        return len(
            self._chroma.get_all(COLLECTION_EXEMPLARS, where={"archetype": archetype_id})
        )
