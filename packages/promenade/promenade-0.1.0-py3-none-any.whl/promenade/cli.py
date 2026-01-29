"""CLI interface for Promenade."""

from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import ConfigError, load_config
from .logs import LogAggregator
from .server import create_app
from .supervisor import Supervisor

PID_FILE = Path.home() / ".config" / "promenade" / "promenade.pid"

app = typer.Typer(
    name="promenade",
    help="Local development process manager",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"Promenade v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Promenade - Local development process manager."""
    pass


@app.command()
def start(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
    port: Optional[int] = typer.Option(
        None,
        "--port",
        "-p",
        help="Override web UI port",
    ),
    no_ui: bool = typer.Option(
        False,
        "--no-ui",
        help="Disable web UI (CLI only)",
    ),
    daemon: bool = typer.Option(
        False,
        "--daemon",
        "-d",
        help="Run in background (daemon mode)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Verbose logging",
    ),
) -> None:
    """Start Promenade and all configured services."""
    # Check if already running
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)  # Check if process exists
            console.print(f"[yellow]Promenade already running (PID {pid})[/yellow]")
            console.print("Use 'promenade stop' to stop it first")
            raise typer.Exit(1)
        except (ProcessLookupError, ValueError):
            # Process not running, clean up stale PID file
            PID_FILE.unlink(missing_ok=True)

    try:
        cfg = load_config(config)
    except ConfigError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    if port:
        cfg.manager.port = port

    # Daemon mode: spawn background process
    if daemon:
        log_file = Path.home() / ".config" / "promenade" / "promenade.log"
        cmd = [sys.executable, "-m", "promenade", "start"]
        if config:
            cmd.extend(["--config", str(config)])
        if port:
            cmd.extend(["--port", str(port)])
        if no_ui:
            cmd.append("--no-ui")
        if verbose:
            cmd.append("--verbose")

        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=log,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )

        # Wait briefly to check if process started successfully
        import time
        time.sleep(0.5)
        if process.poll() is not None:
            console.print(f"[red]Daemon failed to start. Check log:[/red] {log_file}")
            raise typer.Exit(1)

        # Child will write its own PID file, but we can report the PID
        console.print(f"[green]Promenade started in background (PID {process.pid})[/green]")
        console.print(f"[green]Log file:[/green] {log_file}")
        console.print(f"[green]Web UI:[/green] http://{cfg.manager.host}:{cfg.manager.port}")
        console.print("\nUse 'promenade stop' to stop, 'promenade status' to check")
        return

    # Write PID file for foreground mode too
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))

    console.print(f"[green]Loaded config:[/green] {cfg.config_path}")
    console.print(f"[green]Services:[/green] {', '.join(cfg.services.keys())}")

    if not no_ui:
        console.print(
            f"[green]Web UI:[/green] http://{cfg.manager.host}:{cfg.manager.port}"
        )

    async def run() -> None:
        log_aggregator = LogAggregator(buffer_size=cfg.manager.log_buffer_lines)
        supervisor = Supervisor(cfg, log_aggregator)

        # Set up signal handlers for graceful shutdown
        shutdown_event = asyncio.Event()

        def signal_handler() -> None:
            console.print("\n[yellow]Shutting down...[/yellow]")
            shutdown_event.set()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        # Start all services
        await supervisor.start_all()

        if no_ui:
            # Wait for shutdown signal
            await shutdown_event.wait()
        else:
            # Run FastAPI server
            fast_app = create_app(supervisor)
            config_obj = uvicorn.Config(
                fast_app,
                host=cfg.manager.host,
                port=cfg.manager.port,
                log_level="warning" if not verbose else "info",
            )
            server = uvicorn.Server(config_obj)

            # Run server until shutdown
            server_task = asyncio.create_task(server.serve())
            shutdown_task = asyncio.create_task(shutdown_event.wait())

            done, pending = await asyncio.wait(
                [server_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            # If server exited first (e.g., error), don't wait for shutdown
            if server_task in done:
                server_task.result()  # Re-raise any exception

        # Stop all services
        await supervisor.stop_all()

        # Clean up PID file
        PID_FILE.unlink(missing_ok=True)

    asyncio.run(run())


@app.command()
def status(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Show status of all services (from a running instance)."""
    try:
        cfg = load_config(config)
    except ConfigError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    import httpx

    url = f"http://{cfg.manager.host}:{cfg.manager.port}/api/status"

    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
    except httpx.ConnectError:
        console.print("[red]Promenade is not running[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error connecting:[/red] {e}")
        raise typer.Exit(1)

    # Display services in a table
    table = Table(title="Services")
    table.add_column("Name", style="cyan")
    table.add_column("Status")
    table.add_column("Health")
    table.add_column("PID")
    table.add_column("URL")

    status_colors = {
        "running": "green",
        "stopped": "dim",
        "failed": "red",
        "gave_up": "red",
        "starting": "yellow",
        "stopping": "yellow",
        "pending": "dim",
        "retrying": "yellow",
    }

    health_colors = {
        "healthy": "green",
        "unhealthy": "red",
        "waiting": "yellow",
        "unknown": "dim",
    }

    for name, service in data["services"].items():
        status_str = service["status"]
        status_color = status_colors.get(status_str, "white")
        health_str = service["health"]
        health_color = health_colors.get(health_str, "white")

        table.add_row(
            name,
            f"[{status_color}]{status_str}[/{status_color}]",
            f"[{health_color}]{health_str}[/{health_color}]",
            str(service["pid"]) if service["pid"] else "-",
            service["url"] or "-",
        )

    console.print(table)


@app.command()
def stop(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Stop running Promenade instance."""
    if not PID_FILE.exists():
        console.print("[yellow]Promenade is not running (no PID file)[/yellow]")
        raise typer.Exit(0)

    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError:
        console.print("[red]Invalid PID file[/red]")
        PID_FILE.unlink(missing_ok=True)
        raise typer.Exit(1)

    # Check if process is running
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        console.print("[yellow]Promenade process not found, cleaning up PID file[/yellow]")
        PID_FILE.unlink(missing_ok=True)
        raise typer.Exit(0)

    # Send SIGTERM for graceful shutdown
    console.print(f"[yellow]Stopping Promenade (PID {pid})...[/yellow]")
    try:
        os.kill(pid, signal.SIGTERM)
    except PermissionError:
        console.print("[red]Permission denied. Try running with sudo.[/red]")
        raise typer.Exit(1)

    # Wait for process to exit (up to 10 seconds)
    import time
    for _ in range(20):
        try:
            os.kill(pid, 0)
            time.sleep(0.5)
        except ProcessLookupError:
            break
    else:
        console.print("[yellow]Process still running, sending SIGKILL...[/yellow]")
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    # Clean up PID file
    PID_FILE.unlink(missing_ok=True)
    console.print("[green]Promenade stopped[/green]")


@app.command()
def reload(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Reload configuration (picks up new/changed services)."""
    try:
        cfg = load_config(config)
    except ConfigError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    import httpx

    url = f"http://{cfg.manager.host}:{cfg.manager.port}/api/reload"

    try:
        response = httpx.post(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            console.print(f"[red]Reload failed:[/red] {data['error']}")
            raise typer.Exit(1)

        added = data.get("added", [])
        removed = data.get("removed", [])
        restarted = data.get("restarted", [])

        if added:
            console.print(f"[green]Added:[/green] {', '.join(added)}")
        if removed:
            console.print(f"[yellow]Removed:[/yellow] {', '.join(removed)}")
        if restarted:
            console.print(f"[blue]Restarted:[/blue] {', '.join(restarted)}")
        if not added and not removed and not restarted:
            console.print("[dim]No changes detected[/dim]")

        console.print("[green]Config reloaded[/green]")
    except httpx.ConnectError:
        console.print("[red]Promenade is not running[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def restart(
    service: Optional[str] = typer.Argument(
        None,
        help="Service name to restart (all if not specified)",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Restart a service or all services."""
    try:
        cfg = load_config(config)
    except ConfigError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    import httpx

    base_url = f"http://{cfg.manager.host}:{cfg.manager.port}/api"

    try:
        if service:
            response = httpx.post(f"{base_url}/services/{service}/restart", timeout=10.0)
        else:
            # Restart all services
            status_resp = httpx.get(f"{base_url}/status", timeout=5.0)
            status_resp.raise_for_status()
            services = status_resp.json()["services"].keys()
            for svc in services:
                response = httpx.post(f"{base_url}/services/{svc}/restart", timeout=10.0)
            console.print("[green]All services restarting[/green]")
            return

        response.raise_for_status()
        console.print(f"[green]Service '{service}' restarting[/green]")
    except httpx.ConnectError:
        console.print("[red]Promenade is not running[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Service not found:[/red] {service}")
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def logs(
    service: Optional[str] = typer.Argument(
        None,
        help="Service name (all if not specified)",
    ),
    follow: bool = typer.Option(
        False,
        "-f",
        "--follow",
        help="Follow log output",
    ),
    lines: int = typer.Option(
        50,
        "-n",
        "--lines",
        help="Number of lines to show",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """View service logs."""
    try:
        cfg = load_config(config)
    except ConfigError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    import httpx

    base_url = f"http://{cfg.manager.host}:{cfg.manager.port}/api"

    try:
        if service:
            response = httpx.get(
                f"{base_url}/services/{service}/logs",
                params={"limit": lines},
                timeout=5.0,
            )
            response.raise_for_status()
            data = response.json()
            for line in data["lines"]:
                _print_log_line(line)
        else:
            # Get logs for all services
            status_resp = httpx.get(f"{base_url}/status", timeout=5.0)
            status_resp.raise_for_status()
            services = list(status_resp.json()["services"].keys())

            all_logs = []
            for svc in services:
                resp = httpx.get(
                    f"{base_url}/services/{svc}/logs",
                    params={"limit": lines},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    all_logs.extend(resp.json()["lines"])

            # Sort by timestamp and show most recent
            all_logs.sort(key=lambda x: x["timestamp"])
            for line in all_logs[-lines:]:
                _print_log_line(line)

        if follow:
            _follow_logs(cfg, service)

    except httpx.ConnectError:
        console.print("[red]Promenade is not running[/red]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Service not found:[/red] {service}")
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _print_log_line(line: dict) -> None:
    """Print a formatted log line."""
    ts = line["timestamp"][:19].replace("T", " ")
    service = line["service"]
    stream = line["stream"]
    text = line["line"]

    if stream == "stderr":
        console.print(f"[dim]{ts}[/dim] [cyan]{service}[/cyan] [red]{text}[/red]")
    else:
        console.print(f"[dim]{ts}[/dim] [cyan]{service}[/cyan] {text}")


def _follow_logs(cfg, service: Optional[str]) -> None:
    """Follow logs via WebSocket."""
    import websockets.sync.client as ws_client

    ws_url = f"ws://{cfg.manager.host}:{cfg.manager.port}/api/logs/stream"
    if service:
        ws_url += f"?services={service}"

    try:
        with ws_client.connect(ws_url) as websocket:
            console.print("[dim]Following logs... (Ctrl+C to stop)[/dim]")
            while True:
                try:
                    message = websocket.recv()
                    import json

                    line = json.loads(message)
                    _print_log_line(line)
                except KeyboardInterrupt:
                    break
    except Exception as e:
        console.print(f"[red]WebSocket error:[/red] {e}")


@app.command("config")
def config_cmd(
    check: bool = typer.Option(
        False,
        "--check",
        help="Validate config file",
    ),
    path: bool = typer.Option(
        False,
        "--path",
        help="Print resolved config path",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config file",
    ),
) -> None:
    """Configuration management commands."""
    try:
        cfg = load_config(config)
    except ConfigError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    if path:
        console.print(str(cfg.config_path))
        return

    if check:
        console.print(f"[green]Config valid:[/green] {cfg.config_path}")
        console.print(f"  Services: {', '.join(cfg.services.keys())}")
        return

    # Default: show config summary
    console.print(f"[green]Config:[/green] {cfg.config_path}")
    console.print(f"[green]Manager:[/green] {cfg.manager.host}:{cfg.manager.port}")
    console.print(f"[green]Services:[/green]")
    for name, svc in cfg.services.items():
        console.print(f"  - {name}: {svc.command}")


if __name__ == "__main__":
    app()
