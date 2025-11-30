"""Health check functionality for monitoring."""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from .logging_config import get_logger

logger = get_logger(__name__)

# Default health check configuration
DEFAULT_HEALTH_PORT = 8081
HEALTH_PATH = "/health"

# Module-level storage for callback (used by handler)
_health_callback: Callable[[], "HealthStatus"] | None = None


@dataclass
class HealthStatus:
    """Health check response data."""

    status: str
    timestamp: float
    database_connected: bool
    sheets_configured: bool

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "checks": {
                "database": "ok" if self.database_connected else "not_connected",
                "sheets": "configured" if self.sheets_configured else "not_configured",
            },
        }


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health check endpoint."""

    def log_message(self, format: str, *args) -> None:
        """Suppress default logging to avoid noise."""
        pass

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == HEALTH_PATH:
            self._handle_health_check()
        else:
            self._send_not_found()

    def _handle_health_check(self) -> None:
        """Handle health check request."""
        # Access callback from server instance
        callback = getattr(self.server, "health_callback", None)

        if callback is None:
            # No callback configured, return basic healthy status
            status = HealthStatus(
                status="healthy",
                timestamp=time.time(),
                database_connected=True,
                sheets_configured=False,
            )
        else:
            status = callback()

        response_body = json.dumps(status.to_dict())
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body.encode())

    def _send_not_found(self) -> None:
        """Send 404 Not Found response."""
        response_body = json.dumps({"error": "Not Found"})
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body.encode())


class HealthCheckHTTPServer(HTTPServer):
    """Custom HTTP server that stores the health callback."""

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        health_callback: Callable[[], HealthStatus] | None = None,
    ):
        """Initialize the server with a health callback.

        Args:
            server_address: Tuple of (host, port).
            handler_class: The request handler class.
            health_callback: Callback function to get health status.
        """
        super().__init__(server_address, handler_class)
        self.health_callback = health_callback


class HealthCheckServer:
    """HTTP server for health check endpoint."""

    def __init__(
        self,
        port: int = DEFAULT_HEALTH_PORT,
        health_callback: Callable[[], HealthStatus] | None = None,
    ):
        """Initialize the health check server.

        Args:
            port: Port to listen on for health check requests.
            health_callback: Callback function to get current health status.
        """
        self.port = port
        self.health_callback = health_callback
        self._server: HealthCheckHTTPServer | None = None
        self._thread: Thread | None = None

    def start(self) -> None:
        """Start the health check server in a background thread."""
        self._server = HealthCheckHTTPServer(
            ("0.0.0.0", self.port),
            HealthCheckHandler,
            health_callback=self.health_callback,
        )
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info("Health check server started", port=self.port)

    def stop(self) -> None:
        """Stop the health check server."""
        if self._server:
            self._server.shutdown()
            self._server = None
            logger.info("Health check server stopped")
