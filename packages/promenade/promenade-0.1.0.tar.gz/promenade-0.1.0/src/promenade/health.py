"""Health checking for Promenade services."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from enum import Enum

import httpx


class Health(str, Enum):
    """Health state of a service."""

    UNKNOWN = "unknown"  # No health check configured
    WAITING = "waiting"  # Process running, health check not passed yet
    HEALTHY = "healthy"  # Health check passed
    UNHEALTHY = "unhealthy"  # Health check failing


class HealthCheck(ABC):
    """Base class for health checks."""

    @abstractmethod
    async def check(self) -> bool:
        """Perform health check.

        Returns:
            True if healthy, False otherwise.
        """
        pass


class HTTPHealthCheck(HealthCheck):
    """HTTP health check - checks if a URL returns a successful status code."""

    def __init__(self, port: int, path: str = "/", timeout: float = 5.0):
        self.url = f"http://127.0.0.1:{port}{path}"
        self.timeout = timeout

    async def check(self) -> bool:
        """Check if HTTP endpoint returns a successful status code."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.url, timeout=self.timeout)
                return 200 <= response.status_code < 400
        except (httpx.RequestError, httpx.TimeoutException):
            return False


class TCPHealthCheck(HealthCheck):
    """TCP health check - checks if a TCP connection can be established."""

    def __init__(self, port: int, timeout: float = 5.0):
        self.port = port
        self.timeout = timeout

    async def check(self) -> bool:
        """Check if TCP connection can be established."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", self.port),
                timeout=self.timeout,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (OSError, asyncio.TimeoutError):
            return False


class HealthChecker:
    """Manages health checking for a service."""

    def __init__(
        self,
        check: HealthCheck,
        interval: float = 2.0,
        initial_timeout: float = 30.0,
    ):
        self.check = check
        self.interval = interval
        self.initial_timeout = initial_timeout
        self._task: asyncio.Task | None = None
        self._health = Health.UNKNOWN
        self._should_stop = False

    @property
    def health(self) -> Health:
        """Current health state."""
        return self._health

    async def start(self) -> None:
        """Start health checking loop."""
        self._should_stop = False
        self._health = Health.WAITING
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        """Stop health checking."""
        self._should_stop = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._health = Health.UNKNOWN

    async def _run_loop(self) -> None:
        """Run health check loop until stopped or healthy."""
        start_time = asyncio.get_event_loop().time()

        while not self._should_stop:
            is_healthy = await self.check.check()

            if is_healthy:
                self._health = Health.HEALTHY
            else:
                elapsed = asyncio.get_event_loop().time() - start_time
                if self._health == Health.HEALTHY:
                    # Was healthy, now failing
                    self._health = Health.UNHEALTHY
                elif elapsed > self.initial_timeout and self._health == Health.WAITING:
                    # Timed out waiting for initial health
                    self._health = Health.UNHEALTHY

            await asyncio.sleep(self.interval)


def create_health_checker(
    check_type: str,
    port: int,
    path: str = "/",
    timeout: float = 30.0,
    interval: float = 2.0,
) -> HealthChecker:
    """Create a health checker based on configuration.

    Args:
        check_type: "http" or "tcp"
        port: Port to check
        path: Path for HTTP checks
        timeout: Initial timeout before marking unhealthy
        interval: Interval between checks

    Returns:
        Configured HealthChecker instance.
    """
    if check_type == "http":
        check = HTTPHealthCheck(port, path)
    elif check_type == "tcp":
        check = TCPHealthCheck(port)
    else:
        raise ValueError(f"Unknown health check type: {check_type}")

    return HealthChecker(check, interval=interval, initial_timeout=timeout)
