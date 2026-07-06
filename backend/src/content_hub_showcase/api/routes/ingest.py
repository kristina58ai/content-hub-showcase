"""Data Ingestion endpoint — visible manual input demo feature (VS-5b, ADR-016)."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from content_hub_showcase.agents.shared_types import Platform
from content_hub_showcase.api.deps import get_archetype_service, get_ingest_service
from content_hub_showcase.api.errors import NotFoundError
from content_hub_showcase.api.schemas import success_payload

router = APIRouter(tags=["ingest"])


class IngestRequest(BaseModel):
    archetype: str = Field(min_length=1, max_length=64)
    platform: Platform
    text: str = Field(min_length=10, max_length=5000)
    views: int = Field(default=0, ge=0, le=100_000_000)
    likes: int = Field(default=0, ge=0, le=100_000_000)
    comments: int = Field(default=0, ge=0, le=100_000_000)
    shares: int = Field(default=0, ge=0, le=100_000_000)


@router.post("/demo/ingest")
async def ingest_post(request: Request, body: IngestRequest) -> dict[str, Any]:
    exists = await asyncio.to_thread(get_archetype_service().has, body.archetype)
    if not exists:
        raise NotFoundError(f"Unknown archetype '{body.archetype}'")

    session_id = getattr(request.state, "session_id", "anonymous")
    ingested_id = await asyncio.to_thread(
        get_ingest_service().ingest,
        session_id,
        body.archetype,
        body.platform,
        body.text,
        body.views,
        body.likes,
        body.comments,
        body.shares,
    )
    return success_payload(
        {
            "ingested_id": ingested_id,
            "session_scoped": True,
            "embedded": True,
            "participates_in_learning_cycle": True,
        }
    )
