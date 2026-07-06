"""Planner nodes: Briefer → Researcher → Generator → Critic (plan.md VS-5)."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from content_hub_showcase.agents.prompts import (
    PLANNER_ANGLES_PROMPT,
    PLANNER_CONTEXT_PROMPT,
    PLANNER_CRITIC_PROMPT,
    PLANNER_GENERATOR_PROMPT,
)
from content_hub_showcase.agents.shared_types import PlanEntry
from content_hub_showcase.agents.states.planner import PlannerState
from content_hub_showcase.personality.repository import PersonalityRepository
from content_hub_showcase.shared.llm_client import LLMClient

PlannerNode = Callable[[PlannerState], Awaitable[dict[str, Any]]]


def parse_plan_entries(raw: str) -> list[PlanEntry]:
    """Parse a strict-JSON array of plan entries; invalid items are dropped."""
    candidate = raw.strip()
    start = candidate.find("[")
    end = candidate.rfind("]")
    if start == -1 or end <= start:
        return []
    try:
        items = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return []
    entries: list[PlanEntry] = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            try:
                entries.append(PlanEntry(**item))
            except (ValidationError, TypeError):
                continue
    return entries


def make_context_briefer(
    repository: PersonalityRepository, llm: LLMClient
) -> PlannerNode:
    async def context_briefer(state: PlannerState) -> dict[str, Any]:
        facts = await asyncio.to_thread(repository.facts_for, state.archetype_id)
        prompt = PLANNER_CONTEXT_PROMPT.format(
            archetype=state.archetype_id,
            facts="\n".join(f"- {fact.fact}" for fact in facts[:12]) or "- (none)",
        )
        result = await llm.generate(prompt, max_tokens=300)
        return {
            "context": result.text.strip(),
            "provider_events": [f"plan_briefer:{result.provider}"],
        }

    return context_briefer


def make_angle_researcher(llm: LLMClient) -> PlannerNode:
    async def angle_researcher(state: PlannerState) -> dict[str, Any]:
        result = await llm.generate(
            PLANNER_ANGLES_PROMPT.format(context=state.context), max_tokens=300
        )
        return {
            "angles": result.text.strip(),
            "provider_events": [f"plan_researcher:{result.provider}"],
        }

    return angle_researcher


def make_plan_generator(llm: LLMClient) -> PlannerNode:
    async def plan_generator(state: PlannerState) -> dict[str, Any]:
        result = await llm.generate(
            PLANNER_GENERATOR_PROMPT.format(context=state.context, angles=state.angles),
            max_tokens=700,
        )
        return {
            "draft": result.text.strip(),
            "provider_events": [f"plan_generator:{result.provider}"],
        }

    return plan_generator


def make_plan_critic(llm: LLMClient) -> PlannerNode:
    async def plan_critic(state: PlannerState) -> dict[str, Any]:
        result = await llm.generate(
            PLANNER_CRITIC_PROMPT.format(entries=state.draft), max_tokens=700
        )
        entries = parse_plan_entries(result.text) or parse_plan_entries(state.draft)
        return {
            "entries": entries,
            "provider_events": [f"plan_critic:{result.provider}"],
        }

    return plan_critic
