"""Tests for the configuration module."""

import os

import pytest

from treecko_bot.config import Config

# Valid test token that matches the expected format: <bot_id>:<hash>
VALID_TEST_TOKEN = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ_0123456"


def test_config_from_env():
    """Test loading configuration from environment variables."""
    os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
    os.environ["GOOGLE_SHEET_ID"] = "test_sheet_id"
    os.environ["DATABASE_PATH"] = "test.db"
    os.environ["WEBHOOK_BASE_URL"] = "https://test.example.com"
    os.environ["PORT"] = "9000"

    config = Config.from_env()

    assert config.telegram_token == VALID_TEST_TOKEN
    assert config.google_sheet_id == "test_sheet_id"
    assert config.database_path == "test.db"
    assert config.webhook_base_url == "https://test.example.com"
    assert config.port == 9000

    # Clean up
    del os.environ["TELEGRAM_BOT_TOKEN"]
    del os.environ["GOOGLE_SHEET_ID"]
    del os.environ["DATABASE_PATH"]
    del os.environ["WEBHOOK_BASE_URL"]
    del os.environ["PORT"]


def test_config_missing_token():
    """Test that missing token raises ValueError."""
    if "TELEGRAM_BOT_TOKEN" in os.environ:
        del os.environ["TELEGRAM_BOT_TOKEN"]

    with pytest.raises(ValueError):
        Config.from_env()


def test_config_defaults():
    """Test default configuration values."""
    os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
    # Ensure webhook-related vars are not set
    if "WEBHOOK_BASE_URL" in os.environ:
        del os.environ["WEBHOOK_BASE_URL"]
    if "PORT" in os.environ:
        del os.environ["PORT"]

    config = Config.from_env()

    assert config.google_credentials_path == "credentials.json"
    assert config.database_path == "transactions.db"
    assert config.webhook_base_url == ""
    assert config.port == 8080

    # Clean up
    del os.environ["TELEGRAM_BOT_TOKEN"]


def test_config_invalid_port():
    """Test that invalid PORT raises ValueError with helpful message."""
    os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
    os.environ["PORT"] = "not_a_number"

    with pytest.raises(ValueError, match="PORT must be a valid integer"):
        Config.from_env()

    # Clean up
    del os.environ["TELEGRAM_BOT_TOKEN"]
    del os.environ["PORT"]


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_invalid_telegram_token_format(self):
        """Test that invalid token format raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = "invalid_token"

        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN format is invalid"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]

    def test_telegram_token_without_colon(self):
        """Test that token without colon raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = "123456789ABCdefGHI"

        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN format is invalid"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]

    def test_telegram_token_with_non_numeric_bot_id(self):
        """Test that token with non-numeric bot ID raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = "abc:ABCdefGHI"

        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN format is invalid"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]

    def test_valid_webhook_url_http(self):
        """Test that valid http URL is accepted."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["WEBHOOK_BASE_URL"] = "http://localhost:8080"

        config = Config.from_env()
        assert config.webhook_base_url == "http://localhost:8080"

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["WEBHOOK_BASE_URL"]

    def test_valid_webhook_url_https(self):
        """Test that valid https URL is accepted."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["WEBHOOK_BASE_URL"] = "https://api.example.com"

        config = Config.from_env()
        assert config.webhook_base_url == "https://api.example.com"

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["WEBHOOK_BASE_URL"]

    def test_invalid_webhook_url_scheme(self):
        """Test that invalid URL scheme raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["WEBHOOK_BASE_URL"] = "ftp://example.com"

        with pytest.raises(ValueError, match="must use http or https scheme"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["WEBHOOK_BASE_URL"]

    def test_invalid_webhook_url_no_host(self):
        """Test that URL without hostname raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["WEBHOOK_BASE_URL"] = "https://"

        with pytest.raises(ValueError, match="must have a valid hostname"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["WEBHOOK_BASE_URL"]

    def test_webhook_url_with_trailing_slash(self):
        """Test that URL with trailing slash raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["WEBHOOK_BASE_URL"] = "https://example.com/"

        with pytest.raises(ValueError, match="should not end with a trailing slash"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["WEBHOOK_BASE_URL"]

    def test_port_below_minimum(self):
        """Test that port below 1 raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["PORT"] = "0"

        with pytest.raises(ValueError, match="PORT must be between 1 and 65535"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["PORT"]

    def test_port_above_maximum(self):
        """Test that port above 65535 raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["PORT"] = "65536"

        with pytest.raises(ValueError, match="PORT must be between 1 and 65535"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["PORT"]

    def test_valid_port_boundary_min(self):
        """Test that minimum port (1) is accepted."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["PORT"] = "1"

        config = Config.from_env()
        assert config.port == 1

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["PORT"]

    def test_valid_port_boundary_max(self):
        """Test that maximum port (65535) is accepted."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["PORT"] = "65535"

        config = Config.from_env()
        assert config.port == 65535

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["PORT"]

    def test_invalid_database_path_extension(self):
        """Test that invalid database extension raises ValueError."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["DATABASE_PATH"] = "data.txt"

        with pytest.raises(ValueError, match="DATABASE_PATH must end with one of"):
            Config.from_env()

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["DATABASE_PATH"]

    def test_valid_database_path_db(self):
        """Test that .db extension is accepted."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["DATABASE_PATH"] = "mydata.db"

        config = Config.from_env()
        assert config.database_path == "mydata.db"

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["DATABASE_PATH"]

    def test_valid_database_path_sqlite(self):
        """Test that .sqlite extension is accepted."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["DATABASE_PATH"] = "mydata.sqlite"

        config = Config.from_env()
        assert config.database_path == "mydata.sqlite"

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["DATABASE_PATH"]

    def test_valid_database_path_sqlite3(self):
        """Test that .sqlite3 extension is accepted."""
        os.environ["TELEGRAM_BOT_TOKEN"] = VALID_TEST_TOKEN
        os.environ["DATABASE_PATH"] = "mydata.sqlite3"

        config = Config.from_env()
        assert config.database_path == "mydata.sqlite3"

        del os.environ["TELEGRAM_BOT_TOKEN"]
        del os.environ["DATABASE_PATH"]
