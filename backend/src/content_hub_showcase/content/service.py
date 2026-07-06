"""Generation runs: async LangGraph execution mapped to SSE frames (§B.7.5, §B.8.1)."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from content_hub_showcase.agents.checkpointer import thread_id as make_thread_id
from content_hub_showcase.agents.graphs.post_generator_graph import POST_GENERATOR_NODES
from content_hub_showcase.api.errors import NotFoundError, RateLimitExceededError
from content_hub_showcase.api.sse import SSEEventType, format_sse
from content_hub_showcase.content.repositories.generated_posts import (
    GeneratedPostsRepository,
)
from content_hub_showcase.content.repositories.ingested import IngestedRepository
from content_hub_showcase.shared.db import utc_now
from content_hub_showcase.shared.embeddings import EmbeddingProvider
from content_hub_showcase.shared.logger import get_logger
from content_hub_showcase.shared.vector_db import COLLECTION_INGESTED, ChromaClient

logger = get_logger(__name__)

RUN_TIMEOUT_SECONDS = 120.0
_PREVIEW_CHARS = 160


@dataclass
class RunHandle:
    run_id: str
    session_id: str
    ip: str
    archetype_id: str
    status: str = "running"  # running | complete | failed
    frames: list[str] = field(default_factory=list)
    new_frame: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task[None] | None = None


def _serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value


class GenerationService:
    """Owns run lifecycle: concurrency guard, event mapping, result persistence."""

    def __init__(
        self,
        graph: Any,
        posts_repository: GeneratedPostsRepository,
        max_concurrent_per_ip: int = 3,
        run_timeout_seconds: float = RUN_TIMEOUT_SECONDS,
        checkpointer: Any = None,
    ) -> None:
        self._graph = graph
        self._repo = posts_repository
        self._max_concurrent = max_concurrent_per_ip
        self._timeout = run_timeout_seconds
        self._checkpointer = checkpointer
        self._checkpointer_ready = False
        self._runs: dict[str, RunHandle] = {}
        self._active_by_ip: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def _ensure_checkpointer(self) -> None:
        """Async Redis saver needs one-time index setup (asetup); memory saver has none."""
        if self._checkpointer_ready:
            return
        setup = getattr(self._checkpointer, "asetup", None)
        if setup is not None:
            await setup()
        self._checkpointer_ready = True

    # --- lifecycle -------------------------------------------------------

    async def start(
        self,
        *,
        session_id: str,
        ip: str,
        archetype_id: str,
        topic: str,
        mode: str = "from_idea",
        platforms: list[str] | None = None,
    ) -> RunHandle:
        await self._ensure_checkpointer()
        # §B.7.6: 3 concurrent generations per IP — enforced here because the
        # middleware cannot observe run completion.
        async with self._lock:
            if self._active_by_ip.get(ip, 0) >= self._max_concurrent:
                raise RateLimitExceededError(60, "concurrent_generations")
            self._active_by_ip[ip] = self._active_by_ip.get(ip, 0) + 1

        run_id = uuid.uuid4().hex
        handle = RunHandle(
            run_id=run_id, session_id=session_id, ip=ip, archetype_id=archetype_id
        )
        self._runs[run_id] = handle

        payload: dict[str, Any] = {
            "archetype_id": archetype_id,
            "topic": topic,
            "mode": mode,
        }
        if platforms:
            payload["platforms"] = platforms
        thread = make_thread_id(
            "post_generator", session_id, utc_now().strftime("%Y%m%dT%H%M%S")
        )
        handle.task = asyncio.create_task(self._execute(handle, payload, thread))
        return handle

    def get_handle(self, run_id: str) -> RunHandle:
        handle = self._runs.get(run_id)
        if handle is None:
            raise NotFoundError(f"Unknown generation run '{run_id}'")
        return handle

    # --- execution -------------------------------------------------------

    def _emit(self, handle: RunHandle, event: SSEEventType, data: dict[str, Any]) -> None:
        handle.frames.append(format_sse(event, data))
        handle.new_frame.set()

    @staticmethod
    def _preview(output: Any) -> str:
        if isinstance(output, dict):
            for key in ("brief", "research_notes", "neutral_body"):
                text = output.get(key)
                if isinstance(text, str) and text:
                    return text[:_PREVIEW_CHARS]
            versions = output.get("platform_versions")
            if isinstance(versions, dict) and versions:
                first = next(iter(versions.values()))
                body = getattr(first, "adapted_body", None) or (
                    first.get("adapted_body") if isinstance(first, dict) else ""
                )
                return str(body)[:_PREVIEW_CHARS]
        return ""

    async def _execute(
        self, handle: RunHandle, payload: dict[str, Any], thread: str
    ) -> None:
        config = {"configurable": {"thread_id": thread}}
        started_at: dict[str, float] = {}
        previous: str | None = None
        final_state: Any = None
        deadline = time.monotonic() + self._timeout
        try:
            async for event in self._graph.astream_events(
                payload, config=config, version="v2"
            ):
                if time.monotonic() > deadline:
                    raise TimeoutError("generation exceeded its time budget")
                kind = event.get("event", "")
                name = event.get("name", "")
                if name in POST_GENERATOR_NODES:
                    if kind == "on_chain_start":
                        if previous and previous != name:
                            self._emit(
                                handle,
                                SSEEventType.GRAPH_TRANSITION,
                                {"from": previous, "to": name},
                            )
                        if name not in started_at:
                            started_at[name] = time.monotonic()
                            self._emit(
                                handle,
                                SSEEventType.AGENT_STARTED,
                                {
                                    "agent": name,
                                    "node_id": name,
                                    "timestamp": utc_now().isoformat(timespec="seconds"),
                                },
                            )
                        previous = name
                    elif kind == "on_chain_end":
                        duration_ms = int(
                            (time.monotonic() - started_at.get(name, time.monotonic()))
                            * 1000
                        )
                        output = event.get("data", {}).get("output")
                        self._emit(
                            handle,
                            SSEEventType.AGENT_COMPLETED,
                            {
                                "agent": name,
                                "duration_ms": duration_ms,
                                "output_preview": self._preview(
                                    output if isinstance(output, dict) else {}
                                ),
                            },
                        )
                elif name == "LangGraph" and kind == "on_chain_end":
                    final_state = event.get("data", {}).get("output")

            result = self._build_result(final_state)
            self._repo.save(
                post_uuid=handle.run_id,
                session_id=handle.session_id,
                archetype_id=handle.archetype_id,
                mode=str(payload.get("mode", "from_idea")),
                neutral_body=result.get("neutral_body"),
                platform_versions=result.get("platform_versions"),
            )
            handle.status = "complete"
            self._emit(
                handle,
                SSEEventType.GENERATION_COMPLETE,
                {"run_id": handle.run_id, "result": result},
            )
        except Exception as exc:  # noqa: BLE001 — every failure becomes an SSE error
            handle.status = "failed"
            logger.error("Generation run failed", exc_info=exc)
            self._emit(
                handle,
                SSEEventType.ERROR,
                {
                    "type": "generation_failed",
                    "message": "Generation failed — try again, or see EXAMPLES.md "
                    "for pre-generated samples",
                    "details": {},
                },
            )
        finally:
            async with self._lock:
                self._active_by_ip[handle.ip] = max(
                    0, self._active_by_ip.get(handle.ip, 1) - 1
                )
            handle.new_frame.set()

    @staticmethod
    def _build_result(final_state: Any) -> dict[str, Any]:
        if not isinstance(final_state, dict):
            return {"neutral_body": None, "platform_versions": {}}
        versions_raw = final_state.get("platform_versions") or {}
        versions = {key: _serialize(value) for key, value in versions_raw.items()}
        return {
            "neutral_body": final_state.get("neutral_body"),
            "platform_versions": versions,
            "provider_events": list(final_state.get("provider_events") or []),
        }

    # --- consumption -----------------------------------------------------

    async def stream(self, run_id: str) -> AsyncIterator[str]:
        handle = self.get_handle(run_id)
        index = 0
        while True:
            while index < len(handle.frames):
                yield handle.frames[index]
                index += 1
            if handle.status != "running":
                break
            handle.new_frame.clear()
            try:
                await asyncio.wait_for(handle.new_frame.wait(), timeout=self._timeout)
            except TimeoutError:
                break
        while index < len(handle.frames):
            yield handle.frames[index]
            index += 1

    def status(self, run_id: str) -> dict[str, Any]:
        handle = self.get_handle(run_id)
        return {"run_id": run_id, "status": handle.status}

    def result(self, run_id: str) -> dict[str, Any]:
        record = self._repo.get(run_id)
        if record is None:
            raise NotFoundError("Result not ready, unknown, or expired (TTL 24h)")
        return record.model_dump()


class IngestService:
    """VS-5b: persist a manual post + embed it into the session-scoped Chroma."""

    def __init__(
        self,
        repository: IngestedRepository,
        session_chroma: ChromaClient,
        embedder: EmbeddingProvider,
    ) -> None:
        self._repo = repository
        self._chroma = session_chroma
        self._embedder = embedder

    def ingest(
        self,
        session_id: str,
        archetype_id: str,
        platform: str,
        text: str,
        views: int = 0,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
    ) -> int:
        from content_hub_showcase.content.models import IngestedPost

        post = IngestedPost(
            session_id=session_id,
            archetype_id=archetype_id,
            platform=platform,  # type: ignore[arg-type]
            text=text,
            views=views,
            likes=likes,
            comments=comments,
            shares=shares,
        )
        row_id = self._repo.save(post)
        embedding = self._embedder.embed_documents([text])[0]
        self._chroma.add(
            COLLECTION_INGESTED,
            ids=[f"{session_id}-{row_id}"],
            documents=[text],
            embeddings=[embedding],
            metadatas=[
                {
                    "session_id": session_id,
                    "archetype": archetype_id,
                    "platform": platform,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "embedding_model": self._embedder.model_tag,
                }
            ],
        )
        return row_id
