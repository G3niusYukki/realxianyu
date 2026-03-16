from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

from src.dashboard.router import RouteContext, get, dispatch_get, dispatch_post
from src.dashboard.routes import orders as orders_routes
from src.dashboard_server import DashboardHandler, MimicOps


def test_virtual_goods_metrics_uses_service_query_interface(monkeypatch: pytest.MonkeyPatch, temp_dir) -> None:
    called: dict[str, object] = {}

    class FakeVirtualGoodsService:
        def __init__(self, db_path: str, config: dict | None = None) -> None:
            called["db_path"] = db_path
            called["config"] = dict(config or {})

        def get_dashboard_metrics(self):
            called["metrics_called"] = True
            return {"total_orders": 3, "status_counts": {"delivered": 1}}

        def list_manual_takeover_orders(self):
            called["manual_called"] = True
            return [{"xianyu_order_id": "m-1"}]

    monkeypatch.setattr("src.dashboard_server.VirtualGoodsService", FakeVirtualGoodsService)

    ops = MimicOps(project_root=temp_dir, module_console=SimpleNamespace())
    payload = ops.get_virtual_goods_metrics()

    assert payload["success"] is True
    assert payload["metrics"]["total_orders"] == 3
    assert payload["manual_takeover_count"] == 1
    assert called["metrics_called"] is True
    assert called["manual_called"] is True


def test_virtual_goods_inspect_order_uses_service_query_interface(monkeypatch: pytest.MonkeyPatch, temp_dir) -> None:
    called: dict[str, object] = {}

    class FakeVirtualGoodsService:
        def __init__(self, db_path: str, config: dict | None = None) -> None:
            called["db_path"] = db_path

        def inspect_order(self, *, order_id: str):
            called["order_id"] = order_id
            return {"order": {"xianyu_order_id": order_id, "order_status": "delivered"}, "callbacks": []}

    monkeypatch.setattr("src.dashboard_server.VirtualGoodsService", FakeVirtualGoodsService)

    ops = MimicOps(project_root=temp_dir, module_console=SimpleNamespace())
    payload = ops.inspect_virtual_goods_order("OID-1")

    assert payload["success"] is True
    assert payload["order_id"] == "OID-1"
    assert payload["inspect"]["order"]["order_status"] == "delivered"
    assert called["order_id"] == "OID-1"


def _build_handler(path: str, mimic_ops) -> DashboardHandler:
    h = DashboardHandler.__new__(DashboardHandler)
    h.path = path
    h.command = "GET"
    h.request_version = "HTTP/1.1"
    h.requestline = f"GET {path} HTTP/1.1"
    h.server_version = "Test"
    h.sys_version = ""
    h.protocol_version = "HTTP/1.1"
    h.client_address = ("127.0.0.1", 0)
    h.server = SimpleNamespace(version_string=lambda: "Test", sys_version="")
    h.repo = SimpleNamespace()
    h.module_console = SimpleNamespace()
    h.mimic_ops = mimic_ops
    h.headers = {}
    h.rfile = io.BytesIO(b"")
    h.wfile = io.BytesIO()
    return h


def _json_from_handler(handler: DashboardHandler) -> dict:
    raw = handler.wfile.getvalue().decode("utf-8")
    body = raw.split("\r\n\r\n", 1)[-1]
    return json.loads(body)


def test_dashboard_handler_virtual_goods_endpoints_get_and_post() -> None:
    from unittest.mock import MagicMock, patch
    from urllib.parse import parse_qs, urlparse

    class FakeOps:
        def get_virtual_goods_metrics(self):
            return {"success": True, "metrics": {"total_orders": 2}, "manual_takeover_count": 0}

        def inspect_virtual_goods_order(self, order_id: str):
            return {"success": True, "order_id": order_id, "inspect": {"order": {"xianyu_order_id": order_id}}}

    ops = FakeOps()

    ctx = MagicMock(spec=RouteContext)
    ctx.mimic_ops = ops
    ctx.query_str.return_value = ""
    ctx.json_body.return_value = {"order_id": "o-2"}
    ctx.send_json = MagicMock()

    orders_routes.handle_virtual_goods_metrics(ctx)
    assert ctx.send_json.call_args[0][0]["success"] is True
    assert ctx.send_json.call_args[0][0]["metrics"]["total_orders"] == 2

    ctx.query_str.return_value = "o-1"
    orders_routes.handle_virtual_goods_inspect_order_get(ctx)
    assert ctx.send_json.call_args[0][0]["success"] is True
    assert ctx.send_json.call_args[0][0]["order_id"] == "o-1"
