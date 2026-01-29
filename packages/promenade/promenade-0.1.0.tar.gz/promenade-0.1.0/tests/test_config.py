"""Tests for configuration loading and validation."""

import tempfile
from pathlib import Path

import pytest
import yaml

from promenade.config import (
    Config,
    ConfigError,
    DefaultsConfig,
    ManagerConfig,
    ReadyCheckConfig,
    RestartPolicy,
    ServiceConfig,
    _detect_dependency_cycles,
    load_config,
)


class TestServiceConfig:
    """Tests for ServiceConfig model."""

    def test_minimal_service(self):
        """Test creating a service with minimal config."""
        svc = ServiceConfig(name="test", command="echo hello")
        assert svc.name == "test"
        assert svc.command == "echo hello"
        assert svc.port is None
        assert svc.hostname is None
        assert svc.restart_policy == RestartPolicy.ONCE

    def test_full_service(self):
        """Test creating a service with all options."""
        svc = ServiceConfig(
            name="api",
            command="flask run",
            directory=Path("/app"),
            port=5000,
            hostname="api.local",
            env={"FLASK_ENV": "development"},
            depends_on=["db"],
            restart_policy=RestartPolicy.ALWAYS,
        )
        assert svc.port == 5000
        assert svc.hostname == "api.local"
        assert svc.depends_on == ["db"]

    def test_hostname_requires_port(self):
        """Test that hostname requires port to be set."""
        with pytest.raises(ValueError, match="port is required"):
            ServiceConfig(name="test", command="echo", hostname="test.local")

    def test_valid_hostnames(self):
        """Test valid hostname formats."""
        valid_hostnames = [
            "localhost",
            "api.local",
            "my-service.test",
            "a.b.c.d",
            "api-v2.my-app.local",
        ]
        for hostname in valid_hostnames:
            svc = ServiceConfig(
                name="test", command="echo", port=8080, hostname=hostname
            )
            assert svc.hostname == hostname

    def test_invalid_hostnames(self):
        """Test invalid hostname formats."""
        invalid_hostnames = [
            "-invalid",
            "invalid-",
            ".invalid",
            "invalid.",
            "inv@lid",
            "inv lid",
        ]
        for hostname in invalid_hostnames:
            with pytest.raises(ValueError, match="Invalid hostname"):
                ServiceConfig(
                    name="test", command="echo", port=8080, hostname=hostname
                )


class TestDependencyCycles:
    """Tests for dependency cycle detection."""

    def test_no_cycles(self):
        """Test valid dependency chain."""
        services = {
            "web": ServiceConfig(name="web", command="npm start", depends_on=["api"]),
            "api": ServiceConfig(name="api", command="flask run", depends_on=["db"]),
            "db": ServiceConfig(name="db", command="postgres"),
        }
        # Should not raise
        _detect_dependency_cycles(services)

    def test_direct_cycle(self):
        """Test detection of direct cycle."""
        services = {
            "a": ServiceConfig(name="a", command="cmd", depends_on=["b"]),
            "b": ServiceConfig(name="b", command="cmd", depends_on=["a"]),
        }
        with pytest.raises(ConfigError, match="Circular dependency"):
            _detect_dependency_cycles(services)

    def test_indirect_cycle(self):
        """Test detection of indirect cycle."""
        services = {
            "a": ServiceConfig(name="a", command="cmd", depends_on=["b"]),
            "b": ServiceConfig(name="b", command="cmd", depends_on=["c"]),
            "c": ServiceConfig(name="c", command="cmd", depends_on=["a"]),
        }
        with pytest.raises(ConfigError, match="Circular dependency"):
            _detect_dependency_cycles(services)

    def test_missing_dependency(self):
        """Test detection of missing dependency."""
        services = {
            "a": ServiceConfig(name="a", command="cmd", depends_on=["nonexistent"]),
        }
        with pytest.raises(ConfigError, match="unknown service"):
            _detect_dependency_cycles(services)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_minimal_config(self, tmp_path):
        """Test loading a minimal valid config."""
        config_content = """
services:
  web:
    command: python -m http.server
"""
        config_file = tmp_path / "promenade.yaml"
        config_file.write_text(config_content)

        cfg = load_config(config_file)

        assert "web" in cfg.services
        assert cfg.services["web"].command == "python -m http.server"
        assert cfg.manager.port == 9000  # Default

    def test_load_full_config(self, tmp_path):
        """Test loading a config with all options."""
        config_content = """
manager:
  port: 8080
  host: 0.0.0.0
  log_buffer_lines: 500

defaults:
  restart_policy: always
  env:
    NODE_ENV: development

services:
  api:
    command: flask run --port 5001
    directory: ./backend
    port: 5001
    hostname: api.local
    env:
      FLASK_DEBUG: "1"
    restart_policy: once
    ready_check:
      type: http
      path: /health
      timeout: 30
      interval: 2

  web:
    command: npm run dev
    directory: ./frontend
    port: 3000
    depends_on:
      - api
"""
        config_file = tmp_path / "promenade.yaml"
        config_file.write_text(config_content)

        cfg = load_config(config_file)

        assert cfg.manager.port == 8080
        assert cfg.manager.host == "0.0.0.0"
        assert cfg.defaults.restart_policy == RestartPolicy.ALWAYS

        api = cfg.services["api"]
        assert api.port == 5001
        assert api.hostname == "api.local"
        assert api.restart_policy == RestartPolicy.ONCE  # Overrides default
        assert api.ready_check is not None
        assert api.ready_check.path == "/health"

        web = cfg.services["web"]
        assert web.depends_on == ["api"]
        # Inherits default env
        assert "NODE_ENV" in web.env

    def test_directory_resolution(self, tmp_path):
        """Test that directories are resolved relative to config file."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        config_content = """
services:
  app:
    command: python app.py
    directory: ./subdir
"""
        config_file = tmp_path / "promenade.yaml"
        config_file.write_text(config_content)

        cfg = load_config(config_file)

        assert cfg.services["app"].directory == subdir

    def test_no_services_error(self, tmp_path):
        """Test error when no services defined."""
        config_content = """
manager:
  port: 9000
"""
        config_file = tmp_path / "promenade.yaml"
        config_file.write_text(config_content)

        with pytest.raises(ConfigError, match="No services"):
            load_config(config_file)

    def test_file_not_found(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(ConfigError, match="not found"):
            load_config(Path("/nonexistent/promenade.yaml"))

    def test_search_path(self, tmp_path, monkeypatch):
        """Test config file search path."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        config_content = """
services:
  app:
    command: echo hello
"""
        (tmp_path / "promenade.yaml").write_text(config_content)

        cfg = load_config(None)
        assert "app" in cfg.services
