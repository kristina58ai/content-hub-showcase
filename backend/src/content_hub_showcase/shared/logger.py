"""Structured JSON logging to stdout — the only observability mechanism (§B.11, ADR-015)."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Defensive redaction: these keys must never reach logs (§B.11.1).
_REDACTED_KEYS = {
    "api_key",
    "authorization",
    "groq_api_key",
    "openrouter_api_key",
    "redis_url",
    "session_id",
    "x-session-id",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        context = getattr(record, "context", None)
        if isinstance(context, dict):
            payload["context"] = {
                key: ("[redacted]" if str(key).lower() in _REDACTED_KEYS else value)
                for key, value in context.items()
            }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
