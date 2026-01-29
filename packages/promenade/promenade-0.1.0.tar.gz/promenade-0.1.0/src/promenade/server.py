"""FastAPI application for Promenade."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import create_router
from .api.websocket import create_websocket_router

if TYPE_CHECKING:
    from .supervisor import Supervisor


def create_app(supervisor: Supervisor) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Promenade",
        description="Local development process manager",
        version="0.1.0",
    )

    # Permissive CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(
        create_router(supervisor),
        prefix="/api",
        tags=["api"],
    )

    # Include WebSocket routes
    app.include_router(
        create_websocket_router(supervisor.log_aggregator),
        prefix="/api",
        tags=["websocket"],
    )

    # Serve static UI files if they exist
    ui_path = Path(__file__).parent / "ui" / "static"
    if ui_path.exists() and ui_path.is_dir():
        # Check if index.html exists
        if (ui_path / "index.html").exists():
            app.mount("/", StaticFiles(directory=ui_path, html=True), name="ui")

    return app
