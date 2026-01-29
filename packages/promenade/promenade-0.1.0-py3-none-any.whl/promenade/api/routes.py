"""REST API routes for Promenade."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException

if TYPE_CHECKING:
    from ..supervisor import Supervisor


def create_router(supervisor: Supervisor) -> APIRouter:
    """Create API router with supervisor dependency."""
    router = APIRouter()

    @router.get("/status")
    async def get_status() -> dict:
        """Get status of all services."""
        states = supervisor.get_all_states()
        config = supervisor.config

        return {
            "services": {name: state.to_dict() for name, state in states.items()},
            "config_path": str(config.config_path),
            "config_last_modified": datetime.fromtimestamp(
                config.config_path.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
            "manager_uptime_seconds": supervisor.uptime_seconds,
        }

    @router.get("/services/{name}")
    async def get_service(name: str) -> dict:
        """Get details for a specific service."""
        state = supervisor.get_state(name)
        if not state:
            raise HTTPException(status_code=404, detail=f"Service not found: {name}")
        return state.to_dict()

    @router.post("/services/{name}/start")
    async def start_service(name: str) -> dict:
        """Start a service."""
        state = supervisor.get_state(name)
        if not state:
            raise HTTPException(status_code=404, detail=f"Service not found: {name}")

        await supervisor.start_service(name)
        return {"status": "starting", "service": name}

    @router.post("/services/{name}/stop")
    async def stop_service(name: str) -> dict:
        """Stop a service."""
        state = supervisor.get_state(name)
        if not state:
            raise HTTPException(status_code=404, detail=f"Service not found: {name}")

        await supervisor.stop_service(name)
        return {"status": "stopping", "service": name}

    @router.post("/services/{name}/restart")
    async def restart_service(name: str) -> dict:
        """Restart a service."""
        state = supervisor.get_state(name)
        if not state:
            raise HTTPException(status_code=404, detail=f"Service not found: {name}")

        await supervisor.restart_service(name)
        return {"status": "restarting", "service": name}

    @router.get("/services/{name}/logs")
    async def get_service_logs(name: str, limit: int = 100) -> dict:
        """Get log buffer for a service."""
        state = supervisor.get_state(name)
        if not state:
            raise HTTPException(status_code=404, detail=f"Service not found: {name}")

        logs = supervisor.log_aggregator.get_service_logs(name, limit=limit)
        return {
            "service": name,
            "lines": [log.to_dict() for log in logs],
            "count": len(logs),
        }

    @router.get("/config")
    async def get_config() -> dict:
        """Get current parsed configuration."""
        config = supervisor.config
        return {
            "manager": {
                "port": config.manager.port,
                "host": config.manager.host,
                "log_buffer_lines": config.manager.log_buffer_lines,
            },
            "services": {
                name: {
                    "command": svc.command,
                    "directory": str(svc.directory),
                    "port": svc.port,
                    "hostname": svc.hostname,
                    "depends_on": svc.depends_on,
                    "restart_policy": svc.restart_policy.value,
                    "ready_check": (
                        {
                            "type": svc.ready_check.type.value,
                            "path": svc.ready_check.path,
                            "timeout": svc.ready_check.timeout,
                            "interval": svc.ready_check.interval,
                        }
                        if svc.ready_check
                        else None
                    ),
                }
                for name, svc in config.services.items()
            },
            "config_path": str(config.config_path),
        }

    @router.post("/reload")
    async def reload_config() -> dict:
        """Reload configuration and apply changes."""
        result = await supervisor.reload_config()
        return {"status": "ok", **result}

    return router
