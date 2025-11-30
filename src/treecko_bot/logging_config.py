"""Logging configuration for the Treecko Bot."""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

# Log level environment variable
LOG_LEVEL_ENV = "LOG_LEVEL"
LOG_FORMAT_ENV = "LOG_FORMAT"

# Valid log levels
VALID_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Log formats
LOG_FORMAT_TEXT = "text"
LOG_FORMAT_JSON = "json"


class StructuredJsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON formatted log string.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if any
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Add source location in debug mode
        if record.levelno <= logging.DEBUG:
            log_data["source"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data, ensure_ascii=False)


class StructuredTextFormatter(logging.Formatter):
    """Enhanced text formatter with structured context."""

    def __init__(self):
        """Initialize the text formatter."""
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as enhanced text.

        Args:
            record: The log record to format.

        Returns:
            Formatted log string.
        """
        formatted = super().format(record)

        # Add extra fields if any
        if hasattr(record, "extra_data") and record.extra_data:
            extra_str = " ".join(f"{k}={v}" for k, v in record.extra_data.items())
            formatted = f"{formatted} | {extra_str}"

        return formatted


class StructuredLogger(logging.Logger):
    """Logger with support for structured extra data."""

    def _log_with_extra(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info: Any = None,
        extra: dict[str, Any] | None = None,
        stack_info: bool = False,
        stacklevel: int = 1,
        **kwargs: Any,
    ) -> None:
        """Log with extra structured data.

        Args:
            level: Log level.
            msg: Log message.
            args: Message arguments.
            exc_info: Exception info.
            extra: Extra data to include.
            stack_info: Whether to include stack info.
            stacklevel: Stack level for determining source.
            **kwargs: Additional keyword arguments for structured data.
        """
        # Merge extra dict with kwargs for structured data
        extra_data = {}
        if extra:
            extra_data.update(extra)
        extra_data.update(kwargs)

        # Create extra dict for log record
        record_extra = {"extra_data": extra_data} if extra_data else {}

        super()._log(
            level,
            msg,
            args,
            exc_info=exc_info,
            extra=record_extra,
            stack_info=stack_info,
            stacklevel=stacklevel + 1,
        )

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log debug message with optional extra data."""
        if self.isEnabledFor(logging.DEBUG):
            self._log_with_extra(logging.DEBUG, msg, args, stacklevel=2, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log info message with optional extra data."""
        if self.isEnabledFor(logging.INFO):
            self._log_with_extra(logging.INFO, msg, args, stacklevel=2, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log warning message with optional extra data."""
        if self.isEnabledFor(logging.WARNING):
            self._log_with_extra(logging.WARNING, msg, args, stacklevel=2, **kwargs)

    def error(self, msg: str, *args: Any, exc_info: Any = None, **kwargs: Any) -> None:
        """Log error message with optional extra data."""
        if self.isEnabledFor(logging.ERROR):
            self._log_with_extra(
                logging.ERROR, msg, args, exc_info=exc_info, stacklevel=2, **kwargs
            )

    def critical(self, msg: str, *args: Any, exc_info: Any = None, **kwargs: Any) -> None:
        """Log critical message with optional extra data."""
        if self.isEnabledFor(logging.CRITICAL):
            self._log_with_extra(
                logging.CRITICAL, msg, args, exc_info=exc_info, stacklevel=2, **kwargs
            )


def get_log_level() -> int:
    """Get log level from environment variable.

    Returns:
        The logging level as an integer.
    """
    level_name = os.getenv(LOG_LEVEL_ENV, "INFO").upper()
    return VALID_LOG_LEVELS.get(level_name, logging.INFO)


def get_log_format() -> str:
    """Get log format from environment variable.

    Returns:
        The log format name ('text' or 'json').
    """
    format_name = os.getenv(LOG_FORMAT_ENV, LOG_FORMAT_TEXT).lower()
    if format_name not in (LOG_FORMAT_TEXT, LOG_FORMAT_JSON):
        return LOG_FORMAT_TEXT
    return format_name


def setup_logging() -> None:
    """Configure logging for the application.

    Sets up logging with configurable level and format based on
    environment variables:
    - LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    - LOG_FORMAT: text, json (default: text)
    """
    # Register our custom logger class
    logging.setLoggerClass(StructuredLogger)

    # Get configuration from environment
    log_level = get_log_level()
    log_format = get_log_format()

    # Create appropriate formatter
    if log_format == LOG_FORMAT_JSON:
        formatter = StructuredJsonFormatter()
    else:
        formatter = StructuredTextFormatter()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Log initial configuration at debug level
    logger = logging.getLogger(__name__)
    logger.debug(
        "Logging configured",
        level=logging.getLevelName(log_level),
        format=log_format,
    )


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__).

    Returns:
        StructuredLogger instance.
    """
    return logging.getLogger(name)  # type: ignore[return-value]
