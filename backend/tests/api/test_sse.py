"""SSE frame formatting (§B.7.5)."""

from __future__ import annotations

import json

from content_hub_showcase.api.sse import SSEEventType, format_sse


def test_format_sse_frame_structure() -> None:
    frame = format_sse(SSEEventType.AGENT_STARTED, {"agent": "briefer", "node_id": "briefer"})
    lines = frame.split("\n")
    assert lines[0] == "event: agent_started"
    assert lines[1].startswith("data: ")
    assert frame.endswith("\n\n")
    data = json.loads(lines[1].removeprefix("data: "))
    assert data == {"agent": "briefer", "node_id": "briefer"}


def test_format_sse_accepts_plain_string_event() -> None:
    frame = format_sse("custom_event", {"x": 1})
    assert frame.startswith("event: custom_event\n")


def test_format_sse_serializes_non_json_values() -> None:
    frame = format_sse(SSEEventType.ERROR, {"detail": Exception("boom")})
    assert "boom" in frame


def test_all_spec_event_types_present() -> None:
    expected = {
        "agent_started",
        "agent_progress",
        "agent_completed",
        "graph_transition",
        "generation_complete",
        "error",
    }
    assert {e.value for e in SSEEventType} == expected
