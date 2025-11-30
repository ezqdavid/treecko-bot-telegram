"""Tests for the logging configuration module."""

import json
import logging
import os

import pytest

from treecko_bot.logging_config import (
    LOG_FORMAT_ENV,
    LOG_FORMAT_JSON,
    LOG_FORMAT_TEXT,
    LOG_LEVEL_ENV,
    StructuredJsonFormatter,
    StructuredTextFormatter,
    get_log_format,
    get_log_level,
    get_logger,
    setup_logging,
)


class TestGetLogLevel:
    """Tests for get_log_level function."""

    def test_default_level_is_info(self):
        """Test that default log level is INFO."""
        if LOG_LEVEL_ENV in os.environ:
            del os.environ[LOG_LEVEL_ENV]

        assert get_log_level() == logging.INFO

    def test_debug_level(self):
        """Test DEBUG level from environment."""
        os.environ[LOG_LEVEL_ENV] = "DEBUG"
        try:
            assert get_log_level() == logging.DEBUG
        finally:
            del os.environ[LOG_LEVEL_ENV]

    def test_warning_level(self):
        """Test WARNING level from environment."""
        os.environ[LOG_LEVEL_ENV] = "WARNING"
        try:
            assert get_log_level() == logging.WARNING
        finally:
            del os.environ[LOG_LEVEL_ENV]

    def test_error_level(self):
        """Test ERROR level from environment."""
        os.environ[LOG_LEVEL_ENV] = "error"  # lowercase should work
        try:
            assert get_log_level() == logging.ERROR
        finally:
            del os.environ[LOG_LEVEL_ENV]

    def test_critical_level(self):
        """Test CRITICAL level from environment."""
        os.environ[LOG_LEVEL_ENV] = "CRITICAL"
        try:
            assert get_log_level() == logging.CRITICAL
        finally:
            del os.environ[LOG_LEVEL_ENV]

    def test_invalid_level_defaults_to_info(self):
        """Test that invalid level defaults to INFO."""
        os.environ[LOG_LEVEL_ENV] = "INVALID"
        try:
            assert get_log_level() == logging.INFO
        finally:
            del os.environ[LOG_LEVEL_ENV]


class TestGetLogFormat:
    """Tests for get_log_format function."""

    def test_default_format_is_text(self):
        """Test that default log format is text."""
        if LOG_FORMAT_ENV in os.environ:
            del os.environ[LOG_FORMAT_ENV]

        assert get_log_format() == LOG_FORMAT_TEXT

    def test_json_format(self):
        """Test JSON format from environment."""
        os.environ[LOG_FORMAT_ENV] = "json"
        try:
            assert get_log_format() == LOG_FORMAT_JSON
        finally:
            del os.environ[LOG_FORMAT_ENV]

    def test_text_format(self):
        """Test text format from environment."""
        os.environ[LOG_FORMAT_ENV] = "TEXT"  # uppercase should work
        try:
            assert get_log_format() == LOG_FORMAT_TEXT
        finally:
            del os.environ[LOG_FORMAT_ENV]

    def test_invalid_format_defaults_to_text(self):
        """Test that invalid format defaults to text."""
        os.environ[LOG_FORMAT_ENV] = "invalid"
        try:
            assert get_log_format() == LOG_FORMAT_TEXT
        finally:
            del os.environ[LOG_FORMAT_ENV]


class TestStructuredJsonFormatter:
    """Tests for StructuredJsonFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create a JSON formatter instance."""
        return StructuredJsonFormatter()

    @pytest.fixture
    def log_record(self):
        """Create a basic log record."""
        return logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

    def test_format_basic_message(self, formatter, log_record):
        """Test formatting a basic message."""
        output = formatter.format(log_record)
        data = json.loads(output)

        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"

    def test_format_with_extra_data(self, formatter):
        """Test formatting with extra data."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"user_id": 123, "action": "login"}

        output = formatter.format(record)
        data = json.loads(output)

        assert "extra" in data
        assert data["extra"]["user_id"] == 123
        assert data["extra"]["action"] == "login"

    def test_format_debug_includes_source(self, formatter):
        """Test that debug messages include source location."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=10,
            msg="Debug message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert "source" in data
        assert data["source"]["file"] == "test.py"
        assert data["source"]["line"] == 10


class TestStructuredTextFormatter:
    """Tests for StructuredTextFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create a text formatter instance."""
        return StructuredTextFormatter()

    def test_format_basic_message(self, formatter):
        """Test formatting a basic message."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "test.logger" in output
        assert "INFO" in output
        assert "Test message" in output

    def test_format_with_extra_data(self, formatter):
        """Test formatting with extra data."""
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"user_id": 123, "action": "login"}

        output = formatter.format(record)

        assert "user_id=123" in output
        assert "action=login" in output


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_configures_root_logger(self):
        """Test that setup_logging configures the root logger."""
        # Clean up any existing handlers
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        setup_logging()

        # Root logger should have at least one handler
        assert len(root.handlers) > 0

    def test_setup_logging_with_json_format(self):
        """Test setup_logging with JSON format."""
        os.environ[LOG_FORMAT_ENV] = "json"
        try:
            root = logging.getLogger()
            for handler in root.handlers[:]:
                root.removeHandler(handler)

            setup_logging()

            # Check that JSON formatter is used
            handler = root.handlers[0]
            assert isinstance(handler.formatter, StructuredJsonFormatter)
        finally:
            del os.environ[LOG_FORMAT_ENV]

    def test_setup_logging_with_text_format(self):
        """Test setup_logging with text format."""
        if LOG_FORMAT_ENV in os.environ:
            del os.environ[LOG_FORMAT_ENV]

        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

        setup_logging()

        # Check that text formatter is used
        handler = root.handlers[0]
        assert isinstance(handler.formatter, StructuredTextFormatter)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test.module")
        assert logger is not None
        assert logger.name == "test.module"

    def test_get_logger_same_name_returns_same_logger(self):
        """Test that getting the same logger name returns the same instance."""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")
        assert logger1 is logger2
