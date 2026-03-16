"""Tests for dashboard routes to increase coverage."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

import src.dashboard.routes
from src.dashboard.routes import quote, system, dashboard_data, messages, config, cookie


class TestQuoteRoutes:
    """Test quote routes."""

    def test_handle_route_stats(self):
        """Test /api/route-stats route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.route_stats.return_value = {"total": 100}
        quote.handle_route_stats(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"total": 100})

    def test_handle_export_routes(self):
        """Test /api/export-routes route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.export_routes_zip.return_value = (b"zip data", "routes.zip")
        quote.handle_export_routes(mock_ctx)
        mock_ctx.send_bytes.assert_called_once_with(
            data=b"zip data", content_type="application/zip", download_name="routes.zip"
        )

    def test_handle_get_template_with_default(self):
        """Test /api/get-template route with default=true."""
        mock_ctx = MagicMock()
        mock_ctx.query_bool.return_value = True
        mock_ctx.mimic_ops.get_template.return_value = {"template": "default"}
        quote.handle_get_template(mock_ctx)
        mock_ctx.query_bool.assert_called_once_with("default")
        mock_ctx.mimic_ops.get_template.assert_called_once_with(default=True)
        mock_ctx.send_json.assert_called_once()

    def test_handle_get_template_without_default(self):
        """Test /api/get-template route without default."""
        mock_ctx = MagicMock()
        mock_ctx.query_bool.return_value = False
        mock_ctx.mimic_ops.get_template.return_value = {"template": "custom"}
        quote.handle_get_template(mock_ctx)
        mock_ctx.mimic_ops.get_template.assert_called_once_with(default=False)

    def test_handle_get_markup_rules(self):
        """Test /api/get-markup-rules route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_markup_rules.return_value = {"rules": []}
        quote.handle_get_markup_rules(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"rules": []})

    def test_handle_import_routes_success(self):
        """Test /api/import-routes route success."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.return_value = [("routes.xlsx", b"data")]
        mock_ctx.mimic_ops.import_route_files.return_value = {"success": True}
        quote.handle_import_routes(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"success": True}, status=200)

    def test_handle_import_routes_parse_error(self):
        """Test /api/import-routes route with parse error."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.side_effect = ValueError("parse error")
        quote.handle_import_routes(mock_ctx)
        call_args = mock_ctx.send_json.call_args
        assert call_args[0][0]["success"] is False
        assert call_args[1]["status"] == 400

    def test_handle_import_routes_empty_files(self):
        """Test /api/import-routes route with empty files."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.return_value = []
        mock_ctx.mimic_ops.import_route_files.return_value = {"success": False}
        quote.handle_import_routes(mock_ctx)
        mock_ctx.mimic_ops.import_route_files.assert_called_once_with([])

    def test_handle_import_markup_success(self):
        """Test /api/import-markup route success."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.return_value = [("markup.xlsx", b"data")]
        mock_ctx.mimic_ops.import_markup_files.return_value = {"success": True}
        quote.handle_import_markup(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"success": True}, status=200)

    def test_handle_import_markup_parse_error(self):
        """Test /api/import-markup route with parse error."""
        mock_ctx = MagicMock()
        mock_ctx.multipart_files.side_effect = Exception("parse error")
        quote.handle_import_markup(mock_ctx)
        call_args = mock_ctx.send_json.call_args
        assert call_args[0][0]["success"] is False
        assert call_args[1]["status"] == 400

    def test_handle_save_template(self):
        """Test /api/save-template route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"weight_template": "W", "volume_template": "V"}
        mock_ctx.mimic_ops.save_template.return_value = {"success": True}
        quote.handle_save_template(mock_ctx)
        mock_ctx.mimic_ops.save_template.assert_called_once_with(weight_template="W", volume_template="V")
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
        mock_ctx.mimic_ops.query_route_cost.return_value = {"cost": 10.0, "success": True}
        quote.handle_query_route_cost(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"cost": 10.0, "success": True}, status=200)

    def test_handle_query_route_cost_error(self):
        """Test /api/query-route-cost route with error."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.query_route_cost.return_value = {"cost": 10.0, "success": False}
        quote.handle_query_route_cost(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"cost": 10.0, "success": False}, status=400)

    def test_handle_save_pricing_config(self):
        """Test /api/save-pricing-config route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"markup_categories": [{"id": 1}], "xianyu_discount": 0.1}
        mock_ctx.mimic_ops.save_pricing_config.return_value = {"success": True}
        quote.handle_save_pricing_config(mock_ctx)
        mock_ctx.mimic_ops.save_pricing_config.assert_called_once_with(
            markup_categories=[{"id": 1}], xianyu_discount=0.1
        )
        mock_ctx.send_json.assert_called_once()


class TestSystemRoutes:
    """Test system routes."""

    def test_handle_healthz(self):
        """Test /healthz route."""
        mock_ctx = MagicMock()
        system.handle_healthz(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    @pytest.mark.skip(reason="Health check has complex real dependencies")
    def test_handle_health_check(self):
        """Test /api/health/check route - skipped due to complex dependencies."""
        pass

    def test_handle_module_status(self):
        """Test /api/module/status route."""
        mock_ctx = MagicMock()
        mock_ctx.query_int.side_effect = lambda key, default=0, min_val=0, max_val=0: {
            ("window", 60, 1, 10080): 10,
            ("limit", 20, 1, 200): 20,
        }.get((key, default, min_val, max_val), default)
        mock_ctx.module_console.status.return_value = {"status": "ok"}
        system.handle_module_status(mock_ctx)
        mock_ctx.module_console.status.assert_called_once_with(window_minutes=10, limit=20)
        mock_ctx.send_json.assert_called_once()

    def test_handle_module_check(self):
        """Test /api/module/check route."""
        mock_ctx = MagicMock()
        mock_ctx.query_bool.return_value = True
        mock_ctx.module_console.check.return_value = {"ok": True}
        system.handle_module_check(mock_ctx)
        mock_ctx.module_console.check.assert_called_once_with(skip_gateway=True)
        mock_ctx.send_json.assert_called_once()

    def test_handle_module_logs(self):
        """Test /api/module/logs route."""
        mock_ctx = MagicMock()
        mock_ctx.query_str.return_value = "presales"
        mock_ctx.query_int.return_value = 50
        mock_ctx.module_console.logs.return_value = {"logs": []}
        system.handle_module_logs(mock_ctx)
        mock_ctx.module_console.logs.assert_called_once_with(target="presales", tail_lines=50)
        mock_ctx.send_json.assert_called_once()

    def test_handle_status(self):
        """Test /api/status route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.service_status.return_value = {"status": "ok"}
        system.handle_status(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"status": "ok"})

    def test_handle_service_status(self):
        """Test /api/service-status route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.service_status.return_value = {"status": "ok"}
        system.handle_service_status(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"status": "ok"})

    def test_handle_module_control(self):
        """Test /api/module/control route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"action": "start", "target": "all"}
        mock_ctx.module_console.control.return_value = {"ok": True}
        system.handle_module_control(mock_ctx)
        mock_ctx.module_console.control.assert_called_once_with(action="start", target="all")
        mock_ctx.send_json.assert_called_once()

    def test_handle_service_control(self):
        """Test /api/service/control route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"action": "start"}
        mock_ctx.mimic_ops.service_control.return_value = {"success": True}
        system.handle_service_control(mock_ctx)
        mock_ctx.mimic_ops.service_control.assert_called_once_with(action="start")
        mock_ctx.send_json.assert_called_once()

    def test_handle_service_recover(self):
        """Test /api/service/recover route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"target": "presales"}
        mock_ctx.mimic_ops.service_recover.return_value = {"success": True}
        system.handle_service_recover(mock_ctx)
        mock_ctx.mimic_ops.service_recover.assert_called_once_with(target="presales")
        mock_ctx.send_json.assert_called_once()

    def test_handle_service_auto_fix(self):
        """Test /api/service/auto-fix route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.service_auto_fix.return_value = {"success": True}
        system.handle_service_auto_fix(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"success": True}, status=200)

    def test_handle_reset_database(self):
        """Test /api/reset-database route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"type": "all"}
        mock_ctx.mimic_ops.reset_database.return_value = {"success": True}
        system.handle_reset_database(mock_ctx)
        mock_ctx.mimic_ops.reset_database.assert_called_once_with(db_type="all")
        mock_ctx.send_json.assert_called_once()


class TestDashboardDataRoutes:
    """Test dashboard data routes."""

    def test_handle_summary(self):
        """Test /api/summary route."""
        mock_ctx = MagicMock()
        mock_ctx._handler._legacy_dashboard_payload.return_value = {"summary": "data"}
        dashboard_data.handle_summary(mock_ctx)
        mock_ctx._handler._legacy_dashboard_payload.assert_called_once()
        mock_ctx.send_json.assert_called_once_with({"summary": "data"})

    def test_handle_trend(self):
        """Test /api/trend route."""
        mock_ctx = MagicMock()
        mock_ctx.query_str.side_effect = lambda key, default="": {"metric": "views", "days": "7"}.get(key, default)
        mock_ctx._handler._legacy_dashboard_payload.return_value = [{"date": "2024-01-01", "value": 100}]
        dashboard_data.handle_trend(mock_ctx)
        mock_ctx._handler._legacy_dashboard_payload.assert_called_once()
        mock_ctx.send_json.assert_called_once()

    def test_handle_recent_operations(self):
        """Test /api/recent-operations route."""
        mock_ctx = MagicMock()
        mock_ctx.query_int.return_value = 10
        mock_ctx._handler._legacy_dashboard_payload.return_value = [{"id": 1}]
        dashboard_data.handle_recent_operations(mock_ctx)
        mock_ctx._handler._legacy_dashboard_payload.assert_called_once()
        mock_ctx.send_json.assert_called_once()

    def test_handle_top_products(self):
        """Test /api/top-products route."""
        mock_ctx = MagicMock()
        mock_ctx.query_int.return_value = 5
        mock_ctx._handler._legacy_dashboard_payload.return_value = [{"id": 1}]
        dashboard_data.handle_top_products(mock_ctx)
        mock_ctx._handler._legacy_dashboard_payload.assert_called_once()
        mock_ctx.send_json.assert_called_once()


class TestMessagesRoutes:
    """Test messages routes."""

    def test_handle_replies(self):
        """Test /api/replies route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_replies.return_value = [{"id": 1}]
        messages.handle_replies(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_test_reply(self):
        """Test /api/test-reply route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"text": "hello", "item_title": "item"}
        mock_ctx.mimic_ops.test_reply.return_value = {"reply": "response"}
        messages.handle_test_reply(mock_ctx)
        mock_ctx.mimic_ops.test_reply.assert_called_once()
        mock_ctx.send_json.assert_called_once()

    def test_handle_notifications_test_missing_params(self):
        """Test /api/notifications/test route with missing params."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"channel": "feishu"}  # missing webhook_url
        messages.handle_notifications_test(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"ok": False, "error": "缺少 channel 或 webhook_url"}, status=400)

    def test_handle_ai_test_missing_params(self):
        """Test /api/ai/test route with missing params."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"api_key": "", "base_url": ""}
        messages.handle_ai_test(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"ok": False, "message": "请填写 API Key 和 API 地址"})


class TestConfigRoutes:
    """Test config routes."""

    @patch("src.dashboard.routes.config._read_system_config")
    def test_handle_config_get(self, mock_read_config):
        """Test /api/config GET route."""
        mock_ctx = MagicMock()
        mock_read_config.return_value = {"ai": {"api_key": "test"}}
        config.handle_config_get(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    @patch("src.dashboard.routes.config._read_system_config")
    def test_handle_config_sections(self, mock_read_config):
        """Test /api/config/sections route."""
        mock_ctx = MagicMock()
        config.handle_config_sections(mock_ctx)
        mock_ctx.send_json.assert_called_once()
        call_args = mock_ctx.send_json.call_args[0][0]
        assert "sections" in call_args

    @patch("src.dashboard.routes.config._read_system_config")
    def test_handle_setup_progress(self, mock_read_config):
        """Test /api/config/setup-progress route."""
        mock_ctx = MagicMock()
        mock_read_config.return_value = {
            "store": {"category": "test"},
            "xianguanjia": {"app_key": "test"},
            "ai": {"api_key": "test"},
            "oss": {"access_key_id": "test"},
            "auto_reply": {"default_reply": "test"},
            "notifications": {"feishu_enabled": True},
        }
        config.handle_setup_progress(mock_ctx)
        mock_ctx.send_json.assert_called_once()
        call_args = mock_ctx.send_json.call_args[0][0]
        assert "overall_percent" in call_args

    @patch("src.dashboard.routes.config._read_system_config")
    def test_handle_intent_rules(self, mock_read_config):
        """Test /api/intent-rules route."""
        mock_ctx = MagicMock()
        mock_read_config.return_value = {"auto_reply": {}}
        config.handle_intent_rules(mock_ctx)
        mock_ctx.send_json.assert_called_once()
        call_args = mock_ctx.send_json.call_args[0][0]
        assert "rules" in call_args

    @patch("src.dashboard.routes.config._read_system_config")
    @patch("src.dashboard.routes.config._write_system_config")
    @patch("src.dashboard.routes.config.get_config")
    def test_handle_config_post(self, mock_get_config, mock_write, mock_read):
        """Test /api/config POST route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"ai": {"api_key": "test123"}}
        mock_read.return_value = {}
        with patch("src.dashboard.routes.config._sync_system_config_to_yaml"):
            config.handle_config_post(mock_ctx)
        mock_ctx.send_json.assert_called_once()


class TestCookieRoutes:
    """Test cookie routes."""

    def test_handle_get_cookie(self):
        """Test /api/get-cookie route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.get_cookie.return_value = {"cookie": "test"}
        cookie.handle_get_cookie(mock_ctx)
        mock_ctx.send_json.assert_called_once_with({"cookie": "test"})

    def test_handle_download_cookie_plugin(self):
        """Test /api/download-cookie-plugin route."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.export_cookie_plugin_bundle.return_value = (b"zip data", "plugin.zip")
        cookie.handle_download_cookie_plugin(mock_ctx)
        mock_ctx.send_bytes.assert_called_once()

    def test_handle_download_cookie_plugin_not_found(self):
        """Test /api/download-cookie-plugin route with file not found."""
        mock_ctx = MagicMock()
        mock_ctx.mimic_ops.export_cookie_plugin_bundle.side_effect = FileNotFoundError("Plugin not found")
        cookie.handle_download_cookie_plugin(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_update_cookie(self):
        """Test /api/update-cookie route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"cookie": "test_cookie"}
        mock_ctx.mimic_ops.update_cookie.return_value = {"success": True}
        cookie.handle_update_cookie(mock_ctx)
        mock_ctx.mimic_ops.update_cookie.assert_called_once_with("test_cookie", auto_recover=True)
        mock_ctx.send_json.assert_called_once()

    def test_handle_parse_cookie(self):
        """Test /api/parse-cookie route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"text": "cookie_data"}
        mock_ctx.mimic_ops.parse_cookie_text.return_value = {"success": True}
        cookie.handle_parse_cookie(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_cookie_diagnose(self):
        """Test /api/cookie-diagnose route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"text": "cookie_data"}
        mock_ctx.mimic_ops.diagnose_cookie.return_value = {"success": True}
        cookie.handle_cookie_diagnose(mock_ctx)
        mock_ctx.send_json.assert_called_once()

    def test_handle_cookie_validate(self):
        """Test /api/cookie/validate route."""
        mock_ctx = MagicMock()
        mock_ctx.json_body.return_value = {"cookie": "test"}
        mock_ctx.mimic_ops.diagnose_cookie.return_value = {"grade": "可用"}
        mock_ctx.mimic_ops._cookie_domain_filter_stats.return_value = {"domains": []}
        cookie.handle_cookie_validate(mock_ctx)
        mock_ctx.send_json.assert_called_once()
