"""
Structured logging configuration for Dobeu Undertaker.

Uses structlog for structured JSON logging with support for
both human-readable console output and machine-parseable JSON
for production environments.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor


def setup_logging(
    verbose: bool = False,
    json_output: bool = False,
    log_level: str | None = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        verbose: Enable verbose (DEBUG) logging
        json_output: Output logs as JSON (for production)
        log_level: Explicit log level (overrides verbose flag)
    """
    # Determine log level
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level,
    )

    # Shared processors for all outputs
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        # JSON output for production/CI
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Pretty console output for development
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_with_context(**context: Any) -> structlog.contextvars.bound_contextvars:
    """
    Context manager to add context to all log messages.

    Usage:
        with log_with_context(repo="my-repo", scan_id="abc123"):
            logger.info("Scanning repository")
            # All logs within this block include repo and scan_id

    Args:
        **context: Key-value pairs to add to log context

    Returns:
        Context manager that adds/removes context
    """
    return structlog.contextvars.bound_contextvars(**context)


class LogCapture:
    """
    Capture log messages for testing or reporting.

    Usage:
        capture = LogCapture()
        with capture:
            logger.info("Test message")
        print(capture.messages)  # [{"event": "Test message", ...}]
    """

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []
        self._old_processors: list[Processor] | None = None

    def __enter__(self) -> "LogCapture":
        # Store current config and add capture processor
        config = structlog.get_config()
        self._old_processors = list(config.get("processors", []))

        new_processors = self._old_processors.copy()
        # Insert capture processor before the renderer
        new_processors.insert(-1, self._capture_processor)

        structlog.configure(processors=new_processors)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._old_processors is not None:
            structlog.configure(processors=self._old_processors)

    def _capture_processor(
        self,
        logger: Any,
        method_name: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        """Processor that captures log events."""
        self.messages.append(event_dict.copy())
        return event_dict
