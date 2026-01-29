"""Tests for log aggregation."""

import asyncio
from datetime import datetime, timezone

import pytest

from promenade.logs import (
    LogAggregator,
    LogBuffer,
    LogLine,
    Stream,
    create_log_line,
)


class TestLogLine:
    """Tests for LogLine dataclass."""

    def test_create_log_line(self):
        """Test creating a log line."""
        line = LogLine(
            timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            service="api",
            stream=Stream.STDOUT,
            line="Hello world",
        )
        assert line.service == "api"
        assert line.stream == Stream.STDOUT
        assert line.line == "Hello world"

    def test_format_stdout(self):
        """Test formatting stdout log line."""
        line = LogLine(
            timestamp=datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
            service="api",
            stream=Stream.STDOUT,
            line="Server started",
        )
        formatted = line.format()
        assert "[api]" in formatted
        assert "Server started" in formatted
        assert "[stderr]" not in formatted

    def test_format_stderr(self):
        """Test formatting stderr log line."""
        line = LogLine(
            timestamp=datetime(2024, 1, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
            service="api",
            stream=Stream.STDERR,
            line="Error occurred",
        )
        formatted = line.format()
        assert "[stderr]" in formatted

    def test_to_dict(self):
        """Test converting to dictionary."""
        line = LogLine(
            timestamp=datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc),
            service="api",
            stream=Stream.STDOUT,
            line="Hello",
        )
        d = line.to_dict()
        assert d["service"] == "api"
        assert d["stream"] == "stdout"
        assert d["line"] == "Hello"
        assert "timestamp" in d


class TestLogBuffer:
    """Tests for LogBuffer ring buffer."""

    def test_append_and_get(self):
        """Test appending and retrieving lines."""
        buffer = LogBuffer(maxlen=100)
        line = create_log_line("test", "Hello")
        buffer.append(line)

        lines = buffer.get_lines()
        assert len(lines) == 1
        assert lines[0].line == "Hello"

    def test_ring_buffer_eviction(self):
        """Test that old lines are evicted when buffer is full."""
        buffer = LogBuffer(maxlen=3)

        for i in range(5):
            buffer.append(create_log_line("test", f"Line {i}"))

        lines = buffer.get_lines()
        assert len(lines) == 3
        assert lines[0].line == "Line 2"
        assert lines[1].line == "Line 3"
        assert lines[2].line == "Line 4"

    def test_get_lines_with_limit(self):
        """Test getting limited number of lines."""
        buffer = LogBuffer(maxlen=100)

        for i in range(10):
            buffer.append(create_log_line("test", f"Line {i}"))

        lines = buffer.get_lines(limit=3)
        assert len(lines) == 3
        # Should get most recent
        assert lines[0].line == "Line 7"
        assert lines[2].line == "Line 9"

    def test_len(self):
        """Test buffer length."""
        buffer = LogBuffer(maxlen=100)
        assert len(buffer) == 0

        buffer.append(create_log_line("test", "Line 1"))
        buffer.append(create_log_line("test", "Line 2"))
        assert len(buffer) == 2

    def test_clear(self):
        """Test clearing buffer."""
        buffer = LogBuffer(maxlen=100)
        buffer.append(create_log_line("test", "Line 1"))
        buffer.clear()
        assert len(buffer) == 0


class TestLogAggregator:
    """Tests for LogAggregator."""

    @pytest.mark.asyncio
    async def test_add_and_get_logs(self):
        """Test adding and retrieving logs."""
        aggregator = LogAggregator(buffer_size=100)

        await aggregator.add_line(create_log_line("api", "API log"))
        await aggregator.add_line(create_log_line("web", "Web log"))

        logs = aggregator.get_logs()
        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_get_logs_filtered_by_service(self):
        """Test filtering logs by service."""
        aggregator = LogAggregator(buffer_size=100)

        await aggregator.add_line(create_log_line("api", "API log 1"))
        await aggregator.add_line(create_log_line("web", "Web log"))
        await aggregator.add_line(create_log_line("api", "API log 2"))

        logs = aggregator.get_logs(services=["api"])
        assert len(logs) == 2
        assert all(log.service == "api" for log in logs)

    @pytest.mark.asyncio
    async def test_get_service_logs(self):
        """Test getting logs for a specific service."""
        aggregator = LogAggregator(buffer_size=100)

        await aggregator.add_line(create_log_line("api", "API log"))
        await aggregator.add_line(create_log_line("web", "Web log"))

        logs = aggregator.get_service_logs("api")
        assert len(logs) == 1
        assert logs[0].service == "api"

    @pytest.mark.asyncio
    async def test_subscribe_receives_new_logs(self):
        """Test that subscribers receive new log lines."""
        aggregator = LogAggregator(buffer_size=100)
        received: list[LogLine] = []

        async def callback(line: LogLine) -> None:
            received.append(line)

        unsubscribe = aggregator.subscribe(callback)

        await aggregator.add_line(create_log_line("api", "Log 1"))
        await aggregator.add_line(create_log_line("api", "Log 2"))

        assert len(received) == 2
        assert received[0].line == "Log 1"
        assert received[1].line == "Log 2"

        unsubscribe()

    @pytest.mark.asyncio
    async def test_unsubscribe_stops_notifications(self):
        """Test that unsubscribing stops notifications."""
        aggregator = LogAggregator(buffer_size=100)
        received: list[LogLine] = []

        async def callback(line: LogLine) -> None:
            received.append(line)

        unsubscribe = aggregator.subscribe(callback)
        await aggregator.add_line(create_log_line("api", "Log 1"))

        unsubscribe()

        await aggregator.add_line(create_log_line("api", "Log 2"))

        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_subscriber_count(self):
        """Test subscriber count tracking."""
        aggregator = LogAggregator(buffer_size=100)

        async def callback(line: LogLine) -> None:
            pass

        assert aggregator.subscriber_count == 0

        unsub1 = aggregator.subscribe(callback)
        assert aggregator.subscriber_count == 1

        unsub2 = aggregator.subscribe(callback)
        assert aggregator.subscriber_count == 2

        unsub1()
        assert aggregator.subscriber_count == 1

        unsub2()
        assert aggregator.subscriber_count == 0

    @pytest.mark.asyncio
    async def test_logs_sorted_by_timestamp(self):
        """Test that logs are returned sorted by timestamp."""
        aggregator = LogAggregator(buffer_size=100)

        # Add logs out of order (different services)
        await aggregator.add_line(
            LogLine(
                timestamp=datetime(2024, 1, 15, 10, 0, 2, tzinfo=timezone.utc),
                service="api",
                stream=Stream.STDOUT,
                line="Second",
            )
        )
        await aggregator.add_line(
            LogLine(
                timestamp=datetime(2024, 1, 15, 10, 0, 1, tzinfo=timezone.utc),
                service="web",
                stream=Stream.STDOUT,
                line="First",
            )
        )
        await aggregator.add_line(
            LogLine(
                timestamp=datetime(2024, 1, 15, 10, 0, 3, tzinfo=timezone.utc),
                service="api",
                stream=Stream.STDOUT,
                line="Third",
            )
        )

        logs = aggregator.get_logs()
        assert logs[0].line == "First"
        assert logs[1].line == "Second"
        assert logs[2].line == "Third"
