"""Tests for process supervision."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from promenade.config import Config, DefaultsConfig, ManagerConfig, RestartPolicy, ServiceConfig
from promenade.logs import LogAggregator
from promenade.supervisor import ServiceState, Status, Supervisor


def make_config(services: dict[str, ServiceConfig]) -> Config:
    """Helper to create a Config object."""
    return Config(
        manager=ManagerConfig(),
        defaults=DefaultsConfig(),
        services=services,
        config_path=Path("/tmp/test.yaml"),
    )


class TestServiceState:
    """Tests for ServiceState dataclass."""

    def test_initial_state(self):
        """Test initial service state."""
        config = ServiceConfig(name="test", command="echo hello")
        state = ServiceState(config=config)

        assert state.status == Status.PENDING
        assert state.pid is None
        assert state.restart_count == 0

    def test_uptime_when_not_running(self):
        """Test uptime is None when not running."""
        config = ServiceConfig(name="test", command="echo hello")
        state = ServiceState(config=config)
        assert state.uptime_seconds is None

    def test_to_dict(self):
        """Test serialization to dict."""
        config = ServiceConfig(name="test", command="echo hello", port=8080)
        state = ServiceState(config=config, status=Status.RUNNING, pid=12345)

        d = state.to_dict()
        assert d["name"] == "test"
        assert d["status"] == "running"
        assert d["pid"] == 12345
        assert d["port"] == 8080
        assert d["command"] == "echo hello"


class TestSupervisor:
    """Tests for Supervisor class."""

    def test_init_creates_states(self):
        """Test that init creates states for all services."""
        services = {
            "api": ServiceConfig(name="api", command="flask run"),
            "web": ServiceConfig(name="web", command="npm start"),
        }
        config = make_config(services)
        supervisor = Supervisor(config)

        assert "api" in supervisor.get_all_states()
        assert "web" in supervisor.get_all_states()

    def test_get_state(self):
        """Test getting state for a specific service."""
        services = {
            "api": ServiceConfig(name="api", command="flask run"),
        }
        config = make_config(services)
        supervisor = Supervisor(config)

        state = supervisor.get_state("api")
        assert state is not None
        assert state.config.name == "api"

        assert supervisor.get_state("nonexistent") is None

    def test_start_order_no_deps(self):
        """Test start order with no dependencies."""
        services = {
            "a": ServiceConfig(name="a", command="cmd"),
            "b": ServiceConfig(name="b", command="cmd"),
            "c": ServiceConfig(name="c", command="cmd"),
        }
        config = make_config(services)
        supervisor = Supervisor(config)

        order = supervisor._get_start_order()
        # All services should be in the order
        assert set(order) == {"a", "b", "c"}

    def test_start_order_with_deps(self):
        """Test start order respects dependencies."""
        services = {
            "web": ServiceConfig(name="web", command="npm", depends_on=["api"]),
            "api": ServiceConfig(name="api", command="flask", depends_on=["db"]),
            "db": ServiceConfig(name="db", command="postgres"),
        }
        config = make_config(services)
        supervisor = Supervisor(config)

        order = supervisor._get_start_order()

        # db must come before api, api must come before web
        assert order.index("db") < order.index("api")
        assert order.index("api") < order.index("web")

    def test_start_order_complex_deps(self):
        """Test start order with complex dependency graph."""
        services = {
            "a": ServiceConfig(name="a", command="cmd", depends_on=["b", "c"]),
            "b": ServiceConfig(name="b", command="cmd", depends_on=["d"]),
            "c": ServiceConfig(name="c", command="cmd", depends_on=["d"]),
            "d": ServiceConfig(name="d", command="cmd"),
        }
        config = make_config(services)
        supervisor = Supervisor(config)

        order = supervisor._get_start_order()

        # d must come before b and c
        assert order.index("d") < order.index("b")
        assert order.index("d") < order.index("c")
        # b and c must come before a
        assert order.index("b") < order.index("a")
        assert order.index("c") < order.index("a")

    def test_log_aggregator_created_if_not_provided(self):
        """Test that a LogAggregator is created if not provided."""
        services = {
            "api": ServiceConfig(name="api", command="flask run"),
        }
        config = make_config(services)
        supervisor = Supervisor(config)

        assert supervisor.log_aggregator is not None

    def test_log_aggregator_uses_config_buffer_size(self):
        """Test that LogAggregator uses configured buffer size."""
        services = {
            "api": ServiceConfig(name="api", command="flask run"),
        }
        config = Config(
            manager=ManagerConfig(log_buffer_lines=500),
            defaults=DefaultsConfig(),
            services=services,
            config_path=Path("/tmp/test.yaml"),
        )
        supervisor = Supervisor(config)

        # The aggregator should use the configured buffer size
        assert supervisor.log_aggregator._buffer_size == 500

    def test_provided_log_aggregator_is_used(self):
        """Test that provided LogAggregator is used."""
        services = {
            "api": ServiceConfig(name="api", command="flask run"),
        }
        config = make_config(services)
        aggregator = LogAggregator(buffer_size=100)
        supervisor = Supervisor(config, log_aggregator=aggregator)

        assert supervisor.log_aggregator is aggregator


class TestRestartPolicy:
    """Tests for restart policy behavior."""

    @pytest.fixture
    def supervisor_with_service(self):
        """Create a supervisor with a single service for testing."""
        def _create(restart_policy: RestartPolicy):
            services = {
                "test": ServiceConfig(
                    name="test",
                    command="echo hello",
                    restart_policy=restart_policy,
                ),
            }
            config = make_config(services)
            return Supervisor(config)
        return _create

    @pytest.mark.asyncio
    async def test_never_policy_sets_failed(self, supervisor_with_service):
        """Test that restart_policy=never sets status to FAILED."""
        supervisor = supervisor_with_service(RestartPolicy.NEVER)
        state = supervisor.get_state("test")

        await supervisor._handle_failed_exit(state)

        assert state.status == Status.FAILED
        assert state.restart_count == 0

    @pytest.mark.asyncio
    async def test_once_policy_retries_first_failure(self, supervisor_with_service):
        """Test that restart_policy=once retries on first failure."""
        supervisor = supervisor_with_service(RestartPolicy.ONCE)
        state = supervisor.get_state("test")

        with patch.object(supervisor, '_start_service_internal', new_callable=AsyncMock) as mock_start:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await supervisor._handle_failed_exit(state)

        assert state.status == Status.RETRYING
        assert state.restart_count == 1
        mock_start.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_once_policy_gives_up_after_retry(self, supervisor_with_service):
        """Test that restart_policy=once gives up after one retry."""
        supervisor = supervisor_with_service(RestartPolicy.ONCE)
        state = supervisor.get_state("test")
        state.restart_count = 1  # Already retried once

        await supervisor._handle_failed_exit(state)

        assert state.status == Status.GAVE_UP
        assert state.restart_count == 1  # Unchanged

    @pytest.mark.asyncio
    async def test_always_policy_retries(self, supervisor_with_service):
        """Test that restart_policy=always retries."""
        supervisor = supervisor_with_service(RestartPolicy.ALWAYS)
        state = supervisor.get_state("test")

        with patch.object(supervisor, '_start_service_internal', new_callable=AsyncMock) as mock_start:
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await supervisor._handle_failed_exit(state)

        assert state.status == Status.RETRYING
        assert state.restart_count == 1
        mock_start.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_always_policy_exponential_backoff(self, supervisor_with_service):
        """Test that restart_policy=always uses exponential backoff."""
        supervisor = supervisor_with_service(RestartPolicy.ALWAYS)
        state = supervisor.get_state("test")

        delays = []
        with patch.object(supervisor, '_start_service_internal', new_callable=AsyncMock):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                # Simulate multiple failures
                for _ in range(5):
                    await supervisor._handle_failed_exit(state)
                    delays.append(mock_sleep.call_args[0][0])

        # Backoff: 1, 2, 4, 8, 16 seconds
        assert delays == [1, 2, 4, 8, 16]
        assert state.restart_count == 5

    @pytest.mark.asyncio
    async def test_always_policy_backoff_caps_at_30s(self, supervisor_with_service):
        """Test that exponential backoff caps at 30 seconds."""
        supervisor = supervisor_with_service(RestartPolicy.ALWAYS)
        state = supervisor.get_state("test")
        state.restart_count = 10  # Already retried many times

        with patch.object(supervisor, '_start_service_internal', new_callable=AsyncMock):
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                await supervisor._handle_failed_exit(state)

        # 2^10 = 1024, but should cap at 30
        assert mock_sleep.call_args[0][0] == 30

    @pytest.mark.asyncio
    async def test_always_policy_respects_status_change_during_sleep(self, supervisor_with_service):
        """Test that restart is skipped if status changes during backoff sleep."""
        supervisor = supervisor_with_service(RestartPolicy.ALWAYS)
        state = supervisor.get_state("test")

        async def change_status_during_sleep(delay):
            # Simulate user stopping the service during backoff
            state.status = Status.STOPPING

        with patch.object(supervisor, '_start_service_internal', new_callable=AsyncMock) as mock_start:
            with patch('asyncio.sleep', side_effect=change_status_during_sleep):
                await supervisor._handle_failed_exit(state)

        # Should not attempt restart since status changed
        mock_start.assert_not_called()
