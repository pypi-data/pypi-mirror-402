"""Configuration loading and validation for Promenade."""

from __future__ import annotations

import os
import re
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator, model_validator


class RestartPolicy(str, Enum):
    """Restart policy for services."""

    NEVER = "never"
    ONCE = "once"
    ALWAYS = "always"


class ServiceType(str, Enum):
    """Type of service."""

    PROCESS = "process"  # Default: run a command
    STATIC = "static"    # Serve a static file


class HealthCheckType(str, Enum):
    """Type of health check."""

    HTTP = "http"
    TCP = "tcp"


class ReadyCheckConfig(BaseModel):
    """Configuration for service health/ready checks."""

    type: HealthCheckType
    path: str = "/"
    timeout: int = 30
    interval: int = 2


class ServiceConfig(BaseModel):
    """Configuration for a single service."""

    name: str
    type: ServiceType = ServiceType.PROCESS
    command: str | None = None  # Required for process type
    file: Path | None = None    # Required for static type
    directory: Path = Path(".")
    port: int | None = None
    hostname: str | None = None
    env: dict[str, str] = {}
    env_file: Path | None = None
    depends_on: list[str] = []
    restart_policy: RestartPolicy = RestartPolicy.ONCE
    ready_check: ReadyCheckConfig | None = None

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Hostname: letters, numbers, dots, hyphens
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid hostname: {v}")
        return v

    @model_validator(mode="after")
    def validate_service_config(self) -> ServiceConfig:
        if self.hostname is not None and self.port is None:
            raise ValueError("port is required when hostname is specified")

        if self.type == ServiceType.PROCESS and not self.command:
            raise ValueError("command is required for process type services")

        if self.type == ServiceType.STATIC:
            if not self.file:
                raise ValueError("file is required for static type services")
            if not self.port:
                raise ValueError("port is required for static type services")

        return self


class ManagerConfig(BaseModel):
    """Configuration for the Promenade manager."""

    port: int = 7766
    host: str = "127.0.0.1"
    log_buffer_lines: int = 1000
    config_poll_interval: int = 5


class DefaultsConfig(BaseModel):
    """Default configuration values applied to all services."""

    restart_policy: RestartPolicy = RestartPolicy.ONCE
    env: dict[str, str] = {}


class Config(BaseModel):
    """Root configuration for Promenade."""

    manager: ManagerConfig = ManagerConfig()
    defaults: DefaultsConfig = DefaultsConfig()
    services: dict[str, ServiceConfig]
    config_path: Path

    @field_validator("services")
    @classmethod
    def validate_services_not_empty(
        cls, v: dict[str, ServiceConfig]
    ) -> dict[str, ServiceConfig]:
        if not v:
            raise ValueError("At least one service must be defined")
        return v


class ConfigError(Exception):
    """Error in configuration loading or validation."""

    pass


def _detect_dependency_cycles(services: dict[str, ServiceConfig]) -> None:
    """Detect circular dependencies in service configuration."""
    visited: set[str] = set()
    path: set[str] = set()

    def visit(name: str) -> None:
        if name in path:
            raise ConfigError(f"Circular dependency detected involving: {name}")
        if name in visited:
            return

        path.add(name)
        service = services.get(name)
        if service:
            for dep in service.depends_on:
                if dep not in services:
                    raise ConfigError(
                        f"Service '{name}' depends on unknown service '{dep}'"
                    )
                visit(dep)
        path.remove(name)
        visited.add(name)

    for service_name in services:
        visit(service_name)


def _load_env_file(env_file: Path) -> dict[str, str]:
    """Load environment variables from a .env file."""
    env: dict[str, str] = {}
    if not env_file.exists():
        return env

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Remove surrounding quotes if present
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                env[key] = value
    return env


def load_config(config_path: Path | None = None) -> Config:
    """Load and validate configuration from a YAML file.

    Args:
        config_path: Explicit path to config file. If None, searches default locations.

    Returns:
        Validated Config object.

    Raises:
        ConfigError: If config file not found or invalid.
    """
    # Find config file
    if config_path is not None:
        if not config_path.exists():
            raise ConfigError(f"Config file not found: {config_path}")
        resolved_path = config_path.resolve()
    else:
        search_paths = [
            Path.cwd() / "promenade.yaml",
            Path.home() / ".config" / "promenade" / "promenade.yaml",
        ]
        resolved_path = None
        for p in search_paths:
            if p.exists():
                resolved_path = p.resolve()
                break
        if resolved_path is None:
            raise ConfigError(
                "No config file found. Create promenade.yaml or use --config"
            )

    # Load YAML
    with open(resolved_path) as f:
        raw_config: dict[str, Any] = yaml.safe_load(f) or {}

    config_dir = resolved_path.parent

    # Parse manager and defaults
    manager_data = raw_config.get("manager", {})
    defaults_data = raw_config.get("defaults", {})

    manager = ManagerConfig(**manager_data)
    defaults = DefaultsConfig(**defaults_data)

    # Parse services
    raw_services = raw_config.get("services", {})
    if not raw_services:
        raise ConfigError("No services defined in config")

    services: dict[str, ServiceConfig] = {}
    for name, service_data in raw_services.items():
        if not isinstance(service_data, dict):
            raise ConfigError(f"Invalid service definition for '{name}'")

        # Apply defaults
        if "restart_policy" not in service_data:
            service_data["restart_policy"] = defaults.restart_policy.value

        # Merge default env with service env
        merged_env = {**defaults.env, **service_data.get("env", {})}
        service_data["env"] = merged_env

        # Resolve directory relative to config file
        if "directory" in service_data:
            service_data["directory"] = config_dir / service_data["directory"]
        else:
            service_data["directory"] = config_dir

        # Resolve env_file relative to config file
        if "env_file" in service_data and service_data["env_file"]:
            service_data["env_file"] = config_dir / service_data["env_file"]

        # Resolve file path for static services (expand ~ and make absolute)
        if "file" in service_data and service_data["file"]:
            file_path = Path(service_data["file"]).expanduser()
            if not file_path.is_absolute():
                file_path = config_dir / file_path
            service_data["file"] = file_path

        service_data["name"] = name
        services[name] = ServiceConfig(**service_data)

    # Check for circular dependencies
    _detect_dependency_cycles(services)

    return Config(
        manager=manager,
        defaults=defaults,
        services=services,
        config_path=resolved_path,
    )


def get_merged_env(service: ServiceConfig, defaults: DefaultsConfig) -> dict[str, str]:
    """Get merged environment variables for a service.

    Merges in order: system env -> defaults -> service -> env_file
    """
    env = dict(os.environ)
    env.update(defaults.env)
    env.update(service.env)

    if service.env_file:
        env.update(_load_env_file(service.env_file))

    return env
