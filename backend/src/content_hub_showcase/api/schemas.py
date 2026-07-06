"""API response envelope (§B.7.2) and shared request/response schemas."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Meta(BaseModel):
    request_id: str = Field(default_factory=_request_id)
    timestamp: str = Field(default_factory=_timestamp)


class ErrorBody(BaseModel):
    type: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


def success_payload(data: Any) -> dict[str, Any]:
    return {"data": data, "meta": Meta().model_dump()}


def error_payload(
    error_type: str, message: str, details: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "error": ErrorBody(type=error_type, message=message, details=details or {}).model_dump(),
        "meta": Meta().model_dump(),
    }
