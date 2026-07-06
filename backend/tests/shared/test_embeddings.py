"""Embedding Strategy: fake provider behaviour + factory wiring (ADR-017)."""

from __future__ import annotations

import math

import pytest

from content_hub_showcase.shared.config import Settings
from content_hub_showcase.shared.embeddings import (
    EMBEDDING_DIMENSION,
    FakeEmbeddingProvider,
    LocalQwenProvider,
    build_embedding_provider,
)


def test_dimension_is_1024_per_adr_017() -> None:
    assert EMBEDDING_DIMENSION == 1024


def test_fake_provider_shape_and_determinism() -> None:
    provider = FakeEmbeddingProvider()
    v1 = provider.embed_query("hello world")
    v2 = provider.embed_query("hello world")
    v3 = provider.embed_query("different text")
    assert len(v1) == 1024
    assert v1 == v2
    assert v1 != v3


def test_fake_provider_vectors_are_normalized() -> None:
    vector = FakeEmbeddingProvider().embed_query("normalize me")
    norm = math.sqrt(sum(x * x for x in vector))
    assert abs(norm - 1.0) < 1e-6


def test_fake_provider_documents_batch() -> None:
    provider = FakeEmbeddingProvider()
    vectors = provider.embed_documents(["a", "b"])
    assert len(vectors) == 2
    assert vectors[0] == provider.embed_query("a")


def test_factory_returns_fake_when_configured() -> None:
    settings = Settings(_env_file=None, embedding_provider="fake")
    assert isinstance(build_embedding_provider(settings), FakeEmbeddingProvider)


def test_factory_returns_local_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    # conftest exports EMBEDDING_PROVIDER=fake for the suite; default is tested clean.
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    settings = Settings(_env_file=None)
    provider = build_embedding_provider(settings)
    # Construction must not download the model (lazy load).
    assert isinstance(provider, LocalQwenProvider)
    assert provider.model_tag == "qwen3-embedding-0.6b-1024"
