"""Identity Manager nodes: load archetype personality + exemplar stats from Chroma."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from typing import Any

from content_hub_showcase.agents.states.identity_manager import IdentityLoaderState
from content_hub_showcase.personality.repository import PersonalityRepository


def make_load_personality(
    repository: PersonalityRepository,
) -> Callable[[IdentityLoaderState], dict[str, Any]]:
    def load_personality(state: IdentityLoaderState) -> dict[str, Any]:
        facts = repository.facts_for(state.archetype_id)
        counts = Counter(fact.category for fact in facts)
        return {"facts": facts, "facts_by_category": dict(counts)}

    return load_personality


def make_count_exemplars(
    repository: PersonalityRepository,
) -> Callable[[IdentityLoaderState], dict[str, Any]]:
    def count_exemplars(state: IdentityLoaderState) -> dict[str, Any]:
        return {"exemplars_count": repository.exemplars_count(state.archetype_id)}

    return count_exemplars
