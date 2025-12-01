"""Configuration settings for the Treecko Bot."""

import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from dotenv import load_dotenv

from .authorization import AuthorizationConfig
from .rate_limiter import RateLimitConfig

load_dotenv()

# Validation constants
MIN_PORT = 1
MAX_PORT = 65535
VALID_DATABASE_EXTENSIONS = (".db", ".sqlite", ".sqlite3")

# Default rate limiting values
DEFAULT_RATE_LIMIT_MAX_REQUESTS = 10
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60


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
    rate_limit_config: RateLimitConfig = field(default_factory=RateLimitConfig)
    auth_config: AuthorizationConfig = field(default_factory=AuthorizationConfig)

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

        # Rate limiting configuration
        rate_limit_config = cls._load_rate_limit_config()

        # Authorization configuration
        auth_config = cls._load_auth_config()

        return cls(
            telegram_token=telegram_token,
            google_credentials_path=google_credentials_path,
            google_sheet_id=google_sheet_id,
            database_path=database_path,
            webhook_base_url=webhook_base_url,
            port=port,
            health_check_port=health_check_port,
            rate_limit_config=rate_limit_config,
            auth_config=auth_config,
        )

    @classmethod
    def _load_rate_limit_config(cls) -> RateLimitConfig:
        """Load rate limit configuration from environment variables.

        Returns:
            RateLimitConfig instance.
        """
        enabled_str = os.getenv("RATE_LIMIT_ENABLED", "true").lower()
        enabled = enabled_str in ("true", "1", "yes")

        max_requests_str = os.getenv(
            "RATE_LIMIT_MAX_REQUESTS", str(DEFAULT_RATE_LIMIT_MAX_REQUESTS)
        )
        try:
            max_requests = int(max_requests_str)
            if max_requests < 1:
                max_requests = DEFAULT_RATE_LIMIT_MAX_REQUESTS
        except ValueError:
            max_requests = DEFAULT_RATE_LIMIT_MAX_REQUESTS

        window_seconds_str = os.getenv(
            "RATE_LIMIT_WINDOW_SECONDS", str(DEFAULT_RATE_LIMIT_WINDOW_SECONDS)
        )
        try:
            window_seconds = int(window_seconds_str)
            if window_seconds < 1:
                window_seconds = DEFAULT_RATE_LIMIT_WINDOW_SECONDS
        except ValueError:
            window_seconds = DEFAULT_RATE_LIMIT_WINDOW_SECONDS

        return RateLimitConfig(
            max_requests=max_requests,
            window_seconds=window_seconds,
            enabled=enabled,
        )

    @classmethod
    def _load_auth_config(cls) -> AuthorizationConfig:
        """Load authorization configuration from environment variables.

        Returns:
            AuthorizationConfig instance.
        """
        mode_str = os.getenv("AUTH_MODE", "open")
        admin_ids_str = os.getenv("AUTH_ADMIN_IDS", "")
        whitelist_ids_str = os.getenv("AUTH_WHITELIST_IDS", "")

        return AuthorizationConfig.from_env_values(
            mode_str=mode_str,
            admin_ids_str=admin_ids_str,
            whitelist_ids_str=whitelist_ids_str,
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
