"""Configuration settings for the Treecko Bot."""

import os
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

# Validation constants
MIN_PORT = 1
MAX_PORT = 65535
VALID_DATABASE_EXTENSIONS = (".db", ".sqlite", ".sqlite3")


@dataclass
class Config:
    """Bot configuration."""

    telegram_token: str
    google_credentials_path: str
    google_sheet_id: str
    database_path: str
    webhook_base_url: str
    port: int
    health_check_port: int

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        # Validate token format (basic check for non-empty alphanumeric with colons)
        cls._validate_telegram_token(telegram_token)

        google_credentials_path = os.getenv(
            "GOOGLE_CREDENTIALS_PATH", "credentials.json"
        )
        google_sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        database_path = os.getenv("DATABASE_PATH", "transactions.db")
        webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "")

        # Validate webhook URL if provided
        if webhook_base_url:
            cls._validate_webhook_url(webhook_base_url)

        # Validate database path
        cls._validate_database_path(database_path)

        port_str = os.getenv("PORT", "8080")
        try:
            port = int(port_str)
        except ValueError as e:
            raise ValueError(f"PORT must be a valid integer, got: {port_str}") from e

        # Validate port range
        cls._validate_port(port)

        # Health check port (defaults to 8081)
        health_check_port_str = os.getenv("HEALTH_CHECK_PORT", "8081")
        try:
            health_check_port = int(health_check_port_str)
        except ValueError as e:
            raise ValueError(
                f"HEALTH_CHECK_PORT must be a valid integer, got: {health_check_port_str}"
            ) from e

        # Validate health check port range
        cls._validate_port(health_check_port, "HEALTH_CHECK_PORT")

        return cls(
            telegram_token=telegram_token,
            google_credentials_path=google_credentials_path,
            google_sheet_id=google_sheet_id,
            database_path=database_path,
            webhook_base_url=webhook_base_url,
            port=port,
            health_check_port=health_check_port,
        )

    @staticmethod
    def _validate_telegram_token(token: str) -> None:
        """Validate Telegram bot token format.

        Args:
            token: The Telegram bot token to validate.

        Raises:
            ValueError: If the token format is invalid.
        """
        # Telegram tokens have format: <bot_id>:<hash>
        # bot_id is numeric, hash is alphanumeric with underscores
        if not re.match(r"^\d+:[A-Za-z0-9_-]+$", token):
            raise ValueError(
                "TELEGRAM_BOT_TOKEN format is invalid. "
                "Expected format: <bot_id>:<hash>"
            )

    @staticmethod
    def _validate_webhook_url(url: str) -> None:
        """Validate webhook URL format.

        Args:
            url: The webhook URL to validate.

        Raises:
            ValueError: If the URL format is invalid.
        """
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"WEBHOOK_BASE_URL must use http or https scheme, got: {parsed.scheme or 'none'}"
            )

        if not parsed.netloc:
            raise ValueError("WEBHOOK_BASE_URL must have a valid hostname")

        # Webhook URL should not have a trailing slash
        if url.endswith("/"):
            raise ValueError("WEBHOOK_BASE_URL should not end with a trailing slash")

    @staticmethod
    def _validate_port(port: int, var_name: str = "PORT") -> None:
        """Validate port number is in valid range.

        Args:
            port: The port number to validate.
            var_name: The variable name to use in error messages.

        Raises:
            ValueError: If the port is out of valid range.
        """
        if not MIN_PORT <= port <= MAX_PORT:
            raise ValueError(
                f"{var_name} must be between {MIN_PORT} and {MAX_PORT}, got: {port}"
            )

    @staticmethod
    def _validate_database_path(path: str) -> None:
        """Validate database path has valid extension.

        Args:
            path: The database file path to validate.

        Raises:
            ValueError: If the path extension is invalid.
        """
        if not path.lower().endswith(VALID_DATABASE_EXTENSIONS):
            raise ValueError(
                f"DATABASE_PATH must end with one of {VALID_DATABASE_EXTENSIONS}, got: {path}"
            )


def get_config() -> Config:
    """Get the application configuration."""
    return Config.from_env()
