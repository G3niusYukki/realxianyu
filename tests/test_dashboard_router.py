"""Tests for dashboard router core functionality."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import src.dashboard.routes
from src.dashboard.router import RouteContext


class TestRouteContext:
    """Test RouteContext functionality."""

    def test_query_str_with_existing_key(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"name": ["value"]},
        )
        assert ctx.query_str("name") == "value"

    def test_query_str_with_missing_key_returns_default(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )
        assert ctx.query_str("missing", default="default") == "default"

    def test_query_int_parses_integer(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"count": ["42"]},
        )
        assert ctx.query_int("count") == 42

    def test_query_int_with_invalid_value_returns_default(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"count": ["invalid"]},
        )
        assert ctx.query_int("count", default=10) == 10

    def test_query_int_with_min_max_clamping(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"page": ["100"]},
        )
        assert ctx.query_int("page", min_val=1, max_val=10) == 10

    def test_query_bool_with_true_values(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"enabled": ["1"], "active": ["true"]},
        )
        assert ctx.query_bool("enabled") is True
        assert ctx.query_bool("active") is True

    def test_query_bool_with_false_values(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"disabled": ["0"], "inactive": ["false"]},
        )
        assert ctx.query_bool("disabled") is False
        assert ctx.query_bool("inactive") is False

    def test_send_json_calls_handler(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )
        ctx.send_json({"message": "test"}, status=201)
        mock_handler._send_json.assert_called_once_with({"message": "test"}, status=201)

    def test_send_bytes_calls_handler(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )
        ctx.send_bytes(b"data", "application/octet-stream", status=200)
        mock_handler._send_bytes.assert_called_once_with(
            b"data", "application/octet-stream", status=200, download_name=None
        )

    def test_json_body_caches_result(self):
        mock_handler = MagicMock()
        mock_handler._read_json_body.return_value = {"key": "value"}
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )
        result1 = ctx.json_body()
        result2 = ctx.json_body()
        assert result1 is result2
        mock_handler._read_json_body.assert_called_once()

    def test_service_accessors(self):
        mock_handler = MagicMock()
        mock_handler.repo = "repo"
        mock_handler.module_console = "console"
        mock_handler.mimic_ops = "ops"
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )
        assert ctx.repo == "repo"
        assert ctx.module_console == "console"
        assert ctx.mimic_ops == "ops"
