"""Service endpoints: health check (keep-alive target) and version (§B.7.4)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from content_hub_showcase.api.schemas import success_payload
from content_hub_showcase.shared.config import get_settings

router = APIRouter(tags=["service"])


@router.get("/health")
async def health() -> dict[str, Any]:
    return success_payload({"status": "ok"})


@router.get("/version")
async def version() -> dict[str, Any]:
    return success_payload({"version": get_settings().app_version})
