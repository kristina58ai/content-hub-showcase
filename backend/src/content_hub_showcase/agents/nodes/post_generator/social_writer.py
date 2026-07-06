"""Social Writer node: per-platform adaptation, runs in parallel via Send fan-out."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from content_hub_showcase.agents.prompts import PLATFORM_RULES, SOCIAL_WRITER_PROMPT
from content_hub_showcase.agents.shared_types import Platform, PostVersion
from content_hub_showcase.agents.states.post_generator import PostGeneratorState
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient


def parse_post_version(raw: str, platform: Platform) -> PostVersion:
    """Parse the strict-JSON response; degrade gracefully to plain text."""
    max_length = int(PLATFORM_RULES[platform]["max_length"])
    candidate = raw.strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start != -1 and end > start:
        try:
            payload: dict[str, Any] = json.loads(candidate[start : end + 1])
            body = str(payload.get("adapted_body", "")).strip()
            if body:
                return PostVersion(
                    platform=platform,
                    adapted_body=body[:max_length],
                    platform_title=payload.get("platform_title") or None,
                    hashtags=[str(h) for h in payload.get("hashtags", [])][:5],
                    mentions=[str(m) for m in payload.get("mentions", [])][:5],
                    category=str(payload.get("category") or "") or None,
                )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    # Fallback: model ignored the JSON contract — ship the raw text, truncated.
    return PostVersion(platform=platform, adapted_body=candidate[:max_length])


def make_social_writer(
    repository: PersonalityRepository, llm: LLMClient
) -> Callable[[PostGeneratorState], Awaitable[dict[str, Any]]]:
    async def social_writer(raw: PostGeneratorState | dict[str, Any]) -> dict[str, Any]:
        # Send() delivers a plain dict payload — normalize to the typed state.
        state = (
            raw
            if isinstance(raw, PostGeneratorState)
            else PostGeneratorState.model_validate(raw)
        )
        if state.platform is None:
            raise ValueError("social_writer must be entered via Send with a platform")
        platform = state.platform
        rules = PLATFORM_RULES[platform]
        exemplars = await asyncio.to_thread(
            repository.exemplars_for, state.archetype_id, state.topic, 2, platform
        )
        prompt = SOCIAL_WRITER_PROMPT.format(
            platform=platform,
            tone=rules["tone"],
            max_length=rules["max_length"],
            hashtags_max=rules["hashtags_max"],
            needs_title=rules["needs_title"],
            neutral_body=state.neutral_body,
            exemplars="\n---\n".join(e.text for e in exemplars) or "(none available)",
        )
        result = await llm.generate(prompt, max_tokens=900)
        version = parse_post_version(result.text, platform)
        return {
            "platform_versions": {platform: version},
            "provider_events": [f"social_writer[{platform}]:{result.provider}"],
        }

    return social_writer
