"""Tests for the health check module."""

import json
import time
import urllib.error
import urllib.request

import pytest

from treecko_bot.health import (
    HEALTH_PATH,
    HealthCheckServer,
    HealthStatus,
)


class TestHealthStatus:
    """Tests for HealthStatus dataclass."""

    def test_to_dict_healthy(self):
        """Test converting healthy status to dict."""
        status = HealthStatus(
            status="healthy",
            timestamp=1234567890.0,
            database_connected=True,
            sheets_configured=True,
        )
        result = status.to_dict()

        assert result["status"] == "healthy"
        assert result["timestamp"] == 1234567890.0
        assert result["checks"]["database"] == "ok"
        assert result["checks"]["sheets"] == "configured"

    def test_to_dict_partial_configuration(self):
        """Test converting partial configuration status to dict."""
        status = HealthStatus(
            status="healthy",
            timestamp=1234567890.0,
            database_connected=True,
            sheets_configured=False,
        )
        result = status.to_dict()

        assert result["checks"]["database"] == "ok"
        assert result["checks"]["sheets"] == "not_configured"

    def test_to_dict_database_not_connected(self):
        """Test converting status with database not connected."""
        status = HealthStatus(
            status="healthy",
            timestamp=1234567890.0,
            database_connected=False,
            sheets_configured=False,
        )
        result = status.to_dict()

        assert result["checks"]["database"] == "not_connected"


class TestHealthCheckServer:
    """Tests for HealthCheckServer."""

    @pytest.fixture
    def health_callback(self):
        """Create a health callback function."""
        def callback():
            return HealthStatus(
                status="healthy",
                timestamp=time.time(),
                database_connected=True,
                sheets_configured=True,
            )
        return callback

    def test_server_start_and_stop(self, health_callback):
        """Test starting and stopping the health check server."""
        # Use a high port to avoid conflicts
        server = HealthCheckServer(port=19876, health_callback=health_callback)
        server.start()

        # Verify server is running by making a request
        time.sleep(0.1)  # Give server time to start

        try:
            url = f"http://localhost:19876{HEALTH_PATH}"
            with urllib.request.urlopen(url, timeout=2) as response:
                assert response.status == 200
                data = json.loads(response.read().decode())
                assert data["status"] == "healthy"
        finally:
            server.stop()

    def test_server_health_endpoint(self, health_callback):
        """Test health endpoint returns correct data."""
        server = HealthCheckServer(port=19877, health_callback=health_callback)
        server.start()
        time.sleep(0.1)

        try:
            url = f"http://localhost:19877{HEALTH_PATH}"
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.loads(response.read().decode())
                assert "status" in data
                assert "timestamp" in data
                assert "checks" in data
                assert "database" in data["checks"]
                assert "sheets" in data["checks"]
        finally:
            server.stop()

    def test_server_404_for_unknown_path(self, health_callback):
        """Test server returns 404 for unknown paths."""
        server = HealthCheckServer(port=19878, health_callback=health_callback)
        server.start()
        time.sleep(0.1)

        try:
            url = "http://localhost:19878/unknown"
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(url, timeout=2)
            assert exc_info.value.code == 404
        finally:
            server.stop()

    def test_server_without_callback(self):
        """Test server works without a callback (uses defaults)."""
        server = HealthCheckServer(port=19879, health_callback=None)
        server.start()
        time.sleep(0.1)

        try:
            url = f"http://localhost:19879{HEALTH_PATH}"
            with urllib.request.urlopen(url, timeout=2) as response:
                assert response.status == 200
                data = json.loads(response.read().decode())
                assert data["status"] == "healthy"
        finally:
            server.stop()

    def test_server_custom_status(self):
        """Test server with custom health status."""
        def custom_callback():
            return HealthStatus(
                status="degraded",
                timestamp=1000.0,
                database_connected=False,
                sheets_configured=False,
            )

        server = HealthCheckServer(port=19880, health_callback=custom_callback)
        server.start()
        time.sleep(0.1)

        try:
            url = f"http://localhost:19880{HEALTH_PATH}"
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.loads(response.read().decode())
                assert data["status"] == "degraded"
                assert data["checks"]["database"] == "not_connected"
        finally:
            server.stop()
