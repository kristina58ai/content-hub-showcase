"""Anonymous session tracking: X-Session-Id UUID with hashed-IP fallback (ADR-012)."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from content_hub_showcase.shared.config import Settings
from content_hub_showcase.shared.db import connect, utc_now_iso
from content_hub_showcase.shared.logger import get_logger

logger = get_logger(__name__)

_UNTRACKED_PATHS = {"/api/v1/health", "/api/v1/version"}


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def hashed_ip(ip: str) -> str:
    """Partial hash only — raw IPs are never stored or logged (§B.11.1)."""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


def resolve_session_id(request: Request) -> str:
    header = request.headers.get("x-session-id", "").strip()
    if header:
        try:
            return str(uuid.UUID(header))
        except ValueError:
            pass
    return f"ip-{hashed_ip(client_ip(request))}"


class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not request.url.path.startswith("/api/") or request.url.path in _UNTRACKED_PATHS:
            return await call_next(request)

        session_id = resolve_session_id(request)
        request.state.session_id = session_id
        self._track_visitor(request, session_id)
        return await call_next(request)

    def _track_visitor(self, request: Request, session_id: str) -> None:
        now = utc_now_iso()
        try:
            with connect(self._settings.showcase_db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO demo_visitors
                        (session_id, ip_address, user_agent, started_at, last_activity)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET last_activity = excluded.last_activity
                    """,
                    (
                        session_id,
                        hashed_ip(client_ip(request)),
                        request.headers.get("user-agent", "")[:300],
                        now,
                        now,
                    ),
                )
        except sqlite3.OperationalError as exc:
            # Missing table = migrations not applied; demo must not 500 over tracking.
            logger.warning(
                "Visitor tracking unavailable",
                extra={"context": {"error": str(exc)}},
            )
