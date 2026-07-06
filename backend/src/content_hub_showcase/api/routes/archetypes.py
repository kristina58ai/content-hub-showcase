"""Archetype endpoints (§B.7.4): list + detail via Identity Manager loader."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter

from content_hub_showcase.api.deps import get_archetype_service
from content_hub_showcase.api.errors import NotFoundError
from content_hub_showcase.api.schemas import success_payload

router = APIRouter(tags=["archetypes"])


@router.get("/archetypes")
async def list_archetypes() -> dict[str, Any]:
    service = get_archetype_service()
    summaries = await asyncio.to_thread(service.list_archetypes)
    return success_payload([summary.model_dump() for summary in summaries])


@router.get("/archetypes/{archetype_id}")
async def archetype_detail(archetype_id: str) -> dict[str, Any]:
    service = get_archetype_service()
    detail = await asyncio.to_thread(service.get_detail, archetype_id)
    if detail is None:
        raise NotFoundError(f"Unknown archetype '{archetype_id}'")
    return success_payload(detail.model_dump())
