"""Tests for the authorization module."""

import pytest

from treecko_bot.authorization import (
    AuthorizationConfig,
    AuthorizationMode,
    UserAuthorization,
)


class TestAuthorizationMode:
    """Tests for AuthorizationMode enum."""

    def test_open_mode(self):
        """Test OPEN mode value."""
        assert AuthorizationMode.OPEN.value == "open"

    def test_whitelist_mode(self):
        """Test WHITELIST mode value."""
        assert AuthorizationMode.WHITELIST.value == "whitelist"

    def test_admin_only_mode(self):
        """Test ADMIN_ONLY mode value."""
        assert AuthorizationMode.ADMIN_ONLY.value == "admin_only"


class TestAuthorizationConfig:
    """Tests for AuthorizationConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AuthorizationConfig()
        assert config.mode == AuthorizationMode.OPEN
        assert config.admin_user_ids == set()
        assert config.whitelisted_user_ids == set()
        assert config.enabled is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = AuthorizationConfig(
            mode=AuthorizationMode.WHITELIST,
            admin_user_ids={123, 456},
            whitelisted_user_ids={789, 101},
            enabled=True,
        )
        assert config.mode == AuthorizationMode.WHITELIST
        assert config.admin_user_ids == {123, 456}
        assert config.whitelisted_user_ids == {789, 101}

    def test_from_env_values_open_mode(self):
        """Test creating config from env values with open mode."""
        config = AuthorizationConfig.from_env_values(mode_str="open")
        assert config.mode == AuthorizationMode.OPEN
        assert config.enabled is False  # Open mode disables authorization

    def test_from_env_values_whitelist_mode(self):
        """Test creating config from env values with whitelist mode."""
        config = AuthorizationConfig.from_env_values(
            mode_str="whitelist",
            whitelist_ids_str="123, 456, 789",
        )
        assert config.mode == AuthorizationMode.WHITELIST
        assert config.whitelisted_user_ids == {123, 456, 789}
        assert config.enabled is True

    def test_from_env_values_admin_only_mode(self):
        """Test creating config from env values with admin_only mode."""
        config = AuthorizationConfig.from_env_values(
            mode_str="admin_only",
            admin_ids_str="123, 456",
        )
        assert config.mode == AuthorizationMode.ADMIN_ONLY
        assert config.admin_user_ids == {123, 456}
        assert config.enabled is True

    def test_from_env_values_parses_admin_ids(self):
        """Test parsing admin IDs from string."""
        config = AuthorizationConfig.from_env_values(
            admin_ids_str="111,222,333"
        )
        assert config.admin_user_ids == {111, 222, 333}

    def test_from_env_values_handles_whitespace(self):
        """Test parsing handles whitespace in IDs."""
        config = AuthorizationConfig.from_env_values(
            admin_ids_str="  111 , 222 ,  333  "
        )
        assert config.admin_user_ids == {111, 222, 333}

    def test_from_env_values_handles_invalid_ids(self):
        """Test parsing handles invalid IDs gracefully."""
        config = AuthorizationConfig.from_env_values(
            admin_ids_str="123, invalid, 456, , -1, 0"
        )
        assert config.admin_user_ids == {123, 456}

    def test_from_env_values_handles_none(self):
        """Test creating config from None values."""
        config = AuthorizationConfig.from_env_values()
        assert config.mode == AuthorizationMode.OPEN
        assert config.admin_user_ids == set()
        assert config.whitelisted_user_ids == set()


class TestUserAuthorization:
    """Tests for UserAuthorization."""

    @pytest.fixture
    def open_auth(self):
        """Create authorization with open mode."""
        config = AuthorizationConfig(mode=AuthorizationMode.OPEN)
        return UserAuthorization(config)

    @pytest.fixture
    def whitelist_auth(self):
        """Create authorization with whitelist mode."""
        config = AuthorizationConfig(
            mode=AuthorizationMode.WHITELIST,
            admin_user_ids={100},
            whitelisted_user_ids={123, 456},
            enabled=True,
        )
        return UserAuthorization(config)

    @pytest.fixture
    def admin_only_auth(self):
        """Create authorization with admin_only mode."""
        config = AuthorizationConfig(
            mode=AuthorizationMode.ADMIN_ONLY,
            admin_user_ids={100, 200},
            enabled=True,
        )
        return UserAuthorization(config)

    def test_open_mode_allows_all(self, open_auth):
        """Test that open mode allows all users."""
        assert open_auth.is_authorized(123)
        assert open_auth.is_authorized(999)

    def test_whitelist_mode_allows_whitelisted(self, whitelist_auth):
        """Test that whitelist mode allows whitelisted users."""
        assert whitelist_auth.is_authorized(123)
        assert whitelist_auth.is_authorized(456)

    def test_whitelist_mode_allows_admins(self, whitelist_auth):
        """Test that whitelist mode allows admin users."""
        assert whitelist_auth.is_authorized(100)

    def test_whitelist_mode_denies_others(self, whitelist_auth):
        """Test that whitelist mode denies non-whitelisted users."""
        assert not whitelist_auth.is_authorized(999)

    def test_admin_only_mode_allows_admins(self, admin_only_auth):
        """Test that admin_only mode allows admin users."""
        assert admin_only_auth.is_authorized(100)
        assert admin_only_auth.is_authorized(200)

    def test_admin_only_mode_denies_others(self, admin_only_auth):
        """Test that admin_only mode denies non-admin users."""
        assert not admin_only_auth.is_authorized(123)
        assert not admin_only_auth.is_authorized(999)

    def test_is_admin(self, whitelist_auth):
        """Test checking if user is admin."""
        assert whitelist_auth.is_admin(100)
        assert not whitelist_auth.is_admin(123)
        assert not whitelist_auth.is_admin(999)

    def test_add_to_whitelist(self, whitelist_auth):
        """Test adding user to whitelist."""
        assert not whitelist_auth.is_authorized(999)

        whitelist_auth.add_to_whitelist(999)

        assert whitelist_auth.is_authorized(999)

    def test_remove_from_whitelist(self, whitelist_auth):
        """Test removing user from whitelist."""
        assert whitelist_auth.is_authorized(123)

        whitelist_auth.remove_from_whitelist(123)

        assert not whitelist_auth.is_authorized(123)

    def test_add_admin(self, whitelist_auth):
        """Test adding admin user."""
        assert not whitelist_auth.is_admin(999)

        whitelist_auth.add_admin(999)

        assert whitelist_auth.is_admin(999)

    def test_remove_admin(self, admin_only_auth):
        """Test removing admin user."""
        assert admin_only_auth.is_admin(100)

        admin_only_auth.remove_admin(100)

        assert not admin_only_auth.is_admin(100)

    def test_disabled_authorization_allows_all(self):
        """Test that disabled authorization allows all users."""
        config = AuthorizationConfig(
            mode=AuthorizationMode.ADMIN_ONLY,
            admin_user_ids={100},
            enabled=False,
        )
        auth = UserAuthorization(config)

        assert auth.is_authorized(999)

    def test_get_authorization_message_open(self, open_auth):
        """Test authorization message for open mode."""
        message = open_auth.get_authorization_message()
        assert "open to all" in message.lower()

    def test_get_authorization_message_whitelist(self, whitelist_auth):
        """Test authorization message for whitelist mode."""
        message = whitelist_auth.get_authorization_message()
        assert "whitelist" in message.lower()

    def test_get_authorization_message_admin_only(self, admin_only_auth):
        """Test authorization message for admin_only mode."""
        message = admin_only_auth.get_authorization_message()
        assert "admin" in message.lower()

    def test_get_unauthorized_message_whitelist(self, whitelist_auth):
        """Test unauthorized message for whitelist mode."""
        message = whitelist_auth.get_unauthorized_message()
        assert "Access Denied" in message
        assert "whitelist" in message.lower()

    def test_get_unauthorized_message_admin_only(self, admin_only_auth):
        """Test unauthorized message for admin_only mode."""
        message = admin_only_auth.get_unauthorized_message()
        assert "Access Denied" in message
        assert "admin" in message.lower()

    def test_default_authorization(self):
        """Test default authorization with no config."""
        auth = UserAuthorization()
        # Default should allow all users
        assert auth.is_authorized(123)
        assert auth.is_authorized(999)
