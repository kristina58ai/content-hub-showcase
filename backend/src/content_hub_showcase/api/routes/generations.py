"""Generation endpoints: create run, SSE stream, result, status (§B.7.4)."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from content_hub_showcase.agents.shared_types import GenerationMode, Platform
from content_hub_showcase.api.deps import get_archetype_service, get_generation_service
from content_hub_showcase.api.errors import NotFoundError
from content_hub_showcase.api.middleware.session import client_ip
from content_hub_showcase.api.schemas import success_payload

router = APIRouter(tags=["generations"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


class GenerateRequest(BaseModel):
    archetype_id: str = Field(min_length=1, max_length=64)
    topic: str = Field(min_length=3, max_length=300)
    mode: GenerationMode = "from_idea"
    platforms: list[Platform] | None = Field(default=None, min_length=1, max_length=5)


@router.post("/generations")
async def create_generation(request: Request, body: GenerateRequest) -> dict[str, Any]:
    archetype_service = get_archetype_service()
    exists = await asyncio.to_thread(archetype_service.has, body.archetype_id)
    if not exists:
        raise NotFoundError(f"Unknown archetype '{body.archetype_id}'")

    service = get_generation_service()
    handle = await service.start(
        session_id=getattr(request.state, "session_id", "anonymous"),
        ip=client_ip(request),
        archetype_id=body.archetype_id,
        topic=body.topic,
        mode=body.mode,
        platforms=list(body.platforms) if body.platforms else None,
    )
    return success_payload(
        {
            "run_id": handle.run_id,
            "stream_url": f"/api/v1/generations/{handle.run_id}/stream",
        }
    )


@router.get("/generations/{run_id}/stream")
async def stream_generation(run_id: str) -> StreamingResponse:
    service = get_generation_service()
    service.get_handle(run_id)  # 404 before the stream starts
    return StreamingResponse(
        service.stream(run_id), media_type="text/event-stream", headers=_SSE_HEADERS
    )


@router.get("/generations/{run_id}/status")
async def generation_status(run_id: str) -> dict[str, Any]:
    return success_payload(get_generation_service().status(run_id))


@router.get("/generations/{run_id}/result")
async def generation_result(run_id: str) -> dict[str, Any]:
    result = await asyncio.to_thread(get_generation_service().result, run_id)
    return success_payload(result)
