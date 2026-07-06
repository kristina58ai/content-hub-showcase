"""Typed prompt templates for all agent networks (§B.4.1: prompts live in Python)."""

from __future__ import annotations

from typing import Any

from langchain_core.prompts import PromptTemplate

from content_hub_showcase.agents.shared_types import Platform

# Per-platform adaptation rules (Showcase-inline equivalent of platforms.json).
PLATFORM_RULES: dict[Platform, dict[str, Any]] = {
    "telegram": {
        "max_length": 4096,
        "tone": "conversational, direct, community-style; short paragraphs",
        "hashtags_max": 3,
        "needs_title": False,
    },
    "x": {
        "max_length": 280,
        "tone": "punchy, compressed, one sharp idea",
        "hashtags_max": 2,
        "needs_title": False,
    },
    "linkedin": {
        "max_length": 3000,
        "tone": "professional, story-driven, line breaks between thoughts",
        "hashtags_max": 5,
        "needs_title": False,
    },
    "medium": {
        "max_length": 20000,
        "tone": "long-form, essay opening that hooks, structured argument",
        "hashtags_max": 5,
        "needs_title": True,
    },
    "threads": {
        "max_length": 500,
        "tone": "casual, quick, personable",
        "hashtags_max": 2,
        "needs_title": False,
    },
}

BRIEFER_PROMPT = PromptTemplate(
    input_variables=["topic", "mode", "facts", "exemplars_topics"],
    template=(
        "You are the Briefer agent of a content system. Build a short creative brief "
        "for a social-media post.\n\n"
        "Topic: {topic}\n"
        "Mode: {mode} (from_plan = the topic comes from the content plan; "
        "from_idea = ad-hoc idea)\n\n"
        "Author personality facts (from RAG):\n{facts}\n\n"
        "Topics of the author's best past posts: {exemplars_topics}\n\n"
        "Write a brief (5-8 sentences): the angle to take, what personality traits to "
        "lean on, what to avoid (taboos), and the emotional register. Plain text only."
    ),
)

RESEARCHER_PROMPT = PromptTemplate(
    input_variables=["topic", "brief", "depth"],
    template=(
        "You are the Researcher agent. Depth: {depth}.\n"
        "Topic: {topic}\nBrief: {brief}\n\n"
        "Produce 3-5 concrete supporting points, angles or well-known facts that make "
        "the post substantive (no fabricated statistics; if uncertain, frame as a "
        "question or opinion). Bullet list, plain text."
    ),
)

WRITER_PROMPT = PromptTemplate(
    input_variables=["topic", "brief", "research_notes", "facts"],
    template=(
        "You are the Writer agent. Write a NEUTRAL platform-agnostic post body "
        "(150-250 words) on the topic below. Neutral means: no hashtags, no platform "
        "formatting, no title — just clean prose in the author's voice.\n\n"
        "Topic: {topic}\nBrief: {brief}\nSupporting points:\n{research_notes}\n\n"
        "Author voice cues:\n{facts}\n\n"
        "Return only the post body text."
    ),
)

PLANNER_CONTEXT_PROMPT = PromptTemplate(
    input_variables=["archetype", "facts"],
    template=(
        "You are the Planner Briefer agent. Summarize this author in 3-4 sentences "
        "as context for content planning.\nAuthor: {archetype}\nFacts:\n{facts}\n"
        "Plain text only."
    ),
)

PLANNER_ANGLES_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=(
        "You are the Planner Researcher agent. Given the author context, list 5 "
        "promising content angles for the next two weeks. Bullet list, plain text.\n"
        "Context: {context}"
    ),
)

PLANNER_GENERATOR_PROMPT = PromptTemplate(
    input_variables=["context", "angles"],
    template=(
        "You are the Planner Generator agent. Draft exactly 3 content-plan entries "
        "as a STRICT JSON array (no markdown fences):\n"
        '[{{"topic": "...", "rationale": "...", "scheduled_for_offset_days": 0, '
        '"target_platforms": ["x"]}}]\n'
        "Platforms allowed: telegram, x, linkedin, medium, threads. Offset 0-13.\n"
        "Context: {context}\nAngles:\n{angles}"
    ),
)

PLANNER_CRITIC_PROMPT = PromptTemplate(
    input_variables=["entries"],
    template=(
        "You are the Planner Critic agent. Review these draft plan entries for "
        "variety, platform fit and author fit. Return the FINAL STRICT JSON array "
        "in the same schema (fix problems, keep exactly 3 items):\n{entries}"
    ),
)

ANALYZER_ANALYST_PROMPT = PromptTemplate(
    input_variables=["rows"],
    template=(
        "You are the Analyst agent. Below are the author's posts sorted from "
        "weakest to strongest engagement. Identify 3-5 concrete patterns that "
        "separate strong posts from weak ones. Bullet list.\nPosts:\n{rows}"
    ),
)

ANALYZER_CRITIC_PROMPT = PromptTemplate(
    input_variables=["patterns", "rows"],
    template=(
        "You are the Analyzer Critic agent. Validate these patterns against the "
        "data; drop unsupported ones, refine wording. Return the final bullet "
        "list.\nPatterns:\n{patterns}\nData:\n{rows}"
    ),
)

ANALYZER_EDITOR_PROMPT = PromptTemplate(
    input_variables=["patterns"],
    template=(
        "You are the Editor agent. Turn the validated patterns into 2-3 suggested "
        "memory updates — what the system should remember about what works for "
        "this author. Bullet list.\nPatterns:\n{patterns}"
    ),
)

SOCIAL_WRITER_PROMPT = PromptTemplate(
    input_variables=[
        "platform",
        "tone",
        "max_length",
        "hashtags_max",
        "needs_title",
        "neutral_body",
        "exemplars",
    ],
    template=(
        "You are the Social Writer agent. Adapt the neutral post below for {platform}.\n"
        "Platform rules: tone = {tone}; hard max length = {max_length} characters; "
        "at most {hashtags_max} hashtags; title required: {needs_title}.\n\n"
        "Few-shot: the author's best past {platform} posts:\n{exemplars}\n\n"
        "Neutral post:\n{neutral_body}\n\n"
        "Respond with STRICT JSON only (no markdown fences):\n"
        '{{"adapted_body": "...", "platform_title": null or "...", '
        '"hashtags": ["#..."], "mentions": [], "category": "short-topic-slug"}}'
    ),
)
