"""Static file server for Promenade."""

from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path


class StaticFileServer:
    """Simple async HTTP server that serves a single static file."""

    def __init__(self, file_path: Path, port: int, host: str = "127.0.0.1"):
        self.file_path = file_path
        self.port = port
        self.host = host
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        """Start the static file server."""
        self._server = await asyncio.start_server(
            self._handle_request,
            self.host,
            self.port,
        )
        await self._server.start_serving()

    async def stop(self) -> None:
        """Stop the static file server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle an incoming HTTP request."""
        try:
            # Read request line
            request_line = await reader.readline()
            if not request_line:
                return

            # Read headers (we don't really need them, but consume them)
            while True:
                line = await reader.readline()
                if line == b"\r\n" or line == b"\n" or not line:
                    break

            # Parse request
            try:
                method, path, _ = request_line.decode().split(" ", 2)
            except ValueError:
                await self._send_error(writer, 400, "Bad Request")
                return

            # Only support GET and HEAD
            if method not in ("GET", "HEAD"):
                await self._send_error(writer, 405, "Method Not Allowed")
                return

            # Serve the file for any path (single file server)
            if not self.file_path.exists():
                await self._send_error(writer, 404, "Not Found")
                return

            # Determine content type
            content_type, _ = mimetypes.guess_type(str(self.file_path))
            if content_type is None:
                content_type = "application/octet-stream"

            # Read file content
            content = self.file_path.read_bytes()

            # Send response
            response_headers = [
                "HTTP/1.1 200 OK",
                f"Content-Type: {content_type}",
                f"Content-Length: {len(content)}",
                "Connection: close",
                "Access-Control-Allow-Origin: *",
                "",
                "",
            ]
            writer.write("\r\n".join(response_headers).encode())

            if method == "GET":
                writer.write(content)

            await writer.drain()

        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass  # Expected when clients disconnect
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def _send_error(
        self,
        writer: asyncio.StreamWriter,
        status: int,
        message: str,
    ) -> None:
        """Send an HTTP error response."""
        body = f"<html><body><h1>{status} {message}</h1></body></html>"
        response_headers = [
            f"HTTP/1.1 {status} {message}",
            "Content-Type: text/html",
            f"Content-Length: {len(body)}",
            "Connection: close",
            "",
            "",
        ]
        writer.write("\r\n".join(response_headers).encode())
        writer.write(body.encode())
        await writer.drain()
