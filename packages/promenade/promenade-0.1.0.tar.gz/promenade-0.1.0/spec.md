# Promenade: Local Development Process Manager

## Overview

Promenade is a lightweight local development orchestrator that manages multiple web services (Flask, React, static sites, etc.) from a single process with a web-based dashboard. It replaces the need for multiple terminal windows and provides unified log viewing, process control, and optional `/etc/hosts` management for custom local domains.

## Goals

- Single process to manage all local dev services
- Web UI for monitoring, log viewing, and control
- Custom local hostnames via `/etc/hosts` management
- Automatic CORS handling for local-to-local requests
- Hot-reloading of configuration changes
- Simple, file-based configuration

## Non-Goals

- Production deployment (this is a dev tool)
- Container orchestration (use docker-compose for that)
- Remote/distributed process management
- Complex dependency resolution beyond simple ordering

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         Promenade Process                          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Config       │  │ Process      │  │ Hosts Manager        │  │
│  │ Watcher      │  │ Supervisor   │  │ (/etc/hosts writes)  │  │
│  │              │  │              │  │                      │  │
│  │ - Load YAML  │  │ - Start/stop │  │ - Add entries on     │  │
│  │ - Validate   │  │ - Restart    │  │   start              │  │
│  │ - Hot reload │  │ - Health     │  │ - Remove on shutdown │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         ▼                 ▼                      ▼              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Service Registry                       │   │
│  │                                                          │   │
│  │  Tracks: name, command, port, hostname, pid, status,     │   │
│  │          log buffer, restart count, health state         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Web UI Server                         │   │
│  │                                                          │   │
│  │  - REST API for status/control                           │   │
│  │  - WebSocket for live log streaming                      │   │
│  │  - Static dashboard UI                                   │   │
│  │  - CORS middleware (permissive for local)                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Config File Location

Promenade looks for configuration in this order:
1. Path specified via `--config` CLI argument
2. `./promenade.yaml` in current directory
3. `~/.config/promenade/promenade.yaml`

### Config Schema

```yaml
# promenade.yaml

# Manager settings
manager:
  port: 9000                    # Web UI port
  host: 127.0.0.1               # Web UI bind address
  log_buffer_lines: 1000        # Lines to keep per service
  config_poll_interval: 5       # Seconds between config file checks

# Global defaults (can be overridden per-service)
defaults:
  restart_policy: once          # "once", "always", "never"
  env:
    NODE_ENV: development

# Service definitions
services:
  # Flask API example
  api:
    command: flask run --port 5001
    directory: ./backend
    port: 5001                  # Port the service listens on
    hostname: api.local         # Optional: custom hostname
    env:
      FLASK_ENV: development
    env_file: .env.local        # Optional: load env from file

  # React dev server example
  frontend:
    command: npm run dev
    directory: ./client
    port: 3000
    hostname: app.local
    depends_on:                 # Optional: start these first
      - api
    ready_check:                # Optional: wait for this before "healthy"
      type: http
      path: /
      timeout: 30

  # Static site example
  docs:
    command: python -m http.server 8080
    directory: ./docs/build
    port: 8080
    hostname: docs.local

  # Background worker (no port)
  worker:
    command: python worker.py
    directory: ./backend
    restart_policy: always      # Keep this one running
```

### Config Validation Rules

- `services` is required and must have at least one service
- `command` is required for each service
- `port` is required if `hostname` is specified
- `hostname` must be a valid hostname (letters, numbers, dots, hyphens)
- `depends_on` must reference existing service names (no cycles)
- `directory` is resolved relative to config file location

---

## Features

### 1. Process Supervision

#### Lifecycle States

```
PENDING → STARTING → RUNNING → STOPPING → STOPPED
              ↓          ↓
           FAILED ← ← ← ←
              ↓
          RETRYING → RUNNING
              ↓
          GAVE_UP
```

#### Restart Policy

| Policy   | Behavior                                           |
|----------|---------------------------------------------------|
| `never`  | Don't restart on failure                          |
| `once`   | Retry once on failure, then give up (DEFAULT)     |
| `always` | Keep retrying with exponential backoff (max 30s)  |

#### Startup Behavior

1. On `promenade start`, all services auto-start
2. Services with `depends_on` wait for dependencies to reach RUNNING state
3. Dependency timeout: 60 seconds (configurable), then start anyway with warning

#### Shutdown Behavior

1. Send SIGTERM to all processes
2. Wait 5 seconds for graceful shutdown
3. Send SIGKILL to any remaining processes
4. Clean up `/etc/hosts` entries

### 2. Hosts File Management

When a service has a `hostname` configured:

1. On service start: Add `127.0.0.1  {hostname}` to `/etc/hosts`
2. On service stop: Remove the entry
3. On Promenade shutdown: Remove all managed entries

#### Implementation Notes

- Requires sudo/root for `/etc/hosts` writes
- Promenade marks its entries with a comment: `# promenade:{service_name}`
- Example entry: `127.0.0.1  api.local  # promenade:api`
- On startup, clean any stale Promenade entries from previous runs

#### Hosts Management Modes

```yaml
manager:
  hosts_management: auto    # "auto", "manual", "disabled"
```

| Mode       | Behavior                                              |
|------------|-------------------------------------------------------|
| `auto`     | Manage /etc/hosts automatically (needs sudo)          |
| `manual`   | Print instructions for user to add manually           |
| `disabled` | Don't touch /etc/hosts, just use localhost:port       |

### 3. Log Aggregation

- Each service maintains a ring buffer of last N lines (default 1000)
- Logs include stdout and stderr (merged, with stderr marked)
- Each line timestamped with ISO-8601 and service name prefix
- WebSocket endpoint streams logs in real-time

#### Log Line Format

```
2024-01-15T10:23:45.123Z [api] Starting Flask development server...
2024-01-15T10:23:45.456Z [api] * Running on http://127.0.0.1:5001
2024-01-15T10:23:46.789Z [frontend] Starting the development server...
2024-01-15T10:23:47.012Z [api] [stderr] WARNING: This is a development server.
```

### 4. Health Checks

Optional per-service health checking:

```yaml
services:
  api:
    ready_check:
      type: http          # "http" or "tcp"
      path: /health       # For HTTP checks
      timeout: 30         # Seconds to wait for healthy
      interval: 2         # Seconds between checks
```

#### Health States

| State       | Meaning                                    |
|-------------|-------------------------------------------|
| `unknown`   | No health check configured                |
| `waiting`   | Process running, health check not passed  |
| `healthy`   | Health check passed                       |
| `unhealthy` | Health check failing (process still runs) |

### 5. Hot Reload

- Config file is polled every N seconds (default: 5)
- On change detection (mtime or content hash):
  1. Parse and validate new config
  2. Diff against current state
  3. Stop removed services
  4. Start added services
  5. Restart modified services (command, directory, env changed)
  6. Log all changes to UI

#### Hot Reload Safety

- Invalid config: Keep running with old config, show error in UI
- Only restart services whose config actually changed
- Preserve log buffers across restarts when possible

### 6. CORS Handling

The Promenade web UI server includes permissive CORS headers for all responses:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: *
```

For managed services, Promenade can optionally inject a CORS proxy. This is opt-in per service:

```yaml
services:
  api:
    cors_proxy: true      # Proxy requests through Promenade with CORS headers
    cors_proxy_port: 5002 # Promenade listens here, forwards to actual port
```

---

## Web UI

### Dashboard View

```
┌─────────────────────────────────────────────────────────────────┐
│  Promenade                                            [Restart All]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ● api          RUNNING (healthy)     http://api.local   │   │
│  │   flask run    PID 12345             ↗ Open  ⟳  ■ Stop  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ● frontend     RUNNING (healthy)     http://app.local   │   │
│  │   npm run dev  PID 12346             ↗ Open  ⟳  ■ Stop  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ○ worker       STOPPED               —                  │   │
│  │   python work  —                     ▶ Start            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Logs  [All ▾]  [Filter: ________]  [Auto-scroll ✓]            │
├─────────────────────────────────────────────────────────────────┤
│  10:23:45 [api] Starting Flask development server...            │
│  10:23:45 [api] * Running on http://127.0.0.1:5001              │
│  10:23:46 [frontend] Starting the development server...         │
│  10:23:47 [frontend] Compiled successfully!                     │
│  10:23:48 [api] 127.0.0.1 - GET /health 200                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### UI Features

- Service cards showing: name, status, health, URL, PID, controls
- Real-time log viewer with service filter dropdown
- Text search/filter within logs
- Click service URL to open in new tab
- Start/stop/restart individual services
- Restart all button
- Visual indicator when config file changes detected
- Toast notifications for state changes

---

## REST API

### Endpoints

| Method | Path                      | Description                    |
|--------|---------------------------|--------------------------------|
| GET    | `/api/status`             | All services status            |
| GET    | `/api/services/{name}`    | Single service details         |
| POST   | `/api/services/{name}/start`   | Start a service           |
| POST   | `/api/services/{name}/stop`    | Stop a service            |
| POST   | `/api/services/{name}/restart` | Restart a service         |
| GET    | `/api/services/{name}/logs`    | Get log buffer (JSON)     |
| GET    | `/api/config`             | Current parsed config          |
| POST   | `/api/reload`             | Force config reload            |
| WS     | `/api/logs/stream`        | WebSocket for live logs        |

### Status Response

```json
{
  "services": {
    "api": {
      "name": "api",
      "status": "running",
      "health": "healthy",
      "pid": 12345,
      "port": 5001,
      "hostname": "api.local",
      "url": "http://api.local:5001",
      "uptime_seconds": 3456,
      "restart_count": 0,
      "last_exit_code": null
    }
  },
  "config_path": "/home/user/project/promenade.yaml",
  "config_last_modified": "2024-01-15T10:00:00Z",
  "manager_uptime_seconds": 7200
}
```

### WebSocket Log Stream

Connect to `/api/logs/stream?services=api,frontend` (or omit param for all)

Messages are JSON:
```json
{
  "timestamp": "2024-01-15T10:23:45.123Z",
  "service": "api",
  "stream": "stdout",
  "line": "Starting Flask development server..."
}
```

---

## CLI Interface

```bash
# Start manager (foreground, default)
promenade start

# Start manager (background/daemon mode)
promenade start --daemon

# Stop running manager
promenade stop

# Show status of all services
promenade status

# Control individual services
promenade restart api
promenade stop frontend
promenade start worker

# View logs (CLI, without web UI)
promenade logs           # All services
promenade logs api       # Single service
promenade logs -f        # Follow mode

# Config management
promenade config check   # Validate config file
promenade config path    # Print resolved config path

# Hosts file helpers (for manual mode)
promenade hosts show     # Print entries that would be added
promenade hosts add      # Add entries (requires sudo)
promenade hosts remove   # Remove entries (requires sudo)

# Version and help
promenade --version
promenade --help
```

### CLI Options

```
promenade start [OPTIONS]

Options:
  --config, -c PATH     Path to config file
  --port, -p PORT       Override web UI port
  --daemon, -d          Run in background
  --no-ui               Disable web UI (CLI only)
  --verbose, -v         Verbose logging
```

---

## Implementation Notes

### Tech Stack

- **Language**: Python 3.10+
- **Async Framework**: FastAPI + uvicorn
- **Process Management**: asyncio.subprocess
- **WebSocket**: FastAPI native WebSocket support
- **Config Parsing**: PyYAML + Pydantic for validation
- **Web UI**: Vanilla HTML/CSS/JS or lightweight React (single bundle)
- **CLI**: Click or Typer

### File Structure

```
promenade/
├── pyproject.toml
├── README.md
├── src/
│   └── promenade/
│       ├── __init__.py
│       ├── __main__.py          # CLI entry point
│       ├── cli.py               # CLI commands
│       ├── config.py            # Config loading/validation
│       ├── supervisor.py        # Process management
│       ├── hosts.py             # /etc/hosts management
│       ├── logs.py              # Log aggregation
│       ├── health.py            # Health checking
│       ├── server.py            # FastAPI app
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py        # REST endpoints
│       │   └── websocket.py     # Log streaming
│       └── ui/
│           └── static/          # Web UI assets
│               ├── index.html
│               ├── app.js
│               └── style.css
└── tests/
    ├── test_config.py
    ├── test_supervisor.py
    └── test_hosts.py
```

### Key Classes

```python
# Core abstractions

@dataclass
class ServiceConfig:
    name: str
    command: str
    directory: Path
    port: int | None
    hostname: str | None
    env: dict[str, str]
    depends_on: list[str]
    restart_policy: Literal["never", "once", "always"]
    ready_check: ReadyCheck | None

@dataclass
class ServiceState:
    config: ServiceConfig
    status: Status  # enum: pending, starting, running, stopping, stopped, failed, gave_up
    health: Health  # enum: unknown, waiting, healthy, unhealthy
    pid: int | None
    process: asyncio.subprocess.Process | None
    log_buffer: deque[LogLine]
    restart_count: int
    started_at: datetime | None
    last_exit_code: int | None

class Supervisor:
    """Manages all service lifecycles."""
    async def start_all(self) -> None
    async def stop_all(self) -> None
    async def start_service(self, name: str) -> None
    async def stop_service(self, name: str) -> None
    async def restart_service(self, name: str) -> None
    def get_status(self) -> dict[str, ServiceState]

class ConfigWatcher:
    """Monitors config file for changes."""
    async def watch(self, callback: Callable) -> None
    def load(self) -> Config
    def diff(self, old: Config, new: Config) -> ConfigDiff

class HostsManager:
    """Manages /etc/hosts entries."""
    def add_entry(self, hostname: str, service_name: str) -> None
    def remove_entry(self, service_name: str) -> None
    def cleanup_all(self) -> None
```

---

## Security Considerations

1. **Hosts file access**: Requires root/sudo. Options:
   - Run Promenade with sudo (not ideal)
   - Use setuid helper binary (complex)
   - Prompt for sudo password when needed
   - Manual mode (user adds entries themselves)

2. **Command execution**: Config file specifies arbitrary commands. This is intentional (dev tool), but:
   - Only run configs from trusted locations
   - Consider warning if config is world-writable

3. **Web UI binding**: Default to 127.0.0.1 only (not 0.0.0.0)

4. **No auth**: Web UI has no authentication (local dev tool assumption)

---

## Future Considerations (Out of Scope for V1)

- Docker container support (start containers instead of processes)
- Service templates / presets
- Multiple config file profiles
- Shared/team configs
- Resource monitoring (CPU, memory per process)
- Log persistence to disk
- Notifications (desktop, webhook)
- Plugin system

---

## Example Usage

```bash
# Create a config file
cat > promenade.yaml << 'EOF'
manager:
  port: 9000
  hosts_management: auto

services:
  api:
    command: flask run --port 5001
    directory: ./backend
    port: 5001
    hostname: api.myapp.local
    env:
      FLASK_DEBUG: "1"

  web:
    command: npm run dev
    directory: ./frontend
    port: 3000
    hostname: myapp.local
    depends_on: [api]
EOF

# Start everything
sudo promenade start

# Open http://localhost:9000 for dashboard
# Services available at:
#   http://api.myapp.local:5001
#   http://myapp.local:3000
```

---

## Success Criteria

- [ ] Single command starts all services
- [ ] Web UI shows all services with status
- [ ] Can view aggregated logs in real-time
- [ ] Can start/stop/restart individual services from UI
- [ ] Custom hostnames work via /etc/hosts
- [ ] Config changes are detected and applied without full restart
- [ ] Clean shutdown removes all /etc/hosts entries
- [ ] Failed services retry once then stop
