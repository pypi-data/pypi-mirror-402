# Promenade

A local development process manager with a web UI. Run all your services with one command and see their status, logs, and health in a unified dashboard.

## Installation

```bash
pip install promenade
```

## Quick Start

1. Create a `promenade.yaml` in your project root:

```yaml
services:
  api:
    command: flask run --port 5001
    directory: ./backend
    port: 5001
    ready_check:
      type: http
      path: /health

  frontend:
    command: npm run dev
    directory: ./frontend
    port: 3000
    depends_on:
      - api
```

2. Start everything:

```bash
promenade start
```

3. Open http://localhost:7766 to see the web UI.

## Features

- **Process supervision** - Start, stop, and restart services with automatic dependency ordering
- **Health checks** - HTTP and TCP health checks with configurable timeouts
- **Log aggregation** - Unified log viewer with per-service filtering
- **Web UI** - Real-time dashboard showing service status, health, and logs
- **Hot reload** - Automatically detects config changes and restarts affected services
- **Restart policies** - Configure `never`, `once`, or `always` restart behavior

## CLI Commands

```bash
promenade start              # Start all services (with web UI on port 7766)
promenade start --no-ui      # Start services without the web UI
promenade start --daemon     # Run in background
promenade stop               # Stop all services
promenade status             # Show service status
promenade restart [service]  # Restart a service (or all if no name given)
promenade logs [service]     # View logs
promenade logs -f            # Follow logs in real-time
promenade reload             # Reload config and restart changed services
promenade config check       # Validate your config file
```

## Configuration

Promenade looks for config in this order:
1. `--config` flag
2. `./promenade.yaml`
3. `~/.config/promenade/promenade.yaml`

### Full Example

```yaml
manager:
  port: 7766
  host: 127.0.0.1
  log_buffer_lines: 1000

defaults:
  restart_policy: once
  env:
    NODE_ENV: development

services:
  api:
    command: flask run --port 5001
    directory: ./backend
    port: 5001
    env:
      FLASK_DEBUG: "1"
    ready_check:
      type: http
      path: /health
      timeout: 30
      interval: 2

  frontend:
    command: npm run dev
    directory: ./frontend
    port: 3000
    depends_on:
      - api
    ready_check:
      type: tcp
      timeout: 30

  worker:
    command: python worker.py
    directory: ./backend
    restart_policy: always
```

### Service Options

| Option | Description |
|--------|-------------|
| `command` | Command to run (required) |
| `directory` | Working directory |
| `port` | Port the service listens on |
| `env` | Environment variables |
| `env_file` | Path to .env file |
| `depends_on` | Services that must start first |
| `restart_policy` | `never`, `once`, or `always` |
| `ready_check` | Health check configuration |

### Health Checks

```yaml
ready_check:
  type: http          # or "tcp"
  path: /health       # HTTP only
  timeout: 30         # Seconds to wait for healthy
  interval: 2         # Seconds between checks
```

## Running as a Daemon

For services you always want running, you can set up promenade to start automatically on login.

### macOS (launchd)

Create `~/Library/LaunchAgents/com.promenade.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.promenade</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/promenade</string>
        <string>start</string>
        <string>--no-ui</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/promenade.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/promenade.log</string>
</dict>
</plist>
```

Then load it:

```bash
launchctl load ~/Library/LaunchAgents/com.promenade.plist
```

Find the path to promenade with `which promenade`.

### Linux (systemd)

Create `~/.config/systemd/user/promenade.service`:

```ini
[Unit]
Description=Promenade Dev Services

[Service]
ExecStart=/path/to/promenade start --no-ui
Restart=always

[Install]
WantedBy=default.target
```

Then enable it:

```bash
systemctl --user enable --now promenade
```

## REST API

The manager exposes a REST API at the same port as the web UI:

- `GET /api/status` - All services status
- `GET /api/services/{name}` - Single service status
- `POST /api/services/{name}/start` - Start a service
- `POST /api/services/{name}/stop` - Stop a service
- `POST /api/services/{name}/restart` - Restart a service
- `GET /api/services/{name}/logs` - Get service logs
- `POST /api/reload` - Reload configuration
- `WS /api/logs/stream` - WebSocket for real-time logs

## License

MIT
