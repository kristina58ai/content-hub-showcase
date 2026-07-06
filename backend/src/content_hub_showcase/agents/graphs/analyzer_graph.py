"""Analyzer graph: demo learning cycle over pre-loaded + session-ingested data.

load_inputs → merge_sort (python) → analyst → critic → editor → plan_advisor
(§B.3.6; the plan advisor stage invokes the Planner graph, mirroring §A.8.2)."""

from __future__ import annotations

from typing import Any, cast

from langgraph.graph import END, START, StateGraph

from content_hub_showcase.agents.nodes.analyzer.nodes import (
    make_analyst,
    make_analyzer_critic,
    make_editor,
    make_load_inputs,
    make_merge_sort,
    make_plan_advisor,
)
from content_hub_showcase.agents.states.analyzer import AnalyzerState
from content_hub_showcase.content.repositories.ingested import IngestedRepository
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient

ANALYZER_NODES = (
    "load_inputs",
    "merge_sort",
    "analyst",
    "analyzer_critic",
    "editor",
    "plan_advisor",
)


def build_analyzer_graph(
    repository: PersonalityRepository,
    ingested_repo: IngestedRepository,
    llm: LLMClient,
    planner_graph: Any,
    checkpointer: Any = None,
) -> Any:
    graph = StateGraph(AnalyzerState)
    # cast: LangGraph's add_node overloads don't unify with plain Callable aliases.
    graph.add_node("load_inputs", cast(Any, make_load_inputs(repository, ingested_repo)))
    graph.add_node("merge_sort", cast(Any, make_merge_sort()))
    graph.add_node("analyst", cast(Any, make_analyst(llm)))
    graph.add_node("analyzer_critic", cast(Any, make_analyzer_critic(llm)))
    graph.add_node("editor", cast(Any, make_editor(llm)))
    graph.add_node("plan_advisor", cast(Any, make_plan_advisor(planner_graph)))

    graph.add_edge(START, "load_inputs")
    graph.add_edge("load_inputs", "merge_sort")
    graph.add_edge("merge_sort", "analyst")
    graph.add_edge("analyst", "analyzer_critic")
    graph.add_edge("analyzer_critic", "editor")
    graph.add_edge("editor", "plan_advisor")
    graph.add_edge("plan_advisor", END)
    return graph.compile(checkpointer=checkpointer)
