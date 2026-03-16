"""Tests for the new dashboard router system.

This module tests the decorator-based router system to increase coverage.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

import src.dashboard.routes  # trigger route registration
from src.dashboard.router import (
    RouteContext,
    _GET_ROUTES,
    _POST_ROUTES,
    _PUT_ROUTES,
    _DELETE_ROUTES,
    clear_routes,
    dispatch_get,
    dispatch_post,
    dispatch_put,
    dispatch_delete,
    all_routes,
    get,
    post,
    put,
    delete,
)
from src.dashboard.routes import quote, orders, system, config, cookie, messages, products, dashboard_data


class TestRouteRegistration:
    """Test route registration via decorators."""

    def setup_method(self):
        """Clear routes before each test."""
        clear_routes()

    def teardown_method(self):
        """Restore original routes after each test."""
        clear_routes()
        import src.dashboard.routes  # re-register original routes

    def test_get_decorator_registers_route(self):
        """Test that @get decorator registers a route."""

        @get("/test-get")
        def handler(ctx):
            ctx.send_json({"ok": True})

        assert "/test-get" in _GET_ROUTES
        assert _GET_ROUTES["/test-get"] is handler

    def test_post_decorator_registers_route(self):
        """Test that @post decorator registers a route."""

        @post("/test-post")
        def handler(ctx):
            ctx.send_json({"ok": True})

        assert "/test-post" in _POST_ROUTES

    def test_put_decorator_registers_route(self):
        """Test that @put decorator registers a route."""

        @put("/test-put")
        def handler(ctx):
            ctx.send_json({"ok": True})

        assert "/test-put" in _PUT_ROUTES

    def test_delete_decorator_registers_route(self):
        """Test that @delete decorator registers a route."""

        @delete("/test-delete")
        def handler(ctx):
            ctx.send_json({"ok": True})

        assert "/test-delete" in _DELETE_ROUTES


class TestRouteDispatch:
    """Test route dispatching."""

    def test_dispatch_get_with_registered_route(self):
        """Test dispatching to a registered GET route."""
        mock_handler = Mock()

        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(_GET_ROUTES, "/test-dispatch", mock_handler)

            mock_ctx = MagicMock()
            result = dispatch_get("/test-dispatch", mock_ctx)

            assert result is True
            mock_handler.assert_called_once_with(mock_ctx)

    def test_dispatch_get_with_unknown_route(self):
        """Test dispatching to an unknown route returns False."""
        mock_ctx = MagicMock()
        result = dispatch_get("/unknown-route", mock_ctx)
        assert result is False

    def test_dispatch_post_with_registered_route(self):
        """Test dispatching to a registered POST route."""
        mock_handler = Mock()

        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(_POST_ROUTES, "/test-post", mock_handler)

            mock_ctx = MagicMock()
            result = dispatch_post("/test-post", mock_ctx)

            assert result is True
            mock_handler.assert_called_once_with(mock_ctx)

    def test_dispatch_put_with_registered_route(self):
        """Test dispatching to a registered PUT route."""
        mock_handler = Mock()

        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(_PUT_ROUTES, "/test-put", mock_handler)

            mock_ctx = MagicMock()
            result = dispatch_put("/test-put", mock_ctx)

            assert result is True

    def test_dispatch_delete_with_registered_route(self):
        """Test dispatching to a registered DELETE route."""
        mock_handler = Mock()

        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(_DELETE_ROUTES, "/test-delete", mock_handler)

            mock_ctx = MagicMock()
            result = dispatch_delete("/test-delete", mock_ctx)

            assert result is True


class TestRouteContext:
    """Test RouteContext functionality."""

    def test_query_str_with_existing_key(self):
        """Test query_str returns value for existing key."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"name": ["value"]},
        )

        assert ctx.query_str("name") == "value"

    def test_query_str_with_missing_key_returns_default(self):
        """Test query_str returns default for missing key."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )

        assert ctx.query_str("missing", default="default") == "default"

    def test_query_int_parses_integer(self):
        """Test query_int parses integer value."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"count": ["42"]},
        )

        assert ctx.query_int("count") == 42

    def test_query_int_with_invalid_value_returns_default(self):
        """Test query_int returns default for invalid value."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"count": ["invalid"]},
        )

        assert ctx.query_int("count", default=10) == 10

    def test_query_int_with_clamping(self):
        """Test query_int clamps value to min/max."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"page": ["5"]},
        )

        assert ctx.query_int("page", min_val=1, max_val=3) == 3
        assert ctx.query_int("page", min_val=10) == 10

    def test_query_bool_with_true_values(self):
        """Test query_bool recognizes true values."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"enabled": ["1"], "active": ["true"], "yes": ["yes"]},
        )

        assert ctx.query_bool("enabled") is True
        assert ctx.query_bool("active") is True
        assert ctx.query_bool("yes") is True

    def test_query_bool_with_false_values(self):
        """Test query_bool recognizes false values."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={"disabled": ["0"], "inactive": ["false"], "no": ["no"]},
        )

        assert ctx.query_bool("disabled") is False
        assert ctx.query_bool("inactive") is False
        assert ctx.query_bool("no") is False

    def test_send_json_calls_handler(self):
        """Test send_json calls handler's _send_json."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )

        ctx.send_json({"message": "test"}, status=201)
        mock_handler._send_json.assert_called_once_with({"message": "test"}, status=201)

    def test_send_bytes_calls_handler(self):
        """Test send_bytes calls handler's _send_bytes."""
        mock_handler = MagicMock()
        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )

        ctx.send_bytes(b"data", "application/octet-stream", status=200, download_name="file.bin")
        mock_handler._send_bytes.assert_called_once_with(
            b"data", "application/octet-stream", status=200, download_name="file.bin"
        )

    def test_json_body_reads_from_handler(self):
        """Test json_body reads from handler's _read_json_body."""
        mock_handler = MagicMock()
        mock_handler._read_json_body.return_value = {"key": "value"}

        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )

        result = ctx.json_body()
        assert result == {"key": "value"}

    def test_json_body_caches_result(self):
        """Test json_body caches the result."""
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

    def test_multipart_files_reads_from_handler(self):
        """Test multipart_files reads from handler's _read_multipart_files."""
        mock_handler = MagicMock()
        mock_handler._read_multipart_files.return_value = [("file.txt", b"content")]

        ctx = RouteContext(
            _handler=mock_handler,
            path="/test",
            query={},
        )

        result = ctx.multipart_files()
        assert result == [("file.txt", b"content")]

    def test_service_accessors(self):
        """Test that service accessors work."""
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


class TestQuoteRoutes:
    """Test quote routes."""

    def test_handle_route_stats(self):
        """Test /api/route-stats route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.route_stats.return_value = {"total": 100}

        quote.handle_route_stats(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"total": 100})

    def test_handle_get_template(self):
        """Test /api/get-template route."""
        mock_ctx = MagicMock()
        mock_ctx.query_bool.return_value = True
        mock_ctx.mimic_ops.get_template.return_value = {"template": "default"}

        quote.handle_get_template(mock_ctx)
        mock_ctx.query_bool.assert_called_once_with("default")
        mock_ctx.mimic_ops.get_template.assert_called_once_with(default=True)

    def test_handle_get_markup_rules(self):
        """Test /api/get-markup-rules route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_markup_rules.return_value = {"rules": []}

        quote.handle_get_markup_rules(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"rules": []})


class TestSystemRoutes:
    """Test system routes."""

    def test_handle_api_status(self):
        """Test /api/status route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.service_status.return_value = {"status": "ok"}

        system.handle_api_status(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"status": "ok"})

    def test_handle_api_get_cookie(self):
        """Test /api/get-cookie route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_cookie.return_value = {"cookie": "test"}

        system.handle_api_get_cookie(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"cookie": "test"})


class TestDashboardDataRoutes:
    """Test dashboard data routes."""

    def test_handle_api_summary(self):
        """Test /api/summary route."""
        mock_ctx = MagicMock()
        mock_ctx.repo.get_summary.return_value = {"summary": "data"}

        dashboard_data.handle_api_summary(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"summary": "data"})

    def test_handle_api_trend(self):
        """Test /api/trend route."""
        mock_ctx = MagicMock()
        mock_ctx.query_str.side_effect = lambda key, default="": {"metric": "views", "days": "7"}.get(key, default)
        mock_ctx.repo.get_trend.return_value = {"trend": "data"}

        dashboard_data.handle_api_trend(mock_ctx)
        mock_ctx.repo.get_trend.assert_called_once_with(metric="views", days=7)

    def test_handle_api_recent_operations(self):
        """Test /api/recent-operations route."""
        mock_ctx = MagicMock()
        mock_ctx.query_int.return_value = 10
        mock_ctx.repo.get_recent_operations.return_value = [{"op": 1}]

        dashboard_data.handle_api_recent_operations(mock_ctx)
        mock_ctx.repo.get_recent_operations.assert_called_once_with(limit=10)


class TestAllRoutes:
    """Test all_routes introspection."""

    def test_all_routes_returns_structure(self):
        """Test that all_routes returns expected structure."""
        routes = all_routes()

        assert "GET" in routes
        assert "POST" in routes
        assert "PUT" in routes
        assert "DELETE" in routes

    def test_all_routes_includes_known_routes(self):
        """Test that all_routes includes known routes."""
        routes = all_routes()

        assert "/api/route-stats" in routes["GET"]
        assert "/api/status" in routes["GET"]
        assert "/api/summary" in routes["GET"]


class TestCookieRoutes:
    """Test cookie routes."""

    def test_handle_api_diagnose_cookie(self):
        """Test /api/cookie-diagnose route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"cookie": "test_cookie"}
        mock_ctx.mimic_ops.diagnose_cookie.return_value = {"valid": True}

        cookie.handle_api_diagnose_cookie(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"valid": True})


class TestOrdersRoutes:
    """Test orders routes."""

    def test_handle_virtual_goods_metrics(self):
        """Test /api/virtual-goods/metrics route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_virtual_goods_metrics.return_value = {
            "success": True,
            "metrics": {"total": 10},
        }

        orders.handle_virtual_goods_metrics(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestMessagesRoutes:
    """Test messages routes."""

    def test_handle_api_send_message(self):
        """Test /api/send-message route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"session_id": "123", "message": "hello"}
        mock_ctx.mimic_ops.send_message.return_value = {"sent": True}

        messages.handle_api_send_message(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestProductsRoutes:
    """Test products routes."""

    def test_handle_api_products_search(self):
        """Test /api/products/search route."""
        mock_ctx = MagicMock()
        mock_ctx.query_str.return_value = "keyword"
        mock_ctx.mimic_ops.search_products.return_value = {"products": []}

        products.handle_api_products_search(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestConfigRoutes:
    """Test config routes."""

    def test_handle_api_system_config(self):
        """Test /api/system-config route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_system_config.return_value = {"config": {}}

        config.handle_api_system_config(mock_ctx)
        mock_ctx.send_json.assert_called_once()
