"""Logging configuration using structlog"""

import logging
import sys
from typing import Any

import structlog

from mcp_server.config import settings

_configured = False


def setup_logging() -> None:
    """Configure structlog for the application"""
    global _configured
    if _configured:
        return

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Configure structlog processors
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.LOG_FORMAT == "json":
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Disable colors to avoid ANSI escape codes in MCP stdio communication
        shared_processors.append(
            structlog.dev.ConsoleRenderer(colors=False)
        )

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        context_class=dict,
        # CRITICAL: Use stderr to avoid polluting MCP's stdout JSON communication
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    _configured = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a logger instance"""
    if not _configured:
        setup_logging()
    return structlog.get_logger(name)


# Default logger
logger = get_logger()
