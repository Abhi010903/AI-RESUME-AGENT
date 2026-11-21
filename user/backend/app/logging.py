"""Structured logging configuration with JSON and text formatters."""

from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import sys
from typing import Any
from app.config import Settings

# Context variable to hold request correlation ID across async execution contexts
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class JSONLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include request ID from record attribute or context variable
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()
        if req_id:
            log_payload["request_id"] = req_id

        if record.exc_info and record.exc_info[0] is not None:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload, default=str)


class TextLogFormatter(logging.Formatter):
    """Human-readable text log formatter for development."""

    DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    def __init__(self) -> None:
        super().__init__(fmt=self.DEFAULT_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")


def setup_logging(settings: Settings) -> logging.Logger:
    """Configure root and application loggers based on settings."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level)

    if settings.log_json:
        handler.setFormatter(JSONLogFormatter())
    else:
        handler.setFormatter(TextLogFormatter())

    root_logger.addHandler(handler)

    # Silence overly verbose third-party loggers if needed
    logging.getLogger("uvicorn.access").handlers = [handler]

    logger = logging.getLogger("app")
    logger.info(
        "Logging configured",
        extra={"env": settings.env, "level": settings.log_level},
    )
    return logger
