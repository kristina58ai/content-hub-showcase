"""LLM fallback chain: Groq → OpenRouter Strategy (§B.8.3, §B.10.2)."""

from __future__ import annotations

import pytest

from content_hub_showcase.shared.config import Settings
from content_hub_showcase.shared.llm_client import (
    FakeListProvider,
    LLMAllProvidersFailedError,
    LLMClient,
    LLMProvider,
    RateLimitError,
    ServiceUnavailableError,
    build_llm_client,
)


class AlwaysFailingProvider(LLMProvider):
    name = "failing"

    def __init__(self, exc_type: type[Exception]) -> None:
        self._exc_type = exc_type
        self.calls = 0

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        self.calls += 1
        raise self._exc_type("simulated failure")


def fast_client(providers: list[LLMProvider]) -> LLMClient:
    return LLMClient(providers, wait_min=0.001, wait_max=0.002)


async def test_primary_success_no_fallback() -> None:
    client = fast_client([FakeListProvider(["hello"])])
    result = await client.generate("prompt")
    assert result.text == "hello"
    assert result.provider == "fake"
    assert result.fallback_used is False


async def test_rate_limited_primary_falls_back() -> None:
    failing = AlwaysFailingProvider(RateLimitError)
    client = fast_client([failing, FakeListProvider(["fallback answer"])])
    result = await client.generate("prompt")
    assert result.text == "fallback answer"
    assert result.fallback_used is True
    assert failing.calls == 3  # retried before falling back


async def test_unavailable_primary_falls_back() -> None:
    client = fast_client(
        [AlwaysFailingProvider(ServiceUnavailableError), FakeListProvider(["ok"])]
    )
    result = await client.generate("prompt")
    assert result.text == "ok"


async def test_all_providers_failed_raises() -> None:
    client = fast_client(
        [
            AlwaysFailingProvider(RateLimitError),
            AlwaysFailingProvider(ServiceUnavailableError),
        ]
    )
    with pytest.raises(LLMAllProvidersFailedError):
        await client.generate("prompt")


def test_build_llm_client_fake_mode() -> None:
    settings = Settings(_env_file=None, llm_primary_provider="fake")
    assert build_llm_client(settings).provider_names == ["fake"]


def test_build_llm_client_no_keys_falls_back_to_fake() -> None:
    settings = Settings(
        _env_file=None, llm_primary_provider="groq", groq_api_key="", openrouter_api_key=""
    )
    assert build_llm_client(settings).provider_names == ["fake"]


def test_build_llm_client_orders_providers() -> None:
    settings = Settings(
        _env_file=None,
        llm_primary_provider="groq",
        groq_api_key="gk",
        openrouter_api_key="ok",
    )
    assert build_llm_client(settings).provider_names == ["groq", "openrouter"]

    settings = Settings(
        _env_file=None,
        llm_primary_provider="openrouter",
        groq_api_key="gk",
        openrouter_api_key="ok",
    )
    assert build_llm_client(settings).provider_names == ["openrouter", "groq"]
