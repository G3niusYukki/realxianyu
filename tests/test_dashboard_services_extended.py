"""Tests for dashboard service modules to increase coverage."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.dashboard.config_service import (
    read_system_config,
    write_system_config,
    update_config,
    mask_sensitive,
    _ALLOWED_CONFIG_SECTIONS,
    _SENSITIVE_CONFIG_KEYS,
)
from src.dashboard.module_console import ModuleConsole, _extract_json_payload
from src.dashboard.repository import DashboardRepository


class TestConfigServiceExtended:
    """Extended tests for config_service."""

    def test_read_system_config_empty_file(self, tmp_path: Path):
        """Test reading empty config file."""
        cfg_file = tmp_path / "system_config.json"
        cfg_file.write_text("{}", encoding="utf-8")

        with patch("src.dashboard.config_service._SYS_CONFIG_FILE", cfg_file):
            result = read_system_config()
            assert result == {}

    def test_read_system_config_invalid_json(self, tmp_path: Path):
        """Test reading invalid JSON config file."""
        cfg_file = tmp_path / "system_config.json"
        cfg_file.write_text("not valid json", encoding="utf-8")

        with patch("src.dashboard.config_service._SYS_CONFIG_FILE", cfg_file):
            result = read_system_config()
            assert result == {}

    def test_write_system_config_creates_directory(self, tmp_path: Path):
        """Test write_system_config creates directory if needed."""
        cfg_file = tmp_path / "subdir" / "system_config.json"

        with patch("src.dashboard.config_service._SYS_CONFIG_FILE", cfg_file):
            write_system_config({"test": "value"})
            assert cfg_file.exists()
            content = json.loads(cfg_file.read_text(encoding="utf-8"))
            assert content == {"test": "value"}

    def test_update_config_preserves_existing(self, tmp_path: Path):
        """Test update_config preserves existing values."""
        cfg_file = tmp_path / "system_config.json"

        with patch("src.dashboard.config_service._SYS_CONFIG_FILE", cfg_file):
            write_system_config({"ai": {"api_key": "secret", "model": "gpt-4"}})
            result = update_config({"ai": {"model": "gpt-3"}})

            assert result["ai"]["api_key"] == "secret"  # preserved
            assert result["ai"]["model"] == "gpt-3"  # updated

    def test_update_config_ignores_disallowed_sections(self, tmp_path: Path):
        """Test update_config ignores disallowed sections."""
        cfg_file = tmp_path / "system_config.json"

        with patch("src.dashboard.config_service._SYS_CONFIG_FILE", cfg_file):
            write_system_config({})
            result = update_config({"unknown_section": {"key": "value"}})

            assert "unknown_section" not in result

    def test_mask_sensitive_nested(self):
        """Test mask_sensitive with nested sensitive keys."""
        cfg = {
            "xianguanjia": {
                "app_key": "public",
                "app_secret": "very_secret_key_12345",
            },
            "oss": {
                "access_key_id": "AKID123456789",
                "access_key_secret": "super_secret_access_key",
            },
        }

        masked = mask_sensitive(cfg)
        assert masked["xianguanjia"]["app_key"] == "public"
        assert masked["xianguanjia"]["app_secret"].endswith("****")
        assert masked["oss"]["access_key_id"].endswith("****")
        assert masked["oss"]["access_key_secret"].endswith("****")


class TestModuleConsoleExtended:
    """Extended tests for ModuleConsole."""

    def test_module_console_init(self, tmp_path: Path):
        """Test ModuleConsole initialization."""
        console = ModuleConsole(project_root=tmp_path)
        assert console._project_root == tmp_path

    def test_module_console_run_cli_success(self, tmp_path: Path):
        """Test ModuleConsole.run_cli with successful execution."""
        console = ModuleConsole(project_root=tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="output",
                stderr="",
            )
            result = console.run_cli(["status"])

            assert result["returncode"] == 0
            assert result["stdout"] == "output"

    def test_module_console_run_cli_failure(self, tmp_path: Path):
        """Test ModuleConsole.run_cli with failed execution."""
        console = ModuleConsole(project_root=tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("command not found")
            result = console.run_cli(["invalid"])

            assert result["returncode"] == -1
            assert "error" in result

    def test_extract_json_payload_valid(self):
        """Test _extract_json_payload with valid JSON."""
        output = 'prefix{"key": "value"}suffix'
        result = _extract_json_payload(output)
        assert result == {"key": "value"}

    def test_extract_json_payload_invalid(self):
        """Test _extract_json_payload with invalid JSON."""
        output = "no json here"
        result = _extract_json_payload(output)
        assert result == {}

    def test_extract_json_payload_multiple(self):
        """Test _extract_json_payload with multiple JSON objects."""
        output = '{"first": 1} {"second": 2}'
        result = _extract_json_payload(output)
        assert result == {"first": 1}  # returns first valid JSON


class TestDashboardRepositoryExtended:
    """Extended tests for DashboardRepository."""

    def test_repository_init_creates_db(self, tmp_path: Path):
        """Test repository initialization creates database."""
        db_path = tmp_path / "test.db"
        repo = DashboardRepository(str(db_path))

        assert db_path.exists()

    def test_repository_get_summary(self, tmp_path: Path):
        """Test get_summary returns summary data."""
        db_path = tmp_path / "test.db"
        repo = DashboardRepository(str(db_path))

        result = repo.get_summary()
        assert isinstance(result, dict)

    def test_repository_get_trend(self, tmp_path: Path):
        """Test get_trend returns trend data."""
        db_path = tmp_path / "test.db"
        repo = DashboardRepository(str(db_path))

        result = repo.get_trend(metric="orders", days=7)
        assert isinstance(result, list)

    def test_repository_get_recent_operations(self, tmp_path: Path):
        """Test get_recent_operations returns operations."""
        db_path = tmp_path / "test.db"
        repo = DashboardRepository(str(db_path))

        result = repo.get_recent_operations(limit=10)
        assert isinstance(result, list)

    def test_repository_get_top_products(self, tmp_path: Path):
        """Test get_top_products returns products."""
        db_path = tmp_path / "test.db"
        repo = DashboardRepository(str(db_path))

        result = repo.get_top_products(limit=5)
        assert isinstance(result, list)

    def test_repository_execute_raw_query(self, tmp_path: Path):
        """Test executing raw SQL query."""
        db_path = tmp_path / "test.db"
        repo = DashboardRepository(str(db_path))

        result = repo.execute("SELECT 1 as test")
        assert result == [{"test": 1}]

    def test_repository_handles_sql_error(self, tmp_path: Path):
        """Test repository handles SQL errors gracefully."""
        db_path = tmp_path / "test.db"
        repo = DashboardRepository(str(db_path))

        with pytest.raises(sqlite3.Error):
            repo.execute("INVALID SQL")


class TestRoutePrefixMatching:
    """Test prefix matching for routes."""

    def test_prefix_route_registration(self):
        """Test registering and dispatching prefix routes."""
        from src.dashboard.router import get_prefix, dispatch_get, _GET_PREFIX_ROUTES, clear_routes

        clear_routes()

        @get_prefix("/api/prefix/", param_name="sub_path")
        def handle_prefix(ctx):
            ctx.send_json({"sub_path": ctx.path_params.get("sub_path")})

        mock_ctx = MagicMock()
        result = dispatch_get("/api/prefix/test/path", mock_ctx)

        assert result is True
        assert mock_ctx.path_params.get("sub_path") == "test/path"

        clear_routes()
        import src.dashboard.routes  # restore original routes


class TestRouterIntrospection:
    """Test router introspection features."""

    def test_all_routes_structure(self):
        """Test all_routes returns correct structure."""
        from src.dashboard.router import all_routes

        routes = all_routes()

        required_keys = ["GET", "POST", "PUT", "DELETE", "GET_PREFIX", "POST_PREFIX"]
        for key in required_keys:
            assert key in routes
            assert isinstance(routes[key], list)

    def test_all_routes_get_routes(self):
        """Test all_routes returns GET routes."""
        from src.dashboard.router import all_routes

        routes = all_routes()
        assert "/api/status" in routes["GET"]
        assert "/api/summary" in routes["GET"]

    def test_all_routes_post_routes(self):
        """Test all_routes returns POST routes."""
        from src.dashboard.router import all_routes

        routes = all_routes()
        assert "/api/module/control" in routes["POST"]
        assert "/api/service/control" in routes["POST"]

    def test_clear_routes(self):
        """Test clear_routes removes all routes."""
        from src.dashboard.router import all_routes, clear_routes

        clear_routes()
        routes = all_routes()

        assert routes["GET"] == []
        assert routes["POST"] == []
        assert routes["PUT"] == []
        assert routes["DELETE"] == []

        import src.dashboard.routes  # restore
