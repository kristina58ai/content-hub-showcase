"""Demo learning-cycle endpoint (§B.7.4, §B.3.6)."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request

from content_hub_showcase.api.deps import get_archetype_service, get_learning_service
from content_hub_showcase.api.errors import NotFoundError
from content_hub_showcase.api.schemas import success_payload

router = APIRouter(tags=["learning"])


@router.post("/archetypes/{archetype_id}/learning-cycle")
async def run_learning_cycle(archetype_id: str, request: Request) -> dict[str, Any]:
    exists = await asyncio.to_thread(get_archetype_service().has, archetype_id)
    if not exists:
        raise NotFoundError(f"Unknown archetype '{archetype_id}'")
    session_id = getattr(request.state, "session_id", "anonymous")
    result = await get_learning_service().run_cycle(archetype_id, session_id)
    return success_payload(result)
