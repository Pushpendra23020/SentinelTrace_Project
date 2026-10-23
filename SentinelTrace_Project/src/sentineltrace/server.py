"""Local HTTP interface for the SentinelTrace demonstration."""
from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .analyzer import analyze_logs
from .rules import public_rule_catalogue

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_PAGE = PROJECT_ROOT / "web" / "index.html"
DEMO_LOG = PROJECT_ROOT / "sample_data" / "demo.log"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
MAX_REQUEST_BYTES = 1_000_000


class SentinelTraceHTTPServer(ThreadingHTTPServer):
    """A request server that does not delay process exit for worker threads."""

    daemon_threads = True
    allow_reuse_address = True


class RequestHandler(BaseHTTPRequestHandler):
    """Serve the dashboard and a minimal local-only JSON API."""

    server_version = "SentinelTrace/3.0"

    def _send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send_bytes(status, encoded, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 - required stdlib callback name
        route = urlparse(self.path).path
        if route == "/":
            self._send_bytes(HTTPStatus.OK, WEB_PAGE.read_bytes(), "text/html; charset=utf-8")
        elif route == "/demo":
            self._send_json(HTTPStatus.OK, {"logs": DEMO_LOG.read_text(encoding="utf-8")})
        elif route == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok", "service": "SentinelTrace", "mode": "local-only"})
        elif route == "/rules":
            self._send_json(HTTPStatus.OK, {"rules": public_rule_catalogue()})
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Route not found."})

    def do_POST(self) -> None:  # noqa: N802 - required stdlib callback name
        if urlparse(self.path).path != "/analyze":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Route not found."})
            return

        header = self.headers.get("Content-Length")
        try:
            content_length = int(header) if header is not None else 0
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Content-Length must be a valid integer."})
            return
        if content_length < 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Content-Length cannot be negative."})
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": "Log input exceeds the 1 MB local-demo limit."},
            )
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object.")
            logs = payload.get("logs", "")
            if not isinstance(logs, str):
                raise ValueError("The 'logs' value must be text.")
            self._send_json(HTTPStatus.OK, analyze_logs(logs))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def log_message(self, _format: str, *_args: object) -> None:
        """Keep routine browser requests out of the evaluation console."""


def main() -> None:
    """Run the project only on the loopback interface by default."""

    host = os.environ.get("SENTINELTRACE_HOST", DEFAULT_HOST)
    try:
        port = int(os.environ.get("SENTINELTRACE_PORT", str(DEFAULT_PORT)))
    except ValueError as exc:
        raise SystemExit("SENTINELTRACE_PORT must be a valid integer.") from exc

    print(f"SentinelTrace is running at http://{host}:{port}")
    print("Press Ctrl+C to stop the local server.")
    try:
        with SentinelTraceHTTPServer((host, port), RequestHandler) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nSentinelTrace stopped.")


if __name__ == "__main__":
    main()
