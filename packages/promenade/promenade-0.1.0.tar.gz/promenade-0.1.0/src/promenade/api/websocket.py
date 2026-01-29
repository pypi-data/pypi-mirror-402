"""WebSocket log streaming for Promenade."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from ..logs import LogAggregator, LogLine


def create_websocket_router(log_aggregator: LogAggregator) -> APIRouter:
    """Create WebSocket router for log streaming."""
    router = APIRouter()

    @router.websocket("/logs/stream")
    async def log_stream(
        websocket: WebSocket,
        services: str | None = Query(default=None),
    ) -> None:
        """Stream logs via WebSocket.

        Query params:
            services: Comma-separated list of service names to filter.
                      If not provided, streams all services.
        """
        await websocket.accept()

        # Parse service filter
        service_filter: list[str] | None = None
        if services:
            service_filter = [s.strip() for s in services.split(",") if s.strip()]

        # Subscribe to log aggregator
        async def on_log(line: LogLine) -> None:
            if service_filter is None or line.service in service_filter:
                try:
                    await websocket.send_json(line.to_dict())
                except Exception:
                    # Connection closed or error
                    pass

        unsubscribe = log_aggregator.subscribe(on_log)

        try:
            # Keep connection alive, handle any client messages
            while True:
                # Wait for messages from client (ping/pong or close)
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
        except WebSocketDisconnect:
            pass
        finally:
            unsubscribe()

    return router
