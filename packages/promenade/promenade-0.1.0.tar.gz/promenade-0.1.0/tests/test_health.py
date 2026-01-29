"""Tests for health checking."""

import asyncio

import pytest

from promenade.health import (
    Health,
    HealthChecker,
    HTTPHealthCheck,
    TCPHealthCheck,
    create_health_checker,
)


class TestHTTPHealthCheck:
    """Tests for HTTP health checks."""

    def test_url_construction(self):
        """Test HTTP health check URL construction."""
        check = HTTPHealthCheck(port=8080, path="/health")
        assert check.url == "http://127.0.0.1:8080/health"

    def test_url_default_path(self):
        """Test HTTP health check with default path."""
        check = HTTPHealthCheck(port=8080)
        assert check.url == "http://127.0.0.1:8080/"

    @pytest.mark.asyncio
    async def test_check_failure_connection_refused(self):
        """Test HTTP health check when connection refused."""
        check = HTTPHealthCheck(port=59999, path="/health", timeout=1.0)
        result = await check.check()
        assert result is False


class TestTCPHealthCheck:
    """Tests for TCP health checks."""

    @pytest.mark.asyncio
    async def test_check_failure_connection_refused(self):
        """Test TCP health check when connection refused."""
        check = TCPHealthCheck(port=59999, timeout=1.0)
        result = await check.check()
        assert result is False


class TestHealthChecker:
    """Tests for HealthChecker orchestrator."""

    @pytest.mark.asyncio
    async def test_initial_state(self):
        """Test initial health state is unknown."""
        check = TCPHealthCheck(port=59999)
        checker = HealthChecker(check, interval=0.1)
        assert checker.health == Health.UNKNOWN

    @pytest.mark.asyncio
    async def test_start_sets_waiting(self):
        """Test that starting sets health to waiting."""
        check = TCPHealthCheck(port=59999)
        checker = HealthChecker(check, interval=0.1, initial_timeout=0.5)

        await checker.start()
        # Give it a moment to start
        await asyncio.sleep(0.05)
        assert checker.health == Health.WAITING

        await checker.stop()

    @pytest.mark.asyncio
    async def test_stop_resets_to_unknown(self):
        """Test that stopping resets health to unknown."""
        check = TCPHealthCheck(port=59999)
        checker = HealthChecker(check, interval=0.1)

        await checker.start()
        await asyncio.sleep(0.05)
        await checker.stop()

        assert checker.health == Health.UNKNOWN

    @pytest.mark.asyncio
    async def test_becomes_unhealthy_after_timeout(self):
        """Test health becomes unhealthy after initial timeout."""
        check = TCPHealthCheck(port=59999, timeout=0.1)
        checker = HealthChecker(check, interval=0.1, initial_timeout=0.3)

        await checker.start()
        # Wait longer than initial timeout
        await asyncio.sleep(0.5)

        assert checker.health == Health.UNHEALTHY

        await checker.stop()


class TestCreateHealthChecker:
    """Tests for create_health_checker factory."""

    def test_create_http_checker(self):
        """Test creating HTTP health checker."""
        checker = create_health_checker(
            check_type="http",
            port=8080,
            path="/health",
            timeout=30,
            interval=2,
        )
        assert isinstance(checker.check, HTTPHealthCheck)

    def test_create_tcp_checker(self):
        """Test creating TCP health checker."""
        checker = create_health_checker(
            check_type="tcp",
            port=8080,
            timeout=30,
            interval=2,
        )
        assert isinstance(checker.check, TCPHealthCheck)

    def test_invalid_check_type(self):
        """Test error for invalid check type."""
        with pytest.raises(ValueError, match="Unknown health check type"):
            create_health_checker(
                check_type="invalid",
                port=8080,
            )
