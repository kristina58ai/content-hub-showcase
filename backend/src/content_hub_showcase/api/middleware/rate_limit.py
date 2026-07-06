"""Per-IP / per-session rate limiting with in-memory sliding windows (§B.7.6).

Limits: 5 generations/hour per IP; 100 reads/hour per IP; 20 archetype
switches/hour per session UUID. The 3-concurrent-generations guard lives in
the generations service (it must decrement when a run finishes, which a
request-scoped middleware cannot observe).
"""

from __future__ import annotations

import re
import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from content_hub_showcase.api.middleware.session import client_ip, resolve_session_id
from content_hub_showcase.api.schemas import error_payload
from content_hub_showcase.shared.config import Settings

_ARCHETYPE_DETAIL_RE = re.compile(r"^/api/v1/archetypes/[^/]+$")
_SKIP_PATHS = {"/api/v1/health", "/api/v1/version"}
_WINDOW_SECONDS = 3600.0


class SlidingWindowLimiter:
    """Thread-safe sliding-window counter keyed by arbitrary strings."""

    def __init__(self, now: Callable[[], float] = time.monotonic) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._now = now

    def check(self, key: str, limit: int, window_seconds: float = _WINDOW_SECONDS) -> int | None:
        """Register a hit; return None if allowed, else retry-after seconds."""
        now = self._now()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] > window_seconds:
                events.popleft()
            if len(events) >= limit:
                return max(1, int(window_seconds - (now - events[0])) + 1)
            events.append(now)
            return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        settings: Settings,
        limiter: SlidingWindowLimiter | None = None,
    ) -> None:
        super().__init__(app)
        self._settings = settings
        self._limiter = limiter or SlidingWindowLimiter()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if not path.startswith("/api/") or path in _SKIP_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        ip = client_ip(request)
        verdict: tuple[int | None, str] = (None, "")

        if request.method == "POST" and path.rstrip("/").endswith("/generations"):
            verdict = (
                self._limiter.check(f"gen:{ip}", self._settings.rate_limit_generations_per_hour),
                "generations_per_hour",
            )
        elif request.method == "GET" and _ARCHETYPE_DETAIL_RE.match(path):
            session_id = resolve_session_id(request)
            verdict = (
                self._limiter.check(
                    f"arch:{session_id}",
                    self._settings.rate_limit_archetype_switches_per_hour,
                ),
                "archetype_switches_per_hour",
            )
        elif request.method == "GET":
            verdict = (
                self._limiter.check(f"read:{ip}", self._settings.rate_limit_reads_per_hour),
                "reads_per_hour",
            )

        retry_after, limit_type = verdict
        if retry_after is not None:
            return JSONResponse(
                status_code=429,
                content=error_payload(
                    "rate_limit_exceeded",
                    f"Slow down — try again in {retry_after} seconds",
                    {"retry_after_seconds": retry_after, "limit_type": limit_type},
                ),
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
