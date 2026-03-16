"""Tests for dashboard router core functionality."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

import src.dashboard.routes  # ensure routes are registered
from src.dashboard.router import (
    RouteContext,
    clear_routes,
    dispatch_get,
    dispatch_post,
    get,
    post,
)


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

    def test_send_json_calls_handler(self):
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )
        ctx.send_json({"message": "test"}, status=201)
        mock_handler._send_json.assert_called_once_with({"message": "test"}, status=201)

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


class TestRouteRegistration:
    """Test route registration."""

    def setup_method(self):
        clear_routes()

    def teardown_method(self):
        clear_routes()
        import src.dashboard.routes

    def test_get_decorator_registers_route(self):
        @get("/test-get")
        def handler(ctx):
            pass

        mock_ctx = MagicMock()
        result = dispatch_get("/test-get", mock_ctx)
        assert result is True

    def test_post_decorator_registers_route(self):
        @post("/test-post")
        def handler(ctx):
            pass

        mock_ctx = MagicMock()
        result = dispatch_post("/test-post", mock_ctx)
        assert result is True

    def test_dispatch_unknown_returns_false(self):
        mock_ctx = MagicMock()
        result = dispatch_get("/unknown", mock_ctx)
        assert result is False
