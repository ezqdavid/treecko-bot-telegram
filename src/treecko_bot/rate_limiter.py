"""Rate limiting functionality for the Telegram bot."""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Default rate limit configuration
DEFAULT_MAX_REQUESTS = 10  # Maximum requests per window
DEFAULT_WINDOW_SECONDS = 60  # Time window in seconds


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting.

    Attributes:
        max_requests: Maximum number of requests allowed per window.
        window_seconds: Time window in seconds for rate limiting.
        enabled: Whether rate limiting is enabled.
    """

    max_requests: int = DEFAULT_MAX_REQUESTS
    window_seconds: int = DEFAULT_WINDOW_SECONDS
    enabled: bool = True


@dataclass
class UserRequestInfo:
    """Information about user requests for rate limiting.

    Attributes:
        request_timestamps: List of timestamps when requests were made.
    """

    request_timestamps: list[float] = field(default_factory=list)


class RateLimiter:
    """Rate limiter to prevent abuse of the bot.

    Uses a sliding window algorithm to track request rates per user.
    """

    def __init__(
        self,
        config: RateLimitConfig | None = None,
        get_time: Callable[[], float] | None = None,
    ) -> None:
        """Initialize the rate limiter.

        Args:
            config: Rate limit configuration. Uses defaults if not provided.
            get_time: Callable to get current time (useful for testing).
                     Defaults to time.time.
        """
        self.config = config or RateLimitConfig()
        self._get_time = get_time or time.time
        self._user_requests: dict[int, UserRequestInfo] = defaultdict(UserRequestInfo)

    def is_rate_limited(self, user_id: int) -> bool:
        """Check if a user is currently rate limited.

        Args:
            user_id: The Telegram user ID to check.

        Returns:
            True if the user is rate limited, False otherwise.
        """
        if not self.config.enabled:
            return False

        current_time = self._get_time()
        user_info = self._user_requests[user_id]

        # Clean up old requests outside the window
        window_start = current_time - self.config.window_seconds
        user_info.request_timestamps = [
            ts for ts in user_info.request_timestamps if ts > window_start
        ]

        # Check if user has exceeded the limit
        return len(user_info.request_timestamps) >= self.config.max_requests

    def record_request(self, user_id: int) -> None:
        """Record a request from a user.

        Args:
            user_id: The Telegram user ID making the request.
        """
        if not self.config.enabled:
            return

        current_time = self._get_time()
        self._user_requests[user_id].request_timestamps.append(current_time)
        logger.debug(
            "Recorded request for user_id=%d, request_count=%d",
            user_id,
            len(self._user_requests[user_id].request_timestamps),
        )

    def check_and_record(self, user_id: int) -> bool:
        """Check rate limit and record request if allowed.

        This is a convenience method that combines is_rate_limited and
        record_request. If the user is not rate limited, the request is
        recorded automatically.

        Args:
            user_id: The Telegram user ID making the request.

        Returns:
            True if the request is allowed, False if rate limited.
        """
        if self.is_rate_limited(user_id):
            logger.warning(
                "User rate limited user_id=%d max_requests=%d window_seconds=%d",
                user_id,
                self.config.max_requests,
                self.config.window_seconds,
            )
            return False

        self.record_request(user_id)
        return True

    def get_remaining_requests(self, user_id: int) -> int:
        """Get the number of remaining requests for a user.

        Args:
            user_id: The Telegram user ID to check.

        Returns:
            Number of remaining requests in the current window.
        """
        if not self.config.enabled:
            return self.config.max_requests

        current_time = self._get_time()
        user_info = self._user_requests[user_id]

        # Clean up old requests
        window_start = current_time - self.config.window_seconds
        valid_requests = [
            ts for ts in user_info.request_timestamps if ts > window_start
        ]

        return max(0, self.config.max_requests - len(valid_requests))

    def get_retry_after(self, user_id: int) -> float:
        """Get the time in seconds until the user can make another request.

        Args:
            user_id: The Telegram user ID to check.

        Returns:
            Seconds until the rate limit resets. Returns 0 if not rate limited.
        """
        if not self.config.enabled:
            return 0.0

        current_time = self._get_time()
        user_info = self._user_requests[user_id]

        if not user_info.request_timestamps:
            return 0.0

        # Clean up old requests
        window_start = current_time - self.config.window_seconds
        valid_requests = [
            ts for ts in user_info.request_timestamps if ts > window_start
        ]

        if len(valid_requests) < self.config.max_requests:
            return 0.0

        # Return time until the oldest request expires
        oldest_request = min(valid_requests)
        return max(0.0, oldest_request + self.config.window_seconds - current_time)

    def reset_user(self, user_id: int) -> None:
        """Reset rate limit for a specific user.

        Args:
            user_id: The Telegram user ID to reset.
        """
        if user_id in self._user_requests:
            del self._user_requests[user_id]
            logger.debug("Reset rate limit for user_id=%d", user_id)

    def reset_all(self) -> None:
        """Reset rate limits for all users."""
        self._user_requests.clear()
        logger.debug("Reset all rate limits")
