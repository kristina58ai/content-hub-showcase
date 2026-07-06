"""LLM access: Groq primary → OpenRouter fallback (Strategy + tenacity, §B.8.3/§B.10.2)."""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from content_hub_showcase.shared.config import Settings
from content_hub_showcase.shared.logger import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """Base class for LLM provider failures."""


class RateLimitError(LLMError):
    """Provider returned 429."""


class ServiceUnavailableError(LLMError):
    """Provider returned 5xx / connection error / empty completion."""


class LLMAllProvidersFailedError(LLMError):
    def __init__(self) -> None:
        super().__init__("All LLM providers failed (primary + fallback)")


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    fallback_used: bool


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str: ...


def _build_messages(prompt: str, system: str | None) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import groq

            self._client = groq.AsyncGroq(api_key=self._api_key)
        return self._client

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        import groq

        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=_build_messages(prompt, system),
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except groq.RateLimitError as exc:
            raise RateLimitError(str(exc)) from exc
        except (groq.APIStatusError, groq.APIConnectionError) as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        content: str | None = response.choices[0].message.content
        if not content:
            raise ServiceUnavailableError("Groq returned an empty completion")
        return content


class OpenRouterProvider(LLMProvider):
    """OpenRouter via the OpenAI-compatible API (free models, §B.16 OQ-1)."""

    name = "openrouter"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import openai

            self._client = openai.AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1", api_key=self._api_key
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        import openai

        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=_build_messages(prompt, system),
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except openai.RateLimitError as exc:
            raise RateLimitError(str(exc)) from exc
        except (openai.APIStatusError, openai.APIConnectionError) as exc:
            raise ServiceUnavailableError(str(exc)) from exc
        content: str | None = response.choices[0].message.content
        if not content:
            raise ServiceUnavailableError("OpenRouter returned an empty completion")
        return content


class FakeListProvider(LLMProvider):
    """Dev/test provider: cycles through canned responses, no network."""

    name = "fake"

    def __init__(self, responses: Sequence[str] | None = None) -> None:
        canned = list(responses) if responses else ["[fake-llm] canned response"]
        self._cycle = itertools.cycle(canned)

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        return next(self._cycle)


class LLMClient:
    """Fallback chain: try each provider with retry, move on when exhausted (§B.10.2)."""

    def __init__(
        self,
        providers: Sequence[LLMProvider],
        *,
        max_attempts: int = 3,
        wait_min: float = 1.0,
        wait_max: float = 10.0,
    ) -> None:
        if not providers:
            raise ValueError("LLMClient requires at least one provider")
        self._providers = list(providers)
        self._max_attempts = max_attempts
        self._wait_min = wait_min
        self._wait_max = wait_max

    @property
    def provider_names(self) -> list[str]:
        return [p.name for p in self._providers]

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResult:
        for index, provider in enumerate(self._providers):
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self._max_attempts),
                    wait=wait_exponential(multiplier=1, min=self._wait_min, max=self._wait_max),
                    retry=retry_if_exception_type((RateLimitError, ServiceUnavailableError)),
                    reraise=True,
                ):
                    with attempt:
                        text = await provider.generate(
                            prompt,
                            system=system,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        return LLMResult(
                            text=text, provider=provider.name, fallback_used=index > 0
                        )
            except (RateLimitError, ServiceUnavailableError):
                logger.warning(
                    "LLM provider exhausted retries, falling back",
                    extra={"context": {"provider": provider.name}},
                )
                continue
        raise LLMAllProvidersFailedError()


def build_llm_client(settings: Settings) -> LLMClient:
    """Assemble the provider chain per config; fake mode is dev-only (no keys)."""
    if settings.llm_primary_provider == "fake":
        logger.warning(
            "LLM fake mode active — responses are canned (dev-only)",
            extra={"context": {"provider": "fake"}},
        )
        return LLMClient([FakeListProvider()])

    groq: LLMProvider | None = (
        GroqProvider(settings.groq_api_key, settings.groq_model)
        if settings.groq_api_key
        else None
    )
    openrouter: LLMProvider | None = (
        OpenRouterProvider(settings.openrouter_api_key, settings.openrouter_model)
        if settings.openrouter_api_key
        else None
    )

    ordered = [groq, openrouter]
    if settings.llm_primary_provider == "openrouter":
        ordered.reverse()
    providers = [p for p in ordered if p is not None]

    if not providers:
        logger.warning(
            "No LLM API keys configured — falling back to fake provider (dev-only)",
            extra={"context": {"provider": "fake"}},
        )
        return LLMClient([FakeListProvider()])
    return LLMClient(providers)
