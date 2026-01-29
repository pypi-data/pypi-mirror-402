"""Structured logging configuration for DataCheck API.

Provides JSON-formatted logging for production environments with proper
log levels, correlation IDs, and sensitive data filtering.
"""

import logging
import sys
import json
import uuid
from datetime import datetime
from typing import Any
from contextvars import ContextVar

# Context variable for request correlation ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Formats log records as JSON with standard fields for easy parsing
    by log aggregation systems (ELK, Splunk, CloudWatch, etc.).
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Build base log entry
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development.

    Uses colored output and readable format for local development.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            Colored log string
        """
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Build log line
        log_line = f"{color}{record.levelname:8s}{reset} {timestamp} [{record.name}] {record.getMessage()}"

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_line += f" [request_id={request_id}]"

        # Add exception if present
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)

        return log_line


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    logger_name: str = "datacheck",
) -> logging.Logger:
    """Setup application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON format (True for production, False for development)
        logger_name: Name of the logger to configure

    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Set formatter based on format preference
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Name of the logger (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"datacheck.{name}")


def set_request_id(request_id: str | None = None) -> str:
    """Set request ID for current context.

    Args:
        request_id: Request ID to set, or None to generate new one

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> str:
    """Get current request ID.

    Returns:
        Current request ID or empty string
    """
    return request_id_var.get()


def log_with_extra(logger: logging.Logger, level: str, message: str, **extra: Any) -> None:
    """Log message with extra fields.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **extra: Extra fields to include in log
    """
    # Create log record
    log_method = getattr(logger, level.lower())

    # Add extra fields to record
    record = logging.LogRecord(
        name=logger.name,
        level=getattr(logging, level.upper()),
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.extra_fields = extra

    log_method(message, extra=extra)


__all__ = [
    "setup_logging",
    "get_logger",
    "set_request_id",
    "get_request_id",
    "log_with_extra",
    "JSONFormatter",
    "TextFormatter",
]
