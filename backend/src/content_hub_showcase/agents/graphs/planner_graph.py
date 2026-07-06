"""Planner graph: Briefer → Researcher → Generator → Critic (§B.3.4, ADR-014)."""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from content_hub_showcase.agents.nodes.planner.nodes import (
    make_angle_researcher,
    make_context_briefer,
    make_plan_critic,
    make_plan_generator,
)
from content_hub_showcase.agents.states.planner import PlannerState
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient

PLANNER_NODES = ("plan_briefer", "plan_researcher", "plan_generator", "plan_critic")


def build_planner_graph(
    repository: PersonalityRepository, llm: LLMClient, checkpointer: Any = None
) -> Any:
    graph = StateGraph(PlannerState)
    # cast: LangGraph's add_node overloads don't unify with plain Callable aliases.
    graph.add_node("plan_briefer", cast(Any, make_context_briefer(repository, llm)))
    graph.add_node("plan_researcher", cast(Any, make_angle_researcher(llm)))
    graph.add_node("plan_generator", cast(Any, make_plan_generator(llm)))
    graph.add_node("plan_critic", cast(Any, make_plan_critic(llm)))

    graph.add_edge(START, "plan_briefer")
    graph.add_edge("plan_briefer", "plan_researcher")
    graph.add_edge("plan_researcher", "plan_generator")
    graph.add_edge("plan_generator", "plan_critic")
    graph.add_edge("plan_critic", END)
    return graph.compile(checkpointer=checkpointer)
