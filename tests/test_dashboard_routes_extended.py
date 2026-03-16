"""Additional tests for dashboard routes to increase coverage."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, Mock

import pytest

import src.dashboard.routes
from src.dashboard.routes import quote, orders, system, config, cookie, messages, products, dashboard_data


class TestQuoteRoutesExtended:
    """Extended tests for quote routes."""

    def test_handle_export_routes(self):
        """Test /api/export-routes route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.export_routes_zip.return_value = (b"zip content", "routes.zip")

        quote.handle_export_routes(mock_ctx)
        mock_ctx.send_bytes.assert_called_once_with(
            data=b"zip content", content_type="application/zip", download_name="routes.zip"
        )

    def test_handle_import_routes_success(self):
        """Test /api/import-routes with valid files."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.return_value = [("routes.xlsx", b"data")]
        mock_ctx.mimic_ops.import_route_files.return_value = {"success": True}

        quote.handle_import_routes(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"success": True})

    def test_handle_import_routes_parse_error(self):
        """Test /api/import-routes with parse error."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.side_effect = ValueError("parse failed")

        quote.handle_import_routes(mock_ctx)
        mock_ctx.send_json.assert_called_once()
        call_args = mock_ctx.send_json.call_args
        assert call_args[0][0]["success"] is False
        assert call_args[1]["status"] == 400

    def test_handle_import_routes_empty_files(self):
        """Test /api/import-routes with no files."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.return_value = []
        mock_ctx.mimic_ops.import_route_files.return_value = {"success": False}

        quote.handle_import_routes(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_import_markup_success(self):
        """Test /api/import-markup with valid files."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.return_value = [("markup.xlsx", b"data")]
        mock_ctx.mimic_ops.import_markup_files.return_value = {"success": True}

        quote.handle_import_markup(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"success": True}, status=200)

    def test_handle_import_markup_parse_error(self):
        """Test /api/import-markup with parse error."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.side_effect = Exception("parse error")

        quote.handle_import_markup(mock_ctx)
        mock_ctx.send_json.assert_called_once()
        call_args = mock_ctx.send_json.call_args
        assert call_args[1]["status"] == 400

    def test_handle_save_template(self):
        """Test /api/save-template route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"weight_template": "W", "volume_template": "V"}
        mock_ctx.mimic_ops.save_template.return_value = {"success": True}

        quote.handle_save_template(mock_ctx)
        mock_ctx.mimic_ops.save_template.assert_called_once_with("W", "V")
        mock_ctx.send_json.assert_called_once()

    def test_handle_save_markup_rules(self):
        """Test /api/save-markup-rules route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"markup_rules": [{"id": 1}]}
        mock_ctx.mimic_ops.save_markup_rules.return_value = {"success": True}

        quote.handle_save_markup_rules(mock_ctx)
        mock_ctx.mimic_ops.save_markup_rules.assert_called_once_with([{"id": 1}])
        mock_ctx.send_json.assert_called_once()

    def test_handle_get_pricing_config(self):
        """Test /api/get-pricing-config route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_pricing_config.return_value = {"config": {}}

        quote.handle_get_pricing_config(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"config": {}})

    def test_handle_get_cost_summary(self):
        """Test /api/get-cost-summary route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_cost_summary.return_value = {"summary": {}}

        quote.handle_get_cost_summary(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"summary": {}})

    def test_handle_query_route_cost(self):
        """Test /api/query-route-cost route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.query_route_cost.return_value = {"cost": 10.0}

        quote.handle_query_route_cost(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"cost": 10.0})


class TestOrdersRoutesExtended:
    """Extended tests for orders routes."""

    def test_handle_virtual_goods_inspect_order_get(self):
        """Test GET /api/virtual-goods/inspect-order."""
        mock_ctx = MagicMock()
        mock_ctx.query_str.return_value = "order123"
        mock_ctx.mimic_ops.inspect_virtual_goods_order.return_value = {"success": True}

        orders.handle_virtual_goods_inspect_order_get(mock_ctx)
        mock_ctx.mimic_ops.inspect_virtual_goods_order.assert_called_once_with("order123")
        mock_ctx.send_json.assert_called_once()

    def test_handle_orders_remind_missing_order_id(self):
        """Test /api/orders/remind with missing order_id."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {}

        orders.handle_orders_remind(mock_ctx)
        mock_ctx.send_json.assert_called_once()
        call_args = mock_ctx.send_json.call_args
        assert call_args[1]["status"] == 400

    def test_handle_xianyu_orders_sync(self):
        """Test /api/xianyu-orders/sync route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"limit": 10}
        mock_ctx.mimic_ops.sync_xianyu_orders.return_value = {"success": True}

        orders.handle_xianyu_orders_sync(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestSystemRoutesExtended:
    """Extended tests for system routes."""

    def test_handle_api_module_status(self):
        """Test /api/module/status route."""
        mock_ctx = MagicMock()
        mock_ctx.query_int.return_value = 10
        mock_ctx.module_console.status.return_value = {"status": "ok"}

        system.handle_api_module_status(mock_ctx)
        mock_ctx.module_console.status.assert_called_once_with(window=10)
        mock_ctx.send_json.assert_called_once()

    def test_handle_api_module_check(self):
        """Test /api/module/check route."""
        mock_ctx = MagicMock()
        mock_ctx.query_bool.return_value = True
        mock_ctx.module_console.check.return_value = {"ok": True}

        system.handle_api_module_check(mock_ctx)
        mock_ctx.module_console.check.assert_called_once_with(skip_gateway=True)
        mock_ctx.send_json.assert_called_once()

    def test_handle_api_module_logs(self):
        """Test /api/module/logs route."""
        mock_ctx = MagicMock()
        mock_ctx.query_str.return_value = "presales"
        mock_ctx.query_int.return_value = 50
        mock_ctx.module_console.logs.return_value = {"logs": []}

        system.handle_api_module_logs(mock_ctx)
        mock_ctx.module_console.logs.assert_called_once_with(target="presales", tail=50)
        mock_ctx.send_json.assert_called_once()

    def test_handle_api_service_control(self):
        """Test /api/service/control route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"action": "start"}
        mock_ctx.mimic_ops.service_control.return_value = {"success": True}

        system.handle_api_service_control(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_api_service_recover(self):
        """Test /api/service/recover route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"target": "presales"}
        mock_ctx.mimic_ops.service_recover.return_value = {"success": True}

        system.handle_api_service_recover(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_api_service_auto_fix(self):
        """Test /api/service/auto-fix route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.service_auto_fix.return_value = {"success": True}

        system.handle_api_service_auto_fix(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_api_reset_database(self):
        """Test /api/reset-database route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"type": "all"}
        mock_ctx.mimic_ops.reset_database.return_value = {"success": True}

        system.handle_api_reset_database(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestDashboardDataRoutesExtended:
    """Extended tests for dashboard data routes."""

    def test_handle_api_top_products(self):
        """Test /api/top-products route."""
        mock_ctx = MagicMock()
        mock_ctx.query_int.return_value = 10
        mock_ctx.repo.get_top_products.return_value = [{"id": 1}]

        dashboard_data.handle_api_top_products(mock_ctx)
        mock_ctx.repo.get_top_products.assert_called_once_with(limit=10)
        mock_ctx.send_json.assert_called_once()


class TestCookieRoutesExtended:
    """Extended tests for cookie routes."""

    def test_handle_api_update_cookie(self):
        """Test /api/update-cookie route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"cookie": "test_cookie"}
        mock_ctx.mimic_ops.update_cookie.return_value = {"success": True}

        cookie.handle_api_update_cookie(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_api_parse_cookie(self):
        """Test /api/parse-cookie route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"text": "cookie_text"}
        mock_ctx.mimic_ops.parse_cookie_text.return_value = {"success": True}

        cookie.handle_api_parse_cookie(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestConfigRoutesExtended:
    """Extended tests for config routes."""

    def test_handle_api_system_config_post(self):
        """Test POST /api/system-config route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"section": {"key": "value"}}
        mock_ctx.mimic_ops.update_system_config.return_value = {"success": True}

        config.handle_api_system_config_post(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestMessagesRoutesExtended:
    """Extended tests for messages routes."""

    def test_handle_api_replies(self):
        """Test /api/replies route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_replies.return_value = [{"id": 1}]

        messages.handle_replies(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_test_reply(self):
        """Test /api/test-reply route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"text": "test", "item_title": "item"}
        mock_ctx.mimic_ops.test_reply.return_value = {"reply": "response"}

        messages.handle_test_reply(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_notifications_test(self):
        """Test /api/notifications/test route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"channel": "email"}
        mock_ctx.mimic_ops.test_notification.return_value = {"success": True}

        messages.handle_notifications_test(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestProductsRoutesExtended:
    """Extended tests for products routes."""

    def test_handle_api_products_list(self):
        """Test /api/products/list route."""
        mock_ctx = MagicMock()
        mock_ctx.query_int.return_value = 10
        mock_ctx.mimic_ops.list_products.return_value = [{"id": 1}]

        products.handle_api_products_list(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_api_products_detail(self):
        """Test /api/products/detail route."""
        mock_ctx = MagicMock()
        mock_ctx.query_str.return_value = "product123"
        mock_ctx.mimic_ops.get_product_detail.return_value = {"id": "product123"}

        products.handle_api_products_detail(mock_ctx)
        mock_ctx.mimic_ops.get_product_detail.assert_called_once_with("product123")
        mock_ctx.send_json.assert_called_once()
