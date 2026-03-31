"""ModuleConsole CLI 控制测试。"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.dashboard.module_console import ModuleConsole, _extract_json_payload, MODULE_TARGETS


class TestExtractJsonPayload:
    def test_valid_json_object(self):
        result = _extract_json_payload('{"ok": true}')
        assert result == {"ok": True}

    def test_valid_json_array(self):
        result = _extract_json_payload("[1, 2, 3]")
        assert result == [1, 2, 3]

    def test_empty_string(self):
        assert _extract_json_payload("") is None

    def test_whitespace_only(self):
        assert _extract_json_payload("   \n") is None

    def test_invalid_json_tries_braces(self):
        result = _extract_json_payload('not json but {"key": 123} here')
        assert result == {"key": 123}

    def test_invalid_json_tries_brackets(self):
        result = _extract_json_payload("not json but [1, 2] end")
        assert result == [1, 2]

    def test_invalid_json_no_valid_pair(self):
        result = _extract_json_payload("no braces here")
        assert result is None


class TestModuleConsoleInit:
    def test_resolves_path(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        assert mc.project_root == tmp_path.resolve()


class TestModuleConsoleRunModuleCli:
    def test_returns_error_on_exception(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(sys, "executable", "/nonexistent/python"):
            result = mc._run_module_cli("status", "presales")
            assert "error" in result or result.get("error")

    def test_parses_json_stdout(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='{"status": "ok"}',
                stderr="",
            )
            result = mc._run_module_cli("status", "presales")
            assert result["status"] == "ok"

    def test_non_zero_returncode_error(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="command failed",
            )
            result = mc._run_module_cli("start", "presales")
            assert "error" in result

    def test_list_payload_returned(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"item": 1}, {"item": 2}]',
                stderr="",
            )
            result = mc._run_module_cli("status", "presales")
            assert result["items"] == [{"item": 1}, {"item": 2}]

    def test_fallback_to_stdout(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="plain text output",
                stderr="",
            )
            result = mc._run_module_cli("status", "presales")
            assert "ok" in result


class TestModuleConsoleStatus:
    def test_uses_cache(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        mc._status_cache = {"cached": True}
        mc._status_cache_ts = float("inf")
        mc._status_cache_key = "60:20"
        result = mc.status(60, 20)
        assert result["cached"] is True

    def test_invalidates_old_cache(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        mc._status_cache = {"old": True}
        mc._status_cache_ts = 0
        mc._status_cache_key = "60:20"
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {"new": True}
            result = mc.status(60, 20)
            assert result["new"] is True
            assert mc._status_cache["new"] is True


class TestModuleConsoleLogs:
    def test_safe_target_all(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {}
            mc.logs("all", 50)
            mock_cli.assert_called_once()
            call_args = mock_cli.call_args[1]["extra_args"]
            assert "--tail-lines" in call_args

    def test_safe_target_module(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {}
            mc.logs("presales", 50)
            mock_cli.assert_called_once()

    def test_unknown_target_defaults_to_all(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {}
            mc.logs("unknown_module", 50)
            mock_cli.assert_called_once()
            call_args = mock_cli.call_args
            assert call_args[1]["target"] == "all"


class TestModuleConsoleCheck:
    def test_calls_check_action(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {"ok": True}
            result = mc.check()
            assert result["ok"] is True


class TestModuleConsoleControl:
    def test_unsupported_action(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        result = mc.control("dance", "presales")
        assert "error" in result
        assert "Unsupported" in result["error"]

    def test_unsupported_target(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        result = mc.control("start", "invalid_target")
        assert "error" in result
        assert "Unsupported" in result["error"]

    def test_start_action(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {"ok": True}
            mc.control("start", "presales")
            call_args = mock_cli.call_args
            assert call_args[1]["action"] == "start"

    def test_stop_action(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {"ok": True}
            mc.control("stop", "presales")
            call_args = mock_cli.call_args
            assert call_args[1]["action"] == "stop"

    def test_restart_action(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {"ok": True}
            mc.control("restart", "presales")
            call_args = mock_cli.call_args
            assert call_args[1]["action"] == "restart"

    def test_recover_action(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {"ok": True}
            mc.control("recover", "presales")
            call_args = mock_cli.call_args
            assert call_args[1]["action"] == "recover"

    def test_control_all_target(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {"ok": True}
            mc.control("start", "all")
            call_args = mock_cli.call_args
            assert call_args[1]["target"] == "all"

    def test_invalidates_cache_on_control(self, tmp_path):
        mc = ModuleConsole(tmp_path)
        mc._status_cache = {"cached": True}
        with patch.object(mc, "_run_module_cli") as mock_cli:
            mock_cli.return_value = {"ok": True}
            mc.control("start", "presales")
            assert mc._status_cache is None
