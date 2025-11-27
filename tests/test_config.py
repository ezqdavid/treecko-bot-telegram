"""Tests for the configuration module."""

import os

import pytest

from treecko_bot.config import Config, get_config


def test_config_from_env():
    """Test loading configuration from environment variables."""
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
    os.environ["GOOGLE_SHEET_ID"] = "test_sheet_id"
    os.environ["DATABASE_PATH"] = "test.db"

    config = Config.from_env()

    assert config.telegram_token == "test_token"
    assert config.google_sheet_id == "test_sheet_id"
    assert config.database_path == "test.db"

    # Clean up
    del os.environ["TELEGRAM_BOT_TOKEN"]
    del os.environ["GOOGLE_SHEET_ID"]
    del os.environ["DATABASE_PATH"]


def test_config_missing_token():
    """Test that missing token raises ValueError."""
    if "TELEGRAM_BOT_TOKEN" in os.environ:
        del os.environ["TELEGRAM_BOT_TOKEN"]

    with pytest.raises(ValueError):
        Config.from_env()


def test_config_defaults():
    """Test default configuration values."""
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"

    config = Config.from_env()

    assert config.google_credentials_path == "credentials.json"
    assert config.database_path == "transactions.db"

    # Clean up
    del os.environ["TELEGRAM_BOT_TOKEN"]
