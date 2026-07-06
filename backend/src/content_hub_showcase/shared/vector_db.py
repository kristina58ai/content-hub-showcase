"""Chroma embedded client wrapper (ADR-002/ADR-011; 1024-dim collections per ADR-017)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

COLLECTION_PERSONALITY = "Personality_qwen06b_v1"
COLLECTION_EXEMPLARS = "Exemplars_qwen06b_v1"
# Session-scoped manual ingestion (VS-5b) — lives in a SEPARATE persist dir
# (settings.chroma_session_dir) so pre-loaded demo data is never polluted.
COLLECTION_INGESTED = "Ingested_qwen06b_v1"


@dataclass(frozen=True)
class VectorHit:
    id: str
    document: str
    metadata: dict[str, Any] = field(default_factory=dict)
    distance: float | None = None


class ChromaClient:
    """Thin wrapper over chromadb.PersistentClient with lazy init."""

    def __init__(self, persist_dir: Path) -> None:
        self._persist_dir = persist_dir
        self._client: Any = None

    def _get(self) -> Any:
        if self._client is None:
            import chromadb

            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        return self._client

    def collection(self, name: str) -> Any:
        return self._get().get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    def add(
        self,
        name: str,
        *,
        ids: Sequence[str],
        documents: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[Mapping[str, Any]],
    ) -> None:
        self.collection(name).add(
            ids=list(ids),
            documents=list(documents),
            embeddings=[list(e) for e in embeddings],
            metadatas=[dict(m) for m in metadatas],
        )

    def query(
        self,
        name: str,
        *,
        embedding: Sequence[float],
        n_results: int = 5,
        where: Mapping[str, Any] | None = None,
    ) -> list[VectorHit]:
        result = self.collection(name).query(
            query_embeddings=[list(embedding)],
            n_results=n_results,
            where=dict(where) if where else None,
        )
        ids: list[str] = result["ids"][0]
        documents: list[str] = result["documents"][0]
        metadatas: list[dict[str, Any]] = result["metadatas"][0]
        distances: list[float | None] = (result.get("distances") or [[None] * len(ids)])[0]
        return [
            VectorHit(id=i, document=d, metadata=m or {}, distance=dist)
            for i, d, m, dist in zip(ids, documents, metadatas, distances, strict=True)
        ]

    def get_all(self, name: str, *, where: Mapping[str, Any] | None = None) -> list[VectorHit]:
        result = self.collection(name).get(
            where=dict(where) if where else None, include=["documents", "metadatas"]
        )
        ids: list[str] = result["ids"]
        documents: list[str] = result["documents"] or []
        metadatas: list[dict[str, Any]] = result["metadatas"] or []
        return [
            VectorHit(id=i, document=d, metadata=m or {})
            for i, d, m in zip(ids, documents, metadatas, strict=True)
        ]

    def count(self, name: str) -> int:
        return int(self.collection(name).count())

    def delete_collection(self, name: str) -> None:
        self._get().delete_collection(name)
