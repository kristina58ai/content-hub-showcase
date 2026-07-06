"""SSE event helpers for LangGraph streaming (§B.7.5)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from enum import StrEnum


class SSEEventType(StrEnum):
    AGENT_STARTED = "agent_started"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    GRAPH_TRANSITION = "graph_transition"
    GENERATION_COMPLETE = "generation_complete"
    ERROR = "error"


def format_sse(event: SSEEventType | str, data: Mapping[str, object]) -> str:
    """Render one SSE frame: `event: <name>\\ndata: <json>\\n\\n`."""
    name = event.value if isinstance(event, SSEEventType) else event
    body = json.dumps(dict(data), ensure_ascii=False, default=str)
    return f"event: {name}\ndata: {body}\n\n"
