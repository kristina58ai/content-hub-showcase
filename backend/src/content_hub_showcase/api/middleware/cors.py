"""CORS restricted to the Vercel deployment + localhost dev (§B.9.1)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from content_hub_showcase.shared.config import Settings


def add_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Session-Id"],
        max_age=600,
    )
