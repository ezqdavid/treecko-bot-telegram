"""User authorization functionality for the Telegram bot."""

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AuthorizationMode(Enum):
    """Authorization modes for the bot.

    Attributes:
        OPEN: Allow all users (no restrictions).
        WHITELIST: Only allow users in the whitelist.
        ADMIN_ONLY: Only allow admin users.
    """

    OPEN = "open"
    WHITELIST = "whitelist"
    ADMIN_ONLY = "admin_only"


@dataclass
class AuthorizationConfig:
    """Configuration for user authorization.

    Attributes:
        mode: The authorization mode to use.
        admin_user_ids: Set of Telegram user IDs that are admins.
        whitelisted_user_ids: Set of Telegram user IDs that are whitelisted.
        enabled: Whether authorization is enabled.
    """

    mode: AuthorizationMode = AuthorizationMode.OPEN
    admin_user_ids: set[int] = field(default_factory=set)
    whitelisted_user_ids: set[int] = field(default_factory=set)
    enabled: bool = True

    @classmethod
    def from_env_values(
        cls,
        mode_str: str | None = None,
        admin_ids_str: str | None = None,
        whitelist_ids_str: str | None = None,
    ) -> "AuthorizationConfig":
        """Create config from environment variable values.

        Args:
            mode_str: Authorization mode string ("open", "whitelist", "admin_only").
            admin_ids_str: Comma-separated string of admin user IDs.
            whitelist_ids_str: Comma-separated string of whitelisted user IDs.

        Returns:
            AuthorizationConfig instance.
        """
        # Parse mode
        mode = AuthorizationMode.OPEN
        if mode_str:
            mode_str_lower = mode_str.lower().strip()
            for m in AuthorizationMode:
                if m.value == mode_str_lower:
                    mode = m
                    break

        # Parse admin IDs
        admin_ids: set[int] = set()
        if admin_ids_str:
            for id_str in admin_ids_str.split(","):
                id_str = id_str.strip()
                if id_str.isdigit() and int(id_str) > 0:
                    admin_ids.add(int(id_str))

        # Parse whitelist IDs
        whitelist_ids: set[int] = set()
        if whitelist_ids_str:
            for id_str in whitelist_ids_str.split(","):
                id_str = id_str.strip()
                if id_str.isdigit() and int(id_str) > 0:
                    whitelist_ids.add(int(id_str))

        # Enable authorization if not in OPEN mode
        enabled = mode != AuthorizationMode.OPEN

        return cls(
            mode=mode,
            admin_user_ids=admin_ids,
            whitelisted_user_ids=whitelist_ids,
            enabled=enabled,
        )


class UserAuthorization:
    """User authorization manager for the bot.

    Controls access to bot functionality based on user IDs and
    authorization mode.
    """

    def __init__(self, config: AuthorizationConfig | None = None) -> None:
        """Initialize the authorization manager.

        Args:
            config: Authorization configuration. Uses defaults if not provided.
        """
        self.config = config or AuthorizationConfig()

    def is_authorized(self, user_id: int) -> bool:
        """Check if a user is authorized to use the bot.

        Args:
            user_id: The Telegram user ID to check.

        Returns:
            True if the user is authorized, False otherwise.
        """
        if not self.config.enabled:
            return True

        if self.config.mode == AuthorizationMode.OPEN:
            return True

        if self.config.mode == AuthorizationMode.ADMIN_ONLY:
            is_admin = user_id in self.config.admin_user_ids
            if not is_admin:
                logger.warning(
                    "Unauthorized user (admin_only mode) user_id=%d",
                    user_id,
                )
            return is_admin

        if self.config.mode == AuthorizationMode.WHITELIST:
            is_whitelisted = (
                user_id in self.config.whitelisted_user_ids
                or user_id in self.config.admin_user_ids
            )
            if not is_whitelisted:
                logger.warning(
                    "Unauthorized user (whitelist mode) user_id=%d",
                    user_id,
                )
            return is_whitelisted

        return True

    def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin.

        Args:
            user_id: The Telegram user ID to check.

        Returns:
            True if the user is an admin, False otherwise.
        """
        return user_id in self.config.admin_user_ids

    def add_to_whitelist(self, user_id: int) -> None:
        """Add a user to the whitelist.

        Args:
            user_id: The Telegram user ID to add.
        """
        self.config.whitelisted_user_ids.add(user_id)
        logger.info("Added user to whitelist user_id=%d", user_id)

    def remove_from_whitelist(self, user_id: int) -> None:
        """Remove a user from the whitelist.

        Args:
            user_id: The Telegram user ID to remove.
        """
        self.config.whitelisted_user_ids.discard(user_id)
        logger.info("Removed user from whitelist user_id=%d", user_id)

    def add_admin(self, user_id: int) -> None:
        """Add a user as an admin.

        Args:
            user_id: The Telegram user ID to add as admin.
        """
        self.config.admin_user_ids.add(user_id)
        logger.info("Added admin user user_id=%d", user_id)

    def remove_admin(self, user_id: int) -> None:
        """Remove a user from admins.

        Args:
            user_id: The Telegram user ID to remove from admins.
        """
        self.config.admin_user_ids.discard(user_id)
        logger.info("Removed admin user user_id=%d", user_id)

    def get_authorization_message(self) -> str:
        """Get a message explaining the current authorization status.

        Returns:
            A user-friendly message about authorization.
        """
        if not self.config.enabled or self.config.mode == AuthorizationMode.OPEN:
            return "This bot is open to all users."

        if self.config.mode == AuthorizationMode.ADMIN_ONLY:
            return (
                "⚠️ This bot is in admin-only mode.\n"
                "Only authorized administrators can use this bot."
            )

        if self.config.mode == AuthorizationMode.WHITELIST:
            return (
                "⚠️ This bot is in whitelist mode.\n"
                "Only whitelisted users can use this bot.\n"
                "Contact the administrator for access."
            )

        return "Authorization is configured."

    def get_unauthorized_message(self) -> str:
        """Get a message to show unauthorized users.

        Returns:
            A message explaining that the user is not authorized.
        """
        if self.config.mode == AuthorizationMode.ADMIN_ONLY:
            return (
                "🚫 *Access Denied*\n\n"
                "This bot is in admin-only mode.\n"
                "You are not authorized to use this bot."
            )

        if self.config.mode == AuthorizationMode.WHITELIST:
            return (
                "🚫 *Access Denied*\n\n"
                "This bot is in whitelist mode.\n"
                "You are not on the authorized users list.\n"
                "Please contact the administrator for access."
            )

        return (
            "🚫 *Access Denied*\n\n"
            "You are not authorized to use this bot."
        )
