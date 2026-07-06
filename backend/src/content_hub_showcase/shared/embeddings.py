"""Embedding Strategy (ADR-017): local Qwen3-Embedding-0.6B, 1024-dim, offline."""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from content_hub_showcase.shared.config import Settings

EMBEDDING_DIMENSION = 1024


class EmbeddingProvider(ABC):
    dimension: int = EMBEDDING_DIMENSION
    model_tag: str = "unknown"

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...


class LocalQwenProvider(EmbeddingProvider):
    """In-process sentence-transformers model; downloads once, then fully offline."""

    model_tag = "qwen3-embedding-0.6b-1024"

    def __init__(self, model_name: str = "Qwen/Qwen3-Embedding-0.6B") -> None:
        self._model_name = model_name
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        vectors = model.encode(list(texts), normalize_embeddings=True)
        return [[float(x) for x in vector] for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        model = self._load()
        try:
            # Qwen3-Embedding ships an instruction-aware "query" prompt in its config.
            vector = model.encode([text], prompt_name="query", normalize_embeddings=True)[0]
        except (KeyError, ValueError):
            vector = model.encode([text], normalize_embeddings=True)[0]
        return [float(x) for x in vector]


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic hash-based unit vectors for tests — no model download."""

    model_tag = "fake-1024"

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def _vector(self, text: str) -> list[float]:
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [((seed[i % 32] * (i + 7)) % 255) / 254.0 - 0.5 for i in range(self.dimension)]
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "fake":
        return FakeEmbeddingProvider()
    return LocalQwenProvider(settings.local_embed_model)
