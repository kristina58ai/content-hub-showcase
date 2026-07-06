"""Pre-loaded content plan endpoint (§B.7.4, §B.3.4)."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter

from content_hub_showcase.api.deps import get_archetype_service
from content_hub_showcase.api.errors import NotFoundError
from content_hub_showcase.api.schemas import success_payload

router = APIRouter(tags=["plans"])


@router.get("/archetypes/{archetype_id}/plan")
async def archetype_plan(archetype_id: str) -> dict[str, Any]:
    plan = await asyncio.to_thread(get_archetype_service().plan, archetype_id)
    if plan is None:
        raise NotFoundError(f"Unknown archetype '{archetype_id}'")
    return success_payload([entry.model_dump() for entry in plan])
