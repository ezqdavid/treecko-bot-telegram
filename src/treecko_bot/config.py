"""Configuration settings for the Treecko Bot."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Bot configuration."""

    telegram_token: str
    google_credentials_path: str
    google_sheet_id: str
    database_path: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        google_credentials_path = os.getenv(
            "GOOGLE_CREDENTIALS_PATH", "credentials.json"
        )
        google_sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        database_path = os.getenv("DATABASE_PATH", "transactions.db")

        return cls(
            telegram_token=telegram_token,
            google_credentials_path=google_credentials_path,
            google_sheet_id=google_sheet_id,
            database_path=database_path,
        )


def get_config() -> Config:
    """Get the application configuration."""
    return Config.from_env()
