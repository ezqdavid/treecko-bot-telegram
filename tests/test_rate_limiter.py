"""Tests for the rate limiter module."""

import pytest

from treecko_bot.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        assert config.max_requests == 10
        assert config.window_seconds == 60
        assert config.enabled is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            max_requests=5, window_seconds=30, enabled=False
        )
        assert config.max_requests == 5
        assert config.window_seconds == 30
        assert config.enabled is False


class TestRateLimiter:
    """Tests for RateLimiter."""

    @pytest.fixture
    def mock_time(self):
        """Create a mock time function."""
        current_time = [0.0]

        def get_time():
            return current_time[0]

        def advance(seconds):
            current_time[0] += seconds

        return get_time, advance

    @pytest.fixture
    def rate_limiter(self, mock_time):
        """Create a rate limiter with mock time."""
        get_time, _ = mock_time
        config = RateLimitConfig(max_requests=3, window_seconds=60)
        return RateLimiter(config=config, get_time=get_time)

    def test_first_request_allowed(self, rate_limiter):
        """Test that the first request is always allowed."""
        assert not rate_limiter.is_rate_limited(user_id=123)

    def test_requests_within_limit_allowed(self, rate_limiter):
        """Test that requests within limit are allowed."""
        user_id = 123

        for _ in range(3):
            assert rate_limiter.check_and_record(user_id)

    def test_requests_over_limit_blocked(self, rate_limiter):
        """Test that requests over limit are blocked."""
        user_id = 123

        # Make 3 requests (max allowed)
        for _ in range(3):
            rate_limiter.record_request(user_id)

        # 4th request should be blocked
        assert rate_limiter.is_rate_limited(user_id)
        assert not rate_limiter.check_and_record(user_id)

    def test_rate_limit_resets_after_window(self, rate_limiter, mock_time):
        """Test that rate limit resets after window expires."""
        get_time, advance = mock_time
        user_id = 123

        # Make 3 requests
        for _ in range(3):
            rate_limiter.record_request(user_id)

        # Should be rate limited
        assert rate_limiter.is_rate_limited(user_id)

        # Advance time past the window
        advance(61)

        # Should no longer be rate limited
        assert not rate_limiter.is_rate_limited(user_id)

    def test_get_remaining_requests(self, rate_limiter):
        """Test getting remaining requests."""
        user_id = 123

        assert rate_limiter.get_remaining_requests(user_id) == 3

        rate_limiter.record_request(user_id)
        assert rate_limiter.get_remaining_requests(user_id) == 2

        rate_limiter.record_request(user_id)
        assert rate_limiter.get_remaining_requests(user_id) == 1

        rate_limiter.record_request(user_id)
        assert rate_limiter.get_remaining_requests(user_id) == 0

    def test_get_retry_after(self, rate_limiter, mock_time):
        """Test getting retry after time."""
        get_time, advance = mock_time
        user_id = 123

        # No requests, retry after should be 0
        assert rate_limiter.get_retry_after(user_id) == 0.0

        # Make 3 requests
        for _ in range(3):
            rate_limiter.record_request(user_id)

        # Should have to wait about 60 seconds
        retry_after = rate_limiter.get_retry_after(user_id)
        assert 59.0 <= retry_after <= 60.0

        # Advance time by 30 seconds
        advance(30)

        # Should have to wait about 30 seconds now
        retry_after = rate_limiter.get_retry_after(user_id)
        assert 29.0 <= retry_after <= 30.0

    def test_reset_user(self, rate_limiter):
        """Test resetting rate limit for a user."""
        user_id = 123

        # Make 3 requests (max allowed)
        for _ in range(3):
            rate_limiter.record_request(user_id)

        assert rate_limiter.is_rate_limited(user_id)

        # Reset user
        rate_limiter.reset_user(user_id)

        # Should no longer be rate limited
        assert not rate_limiter.is_rate_limited(user_id)
        assert rate_limiter.get_remaining_requests(user_id) == 3

    def test_reset_all(self, rate_limiter):
        """Test resetting rate limits for all users."""
        # Make requests for multiple users
        for user_id in [123, 456, 789]:
            for _ in range(3):
                rate_limiter.record_request(user_id)

        # All should be rate limited
        for user_id in [123, 456, 789]:
            assert rate_limiter.is_rate_limited(user_id)

        # Reset all
        rate_limiter.reset_all()

        # None should be rate limited
        for user_id in [123, 456, 789]:
            assert not rate_limiter.is_rate_limited(user_id)

    def test_different_users_independent(self, rate_limiter):
        """Test that rate limits are independent per user."""
        # User 1 makes 3 requests
        for _ in range(3):
            rate_limiter.record_request(123)

        # User 1 should be rate limited
        assert rate_limiter.is_rate_limited(123)

        # User 2 should not be rate limited
        assert not rate_limiter.is_rate_limited(456)
        assert rate_limiter.get_remaining_requests(456) == 3

    def test_disabled_rate_limiter(self):
        """Test that disabled rate limiter allows all requests."""
        config = RateLimitConfig(max_requests=1, enabled=False)
        rate_limiter = RateLimiter(config=config)

        user_id = 123

        # Make many requests
        for _ in range(100):
            assert rate_limiter.check_and_record(user_id)

        # Should never be rate limited
        assert not rate_limiter.is_rate_limited(user_id)
        assert rate_limiter.get_remaining_requests(user_id) == 1
        assert rate_limiter.get_retry_after(user_id) == 0.0

    def test_sliding_window(self, rate_limiter, mock_time):
        """Test that old requests are cleared in sliding window."""
        get_time, advance = mock_time
        user_id = 123

        # Make 2 requests
        rate_limiter.record_request(user_id)
        rate_limiter.record_request(user_id)

        # Advance time by 30 seconds
        advance(30)

        # Make 1 more request
        rate_limiter.record_request(user_id)

        # Should be rate limited (3 requests total)
        assert rate_limiter.is_rate_limited(user_id)

        # Advance time by 31 more seconds (61 total from first 2 requests)
        advance(31)

        # First 2 requests should have expired
        assert not rate_limiter.is_rate_limited(user_id)
        assert rate_limiter.get_remaining_requests(user_id) == 2  # 1 request still in window
