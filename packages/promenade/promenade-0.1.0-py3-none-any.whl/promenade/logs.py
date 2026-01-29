"""Log aggregation and streaming for Promenade."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Awaitable, Callable


class Stream(str, Enum):
    """Output stream type."""

    STDOUT = "stdout"
    STDERR = "stderr"


@dataclass
class LogLine:
    """A single log line from a service."""

    timestamp: datetime
    service: str
    stream: Stream
    line: str

    def format(self) -> str:
        """Format log line for display."""
        ts = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.") + f"{self.timestamp.microsecond // 1000:03d}Z"
        stderr_marker = " [stderr]" if self.stream == Stream.STDERR else ""
        return f"{ts} [{self.service}]{stderr_marker} {self.line}"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat() + "Z",
            "service": self.service,
            "stream": self.stream.value,
            "line": self.line,
        }


class LogBuffer:
    """Ring buffer for log lines using deque."""

    def __init__(self, maxlen: int = 1000):
        self._buffer: deque[LogLine] = deque(maxlen=maxlen)
        self._maxlen = maxlen

    def append(self, line: LogLine) -> None:
        """Add a log line to the buffer."""
        self._buffer.append(line)

    def get_lines(self, limit: int | None = None) -> list[LogLine]:
        """Get log lines from buffer.

        Args:
            limit: Maximum number of lines to return (most recent). None for all.

        Returns:
            List of log lines, oldest first.
        """
        if limit is None or limit >= len(self._buffer):
            return list(self._buffer)
        return list(self._buffer)[-limit:]

    def __len__(self) -> int:
        return len(self._buffer)

    def clear(self) -> None:
        """Clear all log lines."""
        self._buffer.clear()


# Type alias for log subscribers
LogSubscriber = Callable[[LogLine], Awaitable[None]]


class LogAggregator:
    """Central log collection with pub/sub for streaming.

    Maintains per-service log buffers and notifies subscribers of new log lines.
    """

    def __init__(self, buffer_size: int = 1000):
        self._buffer_size = buffer_size
        self._buffers: dict[str, LogBuffer] = {}
        self._subscribers: list[LogSubscriber] = []
        self._lock = asyncio.Lock()

    def _get_or_create_buffer(self, service: str) -> LogBuffer:
        """Get or create a log buffer for a service."""
        if service not in self._buffers:
            self._buffers[service] = LogBuffer(maxlen=self._buffer_size)
        return self._buffers[service]

    async def add_line(self, line: LogLine) -> None:
        """Add a log line and notify all subscribers."""
        async with self._lock:
            buffer = self._get_or_create_buffer(line.service)
            buffer.append(line)

        # Notify subscribers (outside lock to avoid deadlock)
        for subscriber in self._subscribers[:]:  # Copy list to handle modifications
            try:
                await subscriber(line)
            except Exception:
                # Don't let a bad subscriber crash the aggregator
                pass

    def subscribe(self, callback: LogSubscriber) -> Callable[[], None]:
        """Subscribe to new log lines.

        Args:
            callback: Async function called with each new LogLine.

        Returns:
            Unsubscribe function to call when done.
        """
        self._subscribers.append(callback)

        def unsubscribe() -> None:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        return unsubscribe

    def get_logs(
        self,
        services: list[str] | None = None,
        limit: int | None = None,
    ) -> list[LogLine]:
        """Get historical logs, optionally filtered by service.

        Args:
            services: List of service names to include. None for all.
            limit: Maximum total lines to return (most recent).

        Returns:
            List of log lines sorted by timestamp, oldest first.
        """
        all_lines: list[LogLine] = []

        target_services = services or list(self._buffers.keys())
        for service in target_services:
            if service in self._buffers:
                all_lines.extend(self._buffers[service].get_lines())

        # Sort by timestamp
        all_lines.sort(key=lambda x: x.timestamp)

        if limit is not None and len(all_lines) > limit:
            return all_lines[-limit:]
        return all_lines

    def get_service_logs(self, service: str, limit: int | None = None) -> list[LogLine]:
        """Get logs for a specific service."""
        if service not in self._buffers:
            return []
        return self._buffers[service].get_lines(limit)

    def clear_service(self, service: str) -> None:
        """Clear logs for a specific service."""
        if service in self._buffers:
            self._buffers[service].clear()

    def clear_all(self) -> None:
        """Clear all logs."""
        self._buffers.clear()

    @property
    def subscriber_count(self) -> int:
        """Number of active subscribers."""
        return len(self._subscribers)


def create_log_line(service: str, line: str, stream: Stream = Stream.STDOUT) -> LogLine:
    """Create a log line with current timestamp."""
    return LogLine(
        timestamp=datetime.now(timezone.utc),
        service=service,
        stream=stream,
        line=line,
    )
