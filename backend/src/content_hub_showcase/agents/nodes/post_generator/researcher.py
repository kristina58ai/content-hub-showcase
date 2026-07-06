"""Researcher node: supporting points at a configurable depth.

Deviation note (BUILD_REPORT §6): no external web-search API is used — the
public demo must not depend on fragile external services (the same reasoning
that removed checkers, ADR-016). Research is LLM-derived supporting points.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from content_hub_showcase.agents.prompts import RESEARCHER_PROMPT
from content_hub_showcase.agents.states.post_generator import PostGeneratorState
from content_hub_showcase.shared.llm_client import LLMClient

_DEPTH_TOKENS = {"low": 250, "medium": 450, "deep": 800}


def make_researcher(
    llm: LLMClient,
) -> Callable[[PostGeneratorState], Awaitable[dict[str, Any]]]:
    async def researcher(state: PostGeneratorState) -> dict[str, Any]:
        prompt = RESEARCHER_PROMPT.format(
            topic=state.topic, brief=state.brief, depth=state.research_depth
        )
        result = await llm.generate(
            prompt, max_tokens=_DEPTH_TOKENS[state.research_depth]
        )
        return {
            "research_notes": result.text.strip(),
            "provider_events": [f"researcher:{result.provider}"],
        }

    return researcher
