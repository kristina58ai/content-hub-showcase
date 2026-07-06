"""API error types and exception handlers (§B.7.3, §B.10)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from content_hub_showcase.api.schemas import error_payload
from content_hub_showcase.shared.logger import get_logger

logger = get_logger(__name__)


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.details = details or {}


class NotFoundError(ApiError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(404, "not_found", message)


class RateLimitExceededError(ApiError):
    def __init__(self, retry_after_seconds: int, limit_type: str) -> None:
        super().__init__(
            429,
            "rate_limit_exceeded",
            f"Slow down — try again in {retry_after_seconds} seconds",
            {"retry_after_seconds": retry_after_seconds, "limit_type": limit_type},
        )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        headers = {}
        retry_after = exc.details.get("retry_after_seconds")
        if exc.status_code == 429 and retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.error_type, exc.message, exc.details),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_payload("validation_error", "Invalid input", {"errors": exc.errors()}),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # No stack traces to users (§B.10.3); full details go to stdout logs only.
        logger.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_payload("internal_error", "Something went wrong on our side"),
        )
