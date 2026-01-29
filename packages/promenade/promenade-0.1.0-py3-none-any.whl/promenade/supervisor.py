"""Process supervision for Promenade."""

from __future__ import annotations

import asyncio
import os
import signal
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .config import Config, RestartPolicy, ServiceConfig, ServiceType, get_merged_env, load_config
from .health import Health, HealthChecker, create_health_checker
from .logs import LogAggregator, LogLine, Stream, create_log_line
from .static import StaticFileServer


class Status(str, Enum):
    """Process lifecycle status."""

    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RETRYING = "retrying"
    GAVE_UP = "gave_up"


@dataclass
class ServiceState:
    """Runtime state for a service."""

    config: ServiceConfig
    status: Status = Status.PENDING
    health: Health = Health.UNKNOWN
    pid: int | None = None
    process: asyncio.subprocess.Process | None = None
    restart_count: int = 0
    started_at: datetime | None = None
    last_exit_code: int | None = None
    _health_checker: HealthChecker | None = field(default=None, repr=False)
    _output_tasks: list[asyncio.Task] = field(default_factory=list, repr=False)
    _static_server: StaticFileServer | None = field(default=None, repr=False)

    @property
    def uptime_seconds(self) -> float | None:
        """Seconds since service started, or None if not running."""
        if self.started_at is None or self.status != Status.RUNNING:
            return None
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        url = None
        if self.config.port:
            host = self.config.hostname or "localhost"
            url = f"http://{host}:{self.config.port}"

        return {
            "name": self.config.name,
            "status": self.status.value,
            "health": self.health.value,
            "pid": self.pid,
            "port": self.config.port,
            "hostname": self.config.hostname,
            "url": url,
            "uptime_seconds": self.uptime_seconds,
            "restart_count": self.restart_count,
            "last_exit_code": self.last_exit_code,
            "command": self.config.command,
        }


class Supervisor:
    """Manages all service lifecycles."""

    def __init__(self, config: Config, log_aggregator: LogAggregator | None = None):
        self.config = config
        self.log_aggregator = log_aggregator or LogAggregator(
            buffer_size=config.manager.log_buffer_lines
        )
        self._states: dict[str, ServiceState] = {}
        self._shutdown_event = asyncio.Event()
        self._started = False
        self._started_at: datetime | None = None

        # Initialize states for all services
        for name, service_config in config.services.items():
            self._states[name] = ServiceState(config=service_config)

    @property
    def uptime_seconds(self) -> float | None:
        """Seconds since supervisor started, or None if not started."""
        if self._started_at is None:
            return None
        return (datetime.now(timezone.utc) - self._started_at).total_seconds()

    def get_state(self, name: str) -> ServiceState | None:
        """Get state for a service."""
        return self._states.get(name)

    def get_all_states(self) -> dict[str, ServiceState]:
        """Get states for all services."""
        return dict(self._states)

    def _get_start_order(self) -> list[str]:
        """Get service names in dependency order (dependencies first)."""
        visited: set[str] = set()
        result: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            service = self.config.services.get(name)
            if service:
                for dep in service.depends_on:
                    visit(dep)
            result.append(name)

        for name in self.config.services:
            visit(name)

        return result

    async def start_all(self) -> None:
        """Start all services in dependency order."""
        self._started = True
        self._started_at = datetime.now(timezone.utc)
        start_order = self._get_start_order()

        await self._log_system(f"Starting {len(start_order)} services...")

        for name in start_order:
            await self.start_service(name, wait_for_deps=True)

        await self._log_system("All services started")

    async def stop_all(self, timeout: float = 5.0) -> None:
        """Stop all running services gracefully."""
        await self._log_system("Stopping all services...")

        # Stop in reverse dependency order
        stop_order = list(reversed(self._get_start_order()))

        tasks = []
        for name in stop_order:
            state = self._states.get(name)
            if state and state.status in (Status.RUNNING, Status.STARTING, Status.RETRYING):
                tasks.append(self._stop_service_internal(state, timeout))

        if tasks:
            await asyncio.gather(*tasks)

        await self._log_system("All services stopped")
        self._shutdown_event.set()

    async def reload_config(self) -> dict:
        """Reload configuration and apply changes.

        Returns:
            Dict with 'added', 'removed', 'restarted' service lists.
        """
        await self._log_system("Reloading configuration...")

        try:
            new_config = load_config(self.config.config_path)
        except Exception as e:
            await self._log_system(f"Config reload failed: {e}")
            return {"error": str(e)}

        old_services = set(self.config.services.keys())
        new_services = set(new_config.services.keys())

        added = new_services - old_services
        removed = old_services - new_services
        common = old_services & new_services

        # Check which common services have changed
        changed = set()
        for name in common:
            old_svc = self.config.services[name]
            new_svc = new_config.services[name]
            # Compare key fields
            if (old_svc.command != new_svc.command or
                old_svc.directory != new_svc.directory or
                old_svc.port != new_svc.port or
                old_svc.env != new_svc.env or
                old_svc.type != new_svc.type or
                old_svc.file != new_svc.file):
                changed.add(name)

        # Stop removed services
        for name in removed:
            state = self._states.get(name)
            if state and state.status in (Status.RUNNING, Status.STARTING, Status.RETRYING):
                await self._log_system(f"Stopping removed service: {name}")
                await self._stop_service_internal(state)
            del self._states[name]

        # Stop changed services
        for name in changed:
            state = self._states.get(name)
            if state and state.status in (Status.RUNNING, Status.STARTING, Status.RETRYING):
                await self._log_system(f"Stopping changed service: {name}")
                await self._stop_service_internal(state)

        # Update config
        self.config = new_config

        # Update state configs for changed services
        for name in changed:
            self._states[name] = ServiceState(config=new_config.services[name])

        # Add new services
        for name in added:
            self._states[name] = ServiceState(config=new_config.services[name])

        # Start new services
        for name in added:
            await self._log_system(f"Starting new service: {name}")
            await self.start_service(name, wait_for_deps=True)

        # Restart changed services
        for name in changed:
            await self._log_system(f"Restarting changed service: {name}")
            await self.start_service(name, wait_for_deps=True)

        result = {
            "added": list(added),
            "removed": list(removed),
            "restarted": list(changed),
        }
        await self._log_system(f"Config reloaded: {len(added)} added, {len(removed)} removed, {len(changed)} restarted")
        return result

    async def start_service(self, name: str, wait_for_deps: bool = True) -> None:
        """Start a specific service."""
        state = self._states.get(name)
        if not state:
            await self._log_system(f"Unknown service: {name}")
            return

        if state.status in (Status.RUNNING, Status.STARTING):
            await self._log_system(f"Service {name} is already running")
            return

        # Wait for dependencies if needed
        if wait_for_deps and state.config.depends_on:
            await self._wait_for_dependencies(state)

        await self._start_service_internal(state)

    async def stop_service(self, name: str, timeout: float = 5.0) -> None:
        """Stop a specific service."""
        state = self._states.get(name)
        if not state:
            await self._log_system(f"Unknown service: {name}")
            return

        if state.status not in (Status.RUNNING, Status.STARTING, Status.RETRYING):
            await self._log_system(f"Service {name} is not running")
            return

        await self._stop_service_internal(state, timeout)

    async def restart_service(self, name: str, timeout: float = 5.0) -> None:
        """Restart a specific service."""
        state = self._states.get(name)
        if not state:
            await self._log_system(f"Unknown service: {name}")
            return

        if state.status in (Status.RUNNING, Status.STARTING, Status.RETRYING):
            await self._stop_service_internal(state, timeout)

        # Reset restart count for manual restart
        state.restart_count = 0
        await self._start_service_internal(state)

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self._shutdown_event.wait()

    async def _wait_for_dependencies(
        self, state: ServiceState, timeout: float = 60.0
    ) -> None:
        """Wait for service dependencies to be running."""
        deps = state.config.depends_on
        if not deps:
            return

        await self._log_service(
            state.config.name, f"Waiting for dependencies: {', '.join(deps)}"
        )

        start_time = asyncio.get_event_loop().time()
        while True:
            all_running = all(
                self._states.get(dep) and self._states[dep].status == Status.RUNNING
                for dep in deps
            )
            if all_running:
                break

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                await self._log_service(
                    state.config.name,
                    f"Dependency timeout after {timeout}s, starting anyway",
                )
                break

            await asyncio.sleep(0.5)

    async def _start_service_internal(self, state: ServiceState) -> None:
        """Internal method to start a service (process or static)."""
        state.status = Status.STARTING
        config = state.config

        # Handle static file services
        if config.type == ServiceType.STATIC:
            await self._start_static_service(state)
            return

        # Handle process services
        await self._log_service(config.name, f"Starting: {config.command}")

        env = get_merged_env(config, self.config.defaults)

        try:
            process = await asyncio.create_subprocess_shell(
                config.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=config.directory,
                env=env,
                start_new_session=True,  # For clean process group shutdown
            )
        except Exception as e:
            state.status = Status.FAILED
            await self._log_service(config.name, f"Failed to start: {e}")
            return

        state.process = process
        state.pid = process.pid
        state.started_at = datetime.now(timezone.utc)
        state.status = Status.RUNNING

        await self._log_service(config.name, f"Started with PID {process.pid}")

        # Start output readers
        if process.stdout:
            task = asyncio.create_task(
                self._read_stream(config.name, process.stdout, Stream.STDOUT)
            )
            state._output_tasks.append(task)
        if process.stderr:
            task = asyncio.create_task(
                self._read_stream(config.name, process.stderr, Stream.STDERR)
            )
            state._output_tasks.append(task)

        # Start health checker if configured
        if config.ready_check:
            state._health_checker = create_health_checker(
                check_type=config.ready_check.type.value,
                port=config.port or 0,
                path=config.ready_check.path,
                timeout=config.ready_check.timeout,
                interval=config.ready_check.interval,
            )
            await state._health_checker.start()
            # Create task to update health state
            asyncio.create_task(self._update_health(state))
        else:
            state.health = Health.UNKNOWN

        # Start exit watcher
        asyncio.create_task(self._watch_exit(state))

    async def _start_static_service(self, state: ServiceState) -> None:
        """Start a static file server."""
        config = state.config

        if not config.file or not config.port:
            state.status = Status.FAILED
            await self._log_service(config.name, "Static service missing file or port")
            return

        if not config.file.exists():
            state.status = Status.FAILED
            await self._log_service(config.name, f"File not found: {config.file}")
            return

        await self._log_service(
            config.name,
            f"Starting static server for {config.file} on port {config.port}"
        )

        try:
            server = StaticFileServer(config.file, config.port)
            await server.start()
        except Exception as e:
            state.status = Status.FAILED
            await self._log_service(config.name, f"Failed to start: {e}")
            return

        state._static_server = server
        state.started_at = datetime.now(timezone.utc)
        state.status = Status.RUNNING
        state.health = Health.HEALTHY  # Static servers are always healthy

        await self._log_service(
            config.name,
            f"Static server running at http://localhost:{config.port}"
        )

    async def _stop_service_internal(
        self, state: ServiceState, timeout: float = 5.0
    ) -> None:
        """Internal method to stop a service (process or static)."""
        state.status = Status.STOPPING
        await self._log_service(state.config.name, "Stopping...")

        # Handle static servers
        if state._static_server:
            await state._static_server.stop()
            state._static_server = None
            state.status = Status.STOPPED
            state.health = Health.UNKNOWN
            state.started_at = None
            await self._log_service(state.config.name, "Stopped")
            return

        if state.process is None:
            state.status = Status.STOPPED
            return

        # Stop health checker
        if state._health_checker:
            await state._health_checker.stop()
            state._health_checker = None

        pid = state.process.pid

        # Send SIGTERM to process group
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass  # Already dead

        # Wait for graceful shutdown
        try:
            await asyncio.wait_for(state.process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Force kill
            await self._log_service(
                state.config.name, "Graceful shutdown timed out, killing..."
            )
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                await state.process.wait()
            except Exception:
                pass

        # Cancel output tasks
        for task in state._output_tasks:
            task.cancel()
        state._output_tasks.clear()

        state.process = None
        state.pid = None
        state.status = Status.STOPPED
        state.health = Health.UNKNOWN
        state.started_at = None

        await self._log_service(state.config.name, "Stopped")

    async def _watch_exit(self, state: ServiceState) -> None:
        """Watch for process exit and handle restart policy."""
        if state.process is None:
            return

        exit_code = await state.process.wait()
        state.last_exit_code = exit_code

        # If we're stopping, don't try to restart
        if state.status == Status.STOPPING:
            return

        await self._log_service(
            state.config.name, f"Process exited with code {exit_code}"
        )

        # Clear process state
        state.process = None
        state.pid = None
        state.started_at = None

        # Stop health checker
        if state._health_checker:
            await state._health_checker.stop()
            state._health_checker = None
            state.health = Health.UNKNOWN

        # Cancel output tasks
        for task in state._output_tasks:
            task.cancel()
        state._output_tasks.clear()

        # Handle based on exit code and restart policy
        if exit_code == 0:
            state.status = Status.STOPPED
            return

        await self._handle_failed_exit(state)

    async def _handle_failed_exit(self, state: ServiceState) -> None:
        """Handle non-zero exit based on restart policy."""
        policy = state.config.restart_policy

        if policy == RestartPolicy.NEVER:
            state.status = Status.FAILED
            await self._log_service(
                state.config.name, "Failed (restart_policy: never)"
            )

        elif policy == RestartPolicy.ONCE:
            if state.restart_count < 1:
                state.status = Status.RETRYING
                state.restart_count += 1
                await self._log_service(
                    state.config.name,
                    f"Retrying (attempt {state.restart_count}/1)...",
                )
                await asyncio.sleep(1)  # Brief delay before retry
                await self._start_service_internal(state)
            else:
                state.status = Status.GAVE_UP
                await self._log_service(
                    state.config.name, "Gave up after 1 retry"
                )

        elif policy == RestartPolicy.ALWAYS:
            state.status = Status.RETRYING
            state.restart_count += 1
            # Exponential backoff: 1s, 2s, 4s, 8s, ... max 30s
            delay = min(2 ** (state.restart_count - 1), 30)
            await self._log_service(
                state.config.name,
                f"Retrying in {delay}s (attempt {state.restart_count})...",
            )
            await asyncio.sleep(delay)
            if state.status == Status.RETRYING:  # Still want to retry
                await self._start_service_internal(state)

    async def _read_stream(
        self, service_name: str, stream: asyncio.StreamReader, stream_type: Stream
    ) -> None:
        """Read lines from stdout/stderr and feed to log aggregator."""
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip("\n")
                log_line = create_log_line(service_name, text, stream_type)
                await self.log_aggregator.add_line(log_line)
        except asyncio.CancelledError:
            pass

    async def _update_health(self, state: ServiceState) -> None:
        """Update service health state from health checker."""
        if not state._health_checker:
            return

        try:
            while state.status == Status.RUNNING and state._health_checker:
                state.health = state._health_checker.health
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass

    async def _log_service(self, service: str, message: str) -> None:
        """Log a message for a service."""
        log_line = create_log_line(service, message, Stream.STDOUT)
        await self.log_aggregator.add_line(log_line)

    async def _log_system(self, message: str) -> None:
        """Log a system message."""
        log_line = create_log_line("promenade", message, Stream.STDOUT)
        await self.log_aggregator.add_line(log_line)
