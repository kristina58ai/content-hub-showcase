"""Finalizer node: guarantee every requested platform has a version."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from content_hub_showcase.agents.prompts import PLATFORM_RULES
from content_hub_showcase.agents.shared_types import PostVersion
from content_hub_showcase.agents.states.post_generator import PostGeneratorState


def make_finalizer() -> Callable[[PostGeneratorState], dict[str, Any]]:
    def finalizer(state: PostGeneratorState) -> dict[str, Any]:
        missing = [p for p in state.platforms if p not in state.platform_versions]
        if not missing:
            return {"provider_events": ["finalizer:ok"]}
        # A branch degraded past recovery — fill from the neutral body so the demo
        # always shows every requested tab (visible resilience over hard failure).
        filled = {
            platform: PostVersion(
                platform=platform,
                adapted_body=state.neutral_body[
                    : int(PLATFORM_RULES[platform]["max_length"])
                ],
            )
            for platform in missing
        }
        return {
            "platform_versions": filled,
            "provider_events": [f"finalizer:filled_missing={','.join(missing)}"],
        }

    return finalizer
