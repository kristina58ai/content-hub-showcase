"""Briefer node: mode-aware brief from personality RAG + exemplar topics (§B.3.2)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from content_hub_showcase.agents.prompts import BRIEFER_PROMPT
from content_hub_showcase.agents.states.post_generator import PostGeneratorState
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient


def make_briefer(
    repository: PersonalityRepository, llm: LLMClient
) -> Callable[[PostGeneratorState], Awaitable[dict[str, Any]]]:
    async def briefer(state: PostGeneratorState) -> dict[str, Any]:
        facts = await asyncio.to_thread(
            repository.search_facts, state.archetype_id, state.topic, 8
        )
        exemplars = await asyncio.to_thread(
            repository.exemplars_for, state.archetype_id, state.topic, 3
        )
        prompt = BRIEFER_PROMPT.format(
            topic=state.topic,
            mode=state.mode,
            facts="\n".join(f"- {fact.fact}" for fact in facts) or "- (no facts found)",
            exemplars_topics=", ".join(e.topic for e in exemplars) or "none",
        )
        result = await llm.generate(prompt, max_tokens=400)
        return {
            "facts": facts,
            "exemplars": exemplars,
            "brief": result.text.strip(),
            "provider_events": [f"briefer:{result.provider}"],
        }

    return briefer
