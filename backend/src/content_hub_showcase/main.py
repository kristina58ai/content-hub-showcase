"""Content-hub Showcase — FastAPI entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from content_hub_showcase.api.errors import register_error_handlers
from content_hub_showcase.api.middleware.anti_abuse import AntiAbuseMiddleware
from content_hub_showcase.api.middleware.cors import add_cors
from content_hub_showcase.api.middleware.rate_limit import RateLimitMiddleware
from content_hub_showcase.api.middleware.session import SessionMiddleware
from content_hub_showcase.api.routes import (
    archetypes,
    generations,
    health,
    ingest,
    learning,
    plans,
)
from content_hub_showcase.shared.config import get_settings, validate_strict_msgpack
from content_hub_showcase.shared.logger import configure_logging, get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    validate_strict_msgpack()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Showcase backend started",
            extra={"context": {"version": settings.app_version}},
        )
        yield

    app = FastAPI(
        title="Content-hub Showcase",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # Starlette runs the LAST added middleware FIRST. Execution order:
    # CORS → anti-abuse (cheapest reject) → session (sets state) → rate-limit.
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(SessionMiddleware, settings=settings)
    app.add_middleware(AntiAbuseMiddleware, settings=settings)
    add_cors(app, settings)

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(archetypes.router, prefix="/api/v1")
    app.include_router(generations.router, prefix="/api/v1")
    app.include_router(plans.router, prefix="/api/v1")
    app.include_router(learning.router, prefix="/api/v1")
    app.include_router(ingest.router, prefix="/api/v1")
    register_error_handlers(app)
    return app


app = create_app()
