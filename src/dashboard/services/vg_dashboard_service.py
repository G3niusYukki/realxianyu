"""Virtual goods dashboard panel building and metrics service."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.dashboard.helpers.utils import _error_payload, _now_iso
from src.modules.virtual_goods.service import VirtualGoodsService

logger = logging.getLogger(__name__)


class VirtualGoodsDashboardService:
    """Handles virtual goods dashboard panels, metrics, and order inspection."""

    def __init__(
        self,
        project_root: Path,
        xgj_config_provider: Callable[[], dict[str, Any]],
    ) -> None:
        self.project_root = project_root
        self._xgj_config_provider = xgj_config_provider

    def _virtual_goods_service(self) -> VirtualGoodsService:
        return VirtualGoodsService(
            db_path=str(self.project_root / "data" / "orders.db"),
            config=self._xgj_config_provider(),
        )

    @staticmethod
    def _vg_service_metrics(result: dict[str, Any]) -> dict[str, Any]:
        metrics = result.get("metrics")
        if isinstance(metrics, dict):
            return metrics
        data = result.get("data")
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def _vg_int(metrics: dict[str, Any], key: str) -> int:
        try:
            return int(metrics.get(key) or 0)
        except ValueError:
            return 0

    def _build_virtual_goods_dashboard_panels(
        self,
        dashboard_result: dict[str, Any],
        manual_orders: list[dict[str, Any]],
        funnel_result: dict[str, Any] | None,
        exception_result: dict[str, Any] | None,
        fulfillment_result: dict[str, Any] | None,
        product_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        metrics = self._vg_service_metrics(dashboard_result)
        errors = dashboard_result.get("errors") if isinstance(dashboard_result.get("errors"), list) else []

        failed_callbacks = self._vg_int(metrics, "failed_callbacks")
        timeout_backlog = self._vg_int(metrics, "timeout_backlog")
        unknown_event_kind = self._vg_int(metrics, "unknown_event_kind")
        timeout_seconds = self._vg_int(metrics, "timeout_seconds")

        funnel_data = (
            funnel_result.get("data")
            if isinstance(funnel_result, dict) and isinstance(funnel_result.get("data"), dict)
            else {}
        )
        funnel_stage_totals = (
            funnel_data.get("stage_totals") if isinstance(funnel_data.get("stage_totals"), dict) else {}
        )

        exception_data = (
            exception_result.get("data")
            if isinstance(exception_result, dict) and isinstance(exception_result.get("data"), dict)
            else {}
        )
        exception_items = exception_data.get("items") if isinstance(exception_data.get("items"), list) else []

        fulfillment_data = (
            fulfillment_result.get("data")
            if isinstance(fulfillment_result, dict) and isinstance(fulfillment_result.get("data"), dict)
            else {}
        )
        fulfillment_summary = (
            fulfillment_data.get("summary") if isinstance(fulfillment_data.get("summary"), dict) else {}
        )

        product_data = (
            product_result.get("data")
            if isinstance(product_result, dict) and isinstance(product_result.get("data"), dict)
            else {}
        )
        product_summary_raw = product_data.get("summary") if isinstance(product_data.get("summary"), dict) else {}

        stable_product_fields = [
            "exposure_count",
            "paid_order_count",
            "paid_amount_cents",
            "refund_order_count",
            "exception_count",
            "manual_takeover_count",
            "conversion_rate_pct",
        ]
        product_summary: dict[str, Any] = {}
        product_field_state: dict[str, str] = {}
        for key in stable_product_fields:
            if key in product_summary_raw:
                product_summary[key] = product_summary_raw.get(key)
                product_field_state[key] = "available"
            else:
                product_summary[key] = None
                product_field_state[key] = "placeholder"

        exception_pool: list[dict[str, Any]] = [x for x in exception_items if isinstance(x, dict)]
        if unknown_event_kind > 0 and not any(
            str(x.get("type") or "").upper() == "UNKNOWN_EVENT_KIND" for x in exception_pool
        ):
            exception_pool.insert(
                0,
                {
                    "priority": "P0",
                    "type": "UNKNOWN_EVENT_KIND",
                    "count": unknown_event_kind,
                    "summary": "检测到未知事件类型回调，需人工排查映射。",
                },
            )
        if failed_callbacks > 0 and not any(
            str(x.get("type") or "").upper() == "FAILED_CALLBACK" for x in exception_pool
        ):
            exception_pool.append(
                {
                    "priority": "P1",
                    "type": "FAILED_CALLBACK",
                    "count": failed_callbacks,
                    "summary": "回调处理失败，建议优先重放失败回调。",
                }
            )
        if timeout_backlog > 0 and not any(
            str(x.get("type") or "").upper() == "TIMEOUT_BACKLOG" for x in exception_pool
        ):
            exception_pool.append(
                {
                    "priority": "P1",
                    "type": "TIMEOUT_BACKLOG",
                    "count": timeout_backlog,
                    "summary": f"存在超时未处理回调（超时阈值 {timeout_seconds}s）。",
                }
            )
        for err in errors:
            if not isinstance(err, dict):
                continue
            if str(err.get("code") or "").upper() == "UNKNOWN_EVENT_KIND" and unknown_event_kind <= 0:
                exception_pool.append(
                    {
                        "priority": "P0",
                        "type": "UNKNOWN_EVENT_KIND",
                        "count": int(err.get("count") or 1),
                        "summary": str(err.get("message") or "unknown event_kind detected"),
                    }
                )

        stage_totals_int = {str(k): self._vg_int(funnel_stage_totals, str(k)) for k in funnel_stage_totals.keys()}
        funnel_total = sum(stage_totals_int.values())

        return {
            "operations_funnel_overview": {
                "stage_totals": stage_totals_int,
                "total_metric_count": int(
                    ((funnel_result.get("metrics") or {}).get("total_metric_count") or funnel_total)
                    if isinstance(funnel_result, dict)
                    else funnel_total
                ),
                "source": str((funnel_result.get("metrics") or {}).get("source") or "ops_funnel_stage_daily")
                if isinstance(funnel_result, dict)
                else "ops_funnel_stage_daily",
            },
            "exception_priority_pool": {
                "total_items": len(exception_pool),
                "items": exception_pool,
            },
            "fulfillment_efficiency": {
                "fulfilled_orders": self._vg_int(fulfillment_summary, "fulfilled_orders"),
                "failed_orders": self._vg_int(fulfillment_summary, "failed_orders"),
                "fulfillment_rate_pct": float(
                    fulfillment_summary["fulfillment_rate_pct"]
                    if "fulfillment_rate_pct" in fulfillment_summary
                    and fulfillment_summary["fulfillment_rate_pct"] is not None
                    else 0.0
                ),
                "failure_rate_pct": float(
                    fulfillment_summary["failure_rate_pct"]
                    if "failure_rate_pct" in fulfillment_summary and fulfillment_summary["failure_rate_pct"] is not None
                    else 0.0
                ),
                "avg_fulfillment_seconds": float(
                    fulfillment_summary["avg_fulfillment_seconds"]
                    if "avg_fulfillment_seconds" in fulfillment_summary
                    and fulfillment_summary["avg_fulfillment_seconds"] is not None
                    else 0.0
                ),
                "p95_fulfillment_seconds": float(
                    fulfillment_summary["p95_fulfillment_seconds"]
                    if "p95_fulfillment_seconds" in fulfillment_summary
                    and fulfillment_summary["p95_fulfillment_seconds"] is not None
                    else 0.0
                ),
            },
            "product_operations": {
                "summary": product_summary,
                "field_state": product_field_state,
                "manual_takeover_count": int(product_summary.get("manual_takeover_count") or len(manual_orders)),
                "manual_takeover_orders": [
                    {
                        "xianyu_order_id": str(item.get("xianyu_order_id") or ""),
                        "fulfillment_status": str(item.get("fulfillment_status") or ""),
                        "reason": str(item.get("reason") or ""),
                    }
                    for item in manual_orders
                ],
            },
            "drill_down": {
                "inspect_endpoint": "/api/virtual-goods/inspect-order",
                "query_key": "order_id",
                "message": "输入订单号查看成品化明细视图。",
                "actions": [
                    {"name": "claim_callback", "enabled": False, "reason": "Dashboard 为只读视图"},
                    {"name": "replay_callback", "enabled": False, "reason": "Dashboard 为只读视图"},
                    {"name": "manual_takeover", "enabled": False, "reason": "Dashboard 为只读视图"},
                ],
            },
        }

    def get_virtual_goods_metrics(self) -> dict[str, Any]:
        service = self._virtual_goods_service()
        query = getattr(service, "get_dashboard_metrics", None)
        if not callable(query):
            return _error_payload(
                "virtual_goods service query `get_dashboard_metrics` is unavailable",
                code="VG_QUERY_NOT_AVAILABLE",
            )

        result = query()
        if not isinstance(result, dict):
            return _error_payload("virtual_goods metrics payload invalid", code="VG_METRICS_INVALID")
        legacy_metrics_payload = not any(
            key in result for key in ("ok", "action", "code", "message", "data", "metrics", "errors", "ts")
        )

        manual_query = getattr(service, "list_manual_takeover_orders", None)
        manual_orders: list[dict[str, Any]] = []
        if callable(manual_query):
            raw_manual = manual_query()
            if isinstance(raw_manual, dict):
                raw_manual = raw_manual.get("data", {}).get("items", [])
            if isinstance(raw_manual, list):
                manual_orders = [x for x in raw_manual if isinstance(x, dict)]

        funnel_result = None
        if callable(getattr(service, "get_funnel_metrics", None)):
            funnel_result = service.get_funnel_metrics(limit=500)

        exception_result = None
        if callable(getattr(service, "list_priority_exceptions", None)):
            exception_result = service.list_priority_exceptions(limit=100, status="open")

        fulfillment_result = None
        if callable(getattr(service, "get_fulfillment_efficiency_metrics", None)):
            fulfillment_result = service.get_fulfillment_efficiency_metrics(limit=500)

        product_result = None
        if callable(getattr(service, "get_product_operation_metrics", None)):
            product_result = service.get_product_operation_metrics(limit=500)

        payload = {
            "success": bool(result.get("ok", True)),
            "module": "virtual_goods",
            "service_response": {
                "ok": bool(result.get("ok", True)),
                "action": str(result.get("action") or "get_dashboard_metrics"),
                "code": str(result.get("code") or "OK"),
                "message": str(result.get("message") or ""),
                "ts": str(result.get("ts") or ""),
            },
            "dashboard_panels": self._build_virtual_goods_dashboard_panels(
                result,
                manual_orders,
                funnel_result,
                exception_result,
                fulfillment_result,
                product_result,
            ),
            "manual_takeover_count": len(manual_orders),
            "generated_at": _now_iso(),
        }
        if legacy_metrics_payload:
            payload["metrics"] = dict(result)
        return payload

    def get_dashboard_readonly_aggregate(self) -> dict[str, Any]:
        """Dashboard 只读聚合接口（运营视图）。"""
        payload = self.get_virtual_goods_metrics()
        if not payload.get("success"):
            return payload

        panels = payload.get("dashboard_panels") if isinstance(payload.get("dashboard_panels"), dict) else {}
        return {
            "success": True,
            "module": "virtual_goods",
            "readonly": True,
            "service_response": payload.get("service_response", {}),
            "sections": {
                "operations_funnel_overview": panels.get("operations_funnel_overview", {}),
                "exception_priority_pool": panels.get("exception_priority_pool", {}),
                "fulfillment_efficiency": panels.get("fulfillment_efficiency", {}),
                "product_operations": panels.get("product_operations", {}),
                "drill_down": panels.get("drill_down", {}),
            },
            "generated_at": payload.get("generated_at") or _now_iso(),
        }

    def inspect_virtual_goods_order(self, order_id: str) -> dict[str, Any]:
        oid = str(order_id or "").strip()
        if not oid:
            return _error_payload("Missing order_id", code="MISSING_ORDER_ID")

        service = self._virtual_goods_service()
        inspect = getattr(service, "inspect_order", None)
        if not callable(inspect):
            return _error_payload(
                "virtual_goods service query `inspect_order` is unavailable",
                code="VG_QUERY_NOT_AVAILABLE",
            )

        try:
            result = inspect(oid)
        except TypeError:
            result = inspect(order_id=oid)
        if not isinstance(result, dict):
            return _error_payload("virtual_goods inspect payload invalid", code="VG_INSPECT_INVALID")

        data = result.get("data") if isinstance(result.get("data"), dict) else result
        order = data.get("order") if isinstance(data.get("order"), dict) else {}
        callbacks_raw = data.get("callbacks") if isinstance(data.get("callbacks"), list) else []
        exception_pool_raw = (
            data.get("exception_priority_pool") if isinstance(data.get("exception_priority_pool"), dict) else {}
        )
        exception_items_raw = (
            exception_pool_raw.get("items") if isinstance(exception_pool_raw.get("items"), list) else []
        )

        callbacks_view = [
            {
                "callback_id": int(cb.get("id") or 0),
                "external_event_id": str(cb.get("external_event_id") or ""),
                "dedupe_key": str(cb.get("dedupe_key") or ""),
                "event_kind": str(cb.get("event_kind") or ""),
                "verify_passed": bool(cb.get("verify_passed")),
                "processed": bool(cb.get("processed")),
                "attempt_count": int(cb.get("attempt_count") or 0),
                "last_process_error": str(cb.get("last_process_error") or ""),
                "created_at": str(cb.get("created_at") or ""),
                "processed_at": str(cb.get("processed_at") or ""),
            }
            for cb in callbacks_raw
            if isinstance(cb, dict)
        ]
        unknown_count = sum(
            1
            for cb in callbacks_view
            if str(cb.get("event_kind") or "").strip().lower() in {"unknown", "unknown_event_kind"}
        )

        callback_chain = [
            {
                "step": idx + 1,
                "event_kind": item.get("event_kind"),
                "verify_passed": item.get("verify_passed"),
                "processed": item.get("processed"),
                "created_at": item.get("created_at"),
                "processed_at": item.get("processed_at"),
            }
            for idx, item in enumerate(callbacks_view)
        ]
        claim_replay_trace = [
            {
                "callback_id": item.get("callback_id"),
                "external_event_id": item.get("external_event_id"),
                "dedupe_key": item.get("dedupe_key"),
                "attempt_count": item.get("attempt_count"),
                "processed": item.get("processed"),
            }
            for item in callbacks_view
        ]
        recent_errors = [
            {
                "callback_id": item.get("callback_id"),
                "error": item.get("last_process_error"),
                "event_kind": item.get("event_kind"),
                "at": item.get("processed_at") or item.get("created_at"),
            }
            for item in callbacks_view
            if str(item.get("last_process_error") or "").strip()
        ][:5]

        exception_items = [x for x in exception_items_raw if isinstance(x, dict)]
        if unknown_count > 0 and not any(
            str(x.get("type") or "").upper() == "UNKNOWN_EVENT_KIND" for x in exception_items
        ):
            exception_items.insert(
                0,
                {
                    "priority": "P0",
                    "type": "UNKNOWN_EVENT_KIND",
                    "count": unknown_count,
                    "summary": "该订单存在 unknown event_kind 回调，已纳入异常池。",
                },
            )

        inspect_payload = {
            "order": order,
            "callbacks": callbacks_raw,
        }
        return {
            "success": bool(result.get("ok", True)),
            "module": "virtual_goods",
            "order_id": oid,
            "inspect": inspect_payload,
            "service_response": {
                "ok": bool(result.get("ok", True)),
                "action": str(result.get("action") or "inspect_order"),
                "code": str(result.get("code") or "OK"),
                "message": str(result.get("message") or ""),
                "ts": str(result.get("ts") or ""),
            },
            "drill_down_view": {
                "order": {
                    "xianyu_order_id": str(order.get("xianyu_order_id") or oid),
                    "order_status": str(order.get("order_status") or ""),
                    "fulfillment_status": str(order.get("fulfillment_status") or ""),
                    "updated_at": str(order.get("updated_at") or ""),
                },
                "current_status": {
                    "xianyu_order_id": str(order.get("xianyu_order_id") or oid),
                    "order_status": str(order.get("order_status") or ""),
                    "fulfillment_status": str(order.get("fulfillment_status") or ""),
                    "updated_at": str(order.get("updated_at") or ""),
                },
                "manual_takeover": {
                    "enabled": bool(order.get("manual_takeover")),
                    "reason": str(order.get("last_error") or ""),
                },
                "callback_chain": callback_chain,
                "claim_replay_trace": claim_replay_trace,
                "recent_errors": recent_errors,
                "exception_priority_pool": {
                    "total_items": len(exception_items),
                    "items": exception_items,
                },
                "actions": [
                    {"name": "claim_callback", "enabled": False, "reason": "只读视图，不支持执行动作"},
                    {"name": "replay_callback", "enabled": False, "reason": "只读视图，不支持执行动作"},
                    {"name": "manual_takeover", "enabled": False, "reason": "只读视图，不支持执行动作"},
                ],
            },
        }
