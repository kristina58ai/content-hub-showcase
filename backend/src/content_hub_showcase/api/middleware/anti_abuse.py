"""Anti-abuse guards: UA filter, spike detection, violation-based IP blocks (§B.9.1)."""

from __future__ import annotations

import threading
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from content_hub_showcase.api.middleware.rate_limit import SlidingWindowLimiter
from content_hub_showcase.api.middleware.session import client_ip
from content_hub_showcase.api.schemas import error_payload
from content_hub_showcase.shared.config import Settings
from content_hub_showcase.shared.logger import get_logger

logger = get_logger(__name__)

# Headless HTTP libraries recruiters would never browse with. Curl is allowed
# so the demo stays testable from a terminal.
_BLOCKED_UA_SUBSTRINGS = ("python-requests", "python-httpx", "scrapy", "go-http-client", "wget")
_MAX_BODY_BYTES = 32 * 1024
_VIOLATION_BLOCK_THRESHOLD = 10
_BLOCK_SECONDS = 3600.0
_SPIKE_LIMIT_PER_MINUTE = 50
_SPIKE_BLOCK_SECONDS = 600.0


class AntiAbuseMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._violations: dict[str, int] = {}
        self._blocked_until: dict[str, float] = {}
        self._spike = SlidingWindowLimiter()
        self._lock = threading.Lock()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if not path.startswith("/api/") or request.method == "OPTIONS":
            return await call_next(request)

        ip = client_ip(request)
        now = time.monotonic()

        with self._lock:
            blocked_until = self._blocked_until.get(ip, 0.0)
        if blocked_until > now:
            return self._forbidden("Access temporarily blocked")

        # Spike detection: 50 req/min per IP → 10-minute block.
        if self._spike.check(f"spike:{ip}", _SPIKE_LIMIT_PER_MINUTE, 60.0) is not None:
            self._block(ip, _SPIKE_BLOCK_SECONDS, reason="spike")
            return self._forbidden("Access temporarily blocked")

        user_agent = request.headers.get("user-agent", "").strip().lower()
        if not user_agent or any(marker in user_agent for marker in _BLOCKED_UA_SUBSTRINGS):
            self._register_violation(ip)
            return self._forbidden("Client not allowed")

        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > _MAX_BODY_BYTES:
            self._register_violation(ip)
            return JSONResponse(
                status_code=400,
                content=error_payload(
                    "validation_error",
                    "Request body too large",
                    {"max_bytes": _MAX_BODY_BYTES},
                ),
            )

        return await call_next(request)

    def _register_violation(self, ip: str) -> None:
        with self._lock:
            self._violations[ip] = self._violations.get(ip, 0) + 1
            count = self._violations[ip]
        if count > _VIOLATION_BLOCK_THRESHOLD:
            self._block(ip, _BLOCK_SECONDS, reason="violations")

    def _block(self, ip: str, seconds: float, *, reason: str) -> None:
        with self._lock:
            self._blocked_until[ip] = time.monotonic() + seconds
        logger.warning("IP temporarily blocked", extra={"context": {"reason": reason}})

    @staticmethod
    def _forbidden(message: str) -> JSONResponse:
        return JSONResponse(status_code=403, content=error_payload("forbidden", message))
