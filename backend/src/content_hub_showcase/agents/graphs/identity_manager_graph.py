"""Identity Manager graph (Showcase): archetype loader, read-only (§B.3.1, ADR-014).

No checkpointer — the loader is a stateless read; durable state is only needed
for generation flows (post_generator/planner/analyzer).
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from content_hub_showcase.agents.nodes.identity_manager.loader import (
    make_count_exemplars,
    make_load_personality,
)
from content_hub_showcase.agents.states.identity_manager import IdentityLoaderState
from content_hub_showcase.personality.repository import PersonalityRepository


def build_identity_manager_graph(repository: PersonalityRepository) -> Any:
    graph = StateGraph(IdentityLoaderState)
    # cast: LangGraph's add_node overloads don't unify with plain Callable aliases.
    graph.add_node("load_personality", cast(Any, make_load_personality(repository)))
    graph.add_node("count_exemplars", cast(Any, make_count_exemplars(repository)))
    graph.add_edge(START, "load_personality")
    graph.add_edge("load_personality", "count_exemplars")
    graph.add_edge("count_exemplars", END)
    return graph.compile()
