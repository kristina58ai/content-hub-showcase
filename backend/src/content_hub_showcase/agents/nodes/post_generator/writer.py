"""Writer node: neutral platform-agnostic post body (§B.3.2)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from content_hub_showcase.agents.prompts import WRITER_PROMPT
from content_hub_showcase.agents.states.post_generator import PostGeneratorState
from content_hub_showcase.shared.llm_client import LLMClient


def make_writer(
    llm: LLMClient,
) -> Callable[[PostGeneratorState], Awaitable[dict[str, Any]]]:
    async def writer(state: PostGeneratorState) -> dict[str, Any]:
        prompt = WRITER_PROMPT.format(
            topic=state.topic,
            brief=state.brief,
            research_notes=state.research_notes,
            facts="\n".join(f"- {fact.fact}" for fact in state.facts[:8])
            or "- (no facts)",
        )
        result = await llm.generate(prompt, max_tokens=700)
        return {
            "neutral_body": result.text.strip(),
            "provider_events": [f"writer:{result.provider}"],
        }

    return writer
