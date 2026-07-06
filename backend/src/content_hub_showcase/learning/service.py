"""Learning cycle service — runs the Analyzer graph for one demo session (§B.3.6)."""

from __future__ import annotations

from typing import Any


class LearningService:
    def __init__(self, analyzer_graph: Any) -> None:
        self._graph = analyzer_graph

    async def run_cycle(self, archetype_id: str, session_id: str) -> dict[str, Any]:
        state = await self._graph.ainvoke(
            {"archetype_id": archetype_id, "session_id": session_id}
        )
        return {
            "patterns": state["validated_patterns"] or state["patterns"],
            "raw_patterns": state["patterns"],
            "rag_suggestions": state["rag_suggestions"],
            "plan_suggestions": [entry.model_dump() for entry in state["plan_suggestions"]],
            "inputs": {
                "exemplars": len(state["exemplars"]),
                "ingested_this_session": len(state["ingested"]),
            },
        }
