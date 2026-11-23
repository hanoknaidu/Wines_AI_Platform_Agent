"""Structured logging: JSON lines (or pretty console locally), every line tagged
with the request ID. PII redaction runs as a processor, so a stray email in a
log call is masked before it leaves the process."""
from __future__ import annotations

import logging
import sys

import structlog

from app.core.masking import redact_text
from app.core.request_context import get_request_id


def _add_request_id(_, __, event_dict):
    rid = get_request_id()
    if rid and "request_id" not in event_dict:
        event_dict["request_id"] = rid
    return event_dict


def _redact(_, __, event_dict):
    for key, value in list(event_dict.items()):
        if isinstance(value, str) and key not in {"timestamp", "level", "logger", "request_id"}:
            event_dict[key] = redact_text(value)
    return event_dict


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_request_id,
        _redact,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer = structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
    structlog.configure(
        processors=[*processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(level=level.upper(), stream=sys.stdout, format="%(message)s")
    for noisy in ("httpx", "httpcore", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
