"""Analyzer nodes: load → merge/sort (python) → analyst → critic → editor →
plan advisor (invokes the Planner graph). Demo learning cycle, §B.3.6/ADR-016."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from content_hub_showcase.agents.prompts import (
    ANALYZER_ANALYST_PROMPT,
    ANALYZER_CRITIC_PROMPT,
    ANALYZER_EDITOR_PROMPT,
)
from content_hub_showcase.agents.states.analyzer import AnalyzerState
from content_hub_showcase.content.repositories.ingested import IngestedRepository
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient

AnalyzerNode = Callable[[AnalyzerState], Awaitable[dict[str, Any]]]


def make_load_inputs(
    repository: PersonalityRepository, ingested_repo: IngestedRepository
) -> AnalyzerNode:
    async def load_inputs(state: AnalyzerState) -> dict[str, Any]:
        exemplars = await asyncio.to_thread(repository.exemplars_all, state.archetype_id)
        ingested = (
            await asyncio.to_thread(
                ingested_repo.list_for_session, state.session_id, state.archetype_id
            )
            if state.session_id
            else []
        )
        return {"exemplars": exemplars, "ingested": ingested}

    return load_inputs


def _engagement(views: int, likes: int, comments: int, shares: int) -> float:
    if views <= 0:
        return float(likes + comments + shares)
    return round((likes + 2 * comments + 3 * shares) / views * 100, 2)


def make_merge_sort() -> Callable[[AnalyzerState], dict[str, Any]]:
    def merge_sort(state: AnalyzerState) -> dict[str, Any]:
        rows: list[tuple[float, str]] = []
        for exemplar in state.exemplars:
            rows.append(
                (
                    exemplar.engagement_score,
                    f"[{exemplar.engagement_score:.1f}] {exemplar.platform} | "
                    f"{exemplar.topic} | {exemplar.text[:120]}",
                )
            )
        for post in state.ingested:
            score = _engagement(post.views, post.likes, post.comments, post.shares)
            rows.append(
                (
                    score,
                    f"[{score:.1f}] {post.platform} | (ingested this session) | "
                    f"{post.text[:120]}",
                )
            )
        rows.sort(key=lambda row: row[0])  # weakest → strongest (§A.8.2 SORT)
        return {"rows_text": "\n".join(text for _, text in rows) or "(no posts)"}

    return merge_sort


def make_analyst(llm: LLMClient) -> AnalyzerNode:
    async def analyst(state: AnalyzerState) -> dict[str, Any]:
        result = await llm.generate(
            ANALYZER_ANALYST_PROMPT.format(rows=state.rows_text), max_tokens=500
        )
        return {
            "patterns": result.text.strip(),
            "provider_events": [f"analyst:{result.provider}"],
        }

    return analyst


def make_analyzer_critic(llm: LLMClient) -> AnalyzerNode:
    async def analyzer_critic(state: AnalyzerState) -> dict[str, Any]:
        result = await llm.generate(
            ANALYZER_CRITIC_PROMPT.format(patterns=state.patterns, rows=state.rows_text),
            max_tokens=500,
        )
        return {
            "validated_patterns": result.text.strip(),
            "provider_events": [f"analyzer_critic:{result.provider}"],
        }

    return analyzer_critic


def make_editor(llm: LLMClient) -> AnalyzerNode:
    async def editor(state: AnalyzerState) -> dict[str, Any]:
        result = await llm.generate(
            ANALYZER_EDITOR_PROMPT.format(patterns=state.validated_patterns),
            max_tokens=400,
        )
        return {
            "rag_suggestions": result.text.strip(),
            "provider_events": [f"editor:{result.provider}"],
        }

    return editor


def make_plan_advisor(planner_graph: Any) -> AnalyzerNode:
    async def plan_advisor(state: AnalyzerState) -> dict[str, Any]:
        planner_out = await planner_graph.ainvoke({"archetype_id": state.archetype_id})
        return {
            "plan_suggestions": planner_out["entries"],
            "provider_events": list(planner_out["provider_events"]),
        }

    return plan_advisor
