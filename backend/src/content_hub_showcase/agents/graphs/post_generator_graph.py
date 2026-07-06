"""PostGenerator graph: briefer → researcher → writer → social_writer×N → finalizer.

The social_writer stage fans out in parallel via the Send API — one branch per
requested platform (§B.3.2, ADR-005/ADR-006). Checkpointer is injected:
ShallowRedisSaver in production (ADR-009), InMemorySaver in tests.
"""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from content_hub_showcase.agents.nodes.post_generator.briefer import make_briefer
from content_hub_showcase.agents.nodes.post_generator.finalizer import make_finalizer
from content_hub_showcase.agents.nodes.post_generator.researcher import make_researcher
from content_hub_showcase.agents.nodes.post_generator.social_writer import (
    make_social_writer,
)
from content_hub_showcase.agents.nodes.post_generator.writer import make_writer
from content_hub_showcase.agents.states.post_generator import PostGeneratorState
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient

POST_GENERATOR_NODES = ("briefer", "researcher", "writer", "social_writer", "finalizer")


def _fan_out(state: PostGeneratorState) -> list[Send]:
    base = state.model_dump()
    return [Send("social_writer", {**base, "platform": platform}) for platform in state.platforms]


def build_post_generator_graph(
    repository: PersonalityRepository,
    llm: LLMClient,
    checkpointer: Any = None,
) -> Any:
    graph = StateGraph(PostGeneratorState)
    # cast: LangGraph's add_node overloads don't unify with plain Callable aliases.
    graph.add_node("briefer", cast(Any, make_briefer(repository, llm)))
    graph.add_node("researcher", cast(Any, make_researcher(llm)))
    graph.add_node("writer", cast(Any, make_writer(llm)))
    graph.add_node("social_writer", cast(Any, make_social_writer(repository, llm)))
    graph.add_node("finalizer", cast(Any, make_finalizer()))

    graph.add_edge(START, "briefer")
    graph.add_edge("briefer", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_conditional_edges("writer", _fan_out, ["social_writer"])
    graph.add_edge("social_writer", "finalizer")
    graph.add_edge("finalizer", END)
    return graph.compile(checkpointer=checkpointer)
