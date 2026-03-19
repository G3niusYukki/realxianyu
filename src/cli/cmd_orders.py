"""
Order fulfillment and virtual-goods commands.
"""

from __future__ import annotations

import argparse
from typing import Any


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
#
# _json_out is looked up dynamically inside each function (via a local import)
# so that tests patching src.cli._json_out always intercept the correct binding.
# ---------------------------------------------------------------------------


async def cmd_orders(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401

    from src.modules.orders.service import OrderFulfillmentService

    service_config: dict[str, Any] = {}
    xgj_app_key = getattr(args, "xgj_app_key", None)
    xgj_app_secret = getattr(args, "xgj_app_secret", None)
    if xgj_app_key and xgj_app_secret:
        service_config["xianguanjia"] = {
            "enabled": True,
            "app_key": xgj_app_key,
            "app_secret": xgj_app_secret,
            "merchant_id": getattr(args, "xgj_merchant_id", None),
            "base_url": getattr(args, "xgj_base_url", None) or "https://open.goofish.pro",
        }

    service_kwargs: dict[str, Any] = {
        "db_path": args.db_path or "data/orders.db",
    }
    if service_config:
        service_kwargs["config"] = service_config

    service = OrderFulfillmentService(**service_kwargs)
    action = args.action

    if action == "upsert":
        if not args.order_id or not args.status:
            _json_out({"error": "Specify --order-id and --status"})
            return
        result = service.upsert_order(
            order_id=args.order_id,
            raw_status=args.status,
            session_id=args.session_id or "",
            quote_snapshot={"total_fee": args.quote_fee} if args.quote_fee is not None else {},
            item_type=args.item_type or "virtual",
        )
        _json_out(result)
        return

    if action == "deliver":
        if not args.order_id:
            _json_out({"error": "Specify --order-id"})
            return
        shipping_info = {
            "order_no": getattr(args, "ship_order_no", None) or args.order_id,
            "waybill_no": getattr(args, "waybill_no", None),
            "express_code": getattr(args, "express_code", None),
            "express_name": getattr(args, "express_name", None),
            "ship_name": getattr(args, "ship_name", None),
            "ship_mobile": getattr(args, "ship_mobile", None),
            "ship_province": getattr(args, "ship_province", None),
            "ship_city": getattr(args, "ship_city", None),
            "ship_area": getattr(args, "ship_area", None),
            "ship_address": getattr(args, "ship_address", None),
        }
        shipping_info = {k: v for k, v in shipping_info.items() if v not in (None, "")}
        _json_out(
            service.deliver(
                order_id=args.order_id,
                dry_run=bool(args.dry_run),
                shipping_info=shipping_info or None,
            )
        )
        return

    if action == "after-sales":
        if not args.order_id:
            _json_out({"error": "Specify --order-id"})
            return
        _json_out(service.create_after_sales_case(order_id=args.order_id, issue_type=args.issue_type or "delay"))
        return

    if action == "takeover":
        if not args.order_id:
            _json_out({"error": "Specify --order-id"})
            return
        _json_out({"order_id": args.order_id, "manual_takeover": service.set_manual_takeover(args.order_id, True)})
        return

    if action == "resume":
        if not args.order_id:
            _json_out({"error": "Specify --order-id"})
            return
        ok = service.set_manual_takeover(args.order_id, False)
        _json_out({"order_id": args.order_id, "manual_takeover": False if ok else None, "success": ok})
        return

    if action == "trace":
        if not args.order_id:
            _json_out({"error": "Specify --order-id"})
            return
        _json_out(service.trace_order(args.order_id))
        return

    _json_out({"error": f"Unknown orders action: {action}"})


async def cmd_virtual_goods(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401

    from src.modules.virtual_goods.service import VirtualGoodsService

    service = VirtualGoodsService(db_path=args.db_path or "data/orders.db")
    action = str(args.action or "").strip().lower()

    if action == "scheduler":
        method_name = "scheduler_dry_run" if bool(args.dry_run) else "scheduler_run"
        runner = getattr(service, method_name, None)
        if not callable(runner):
            _json_out({"ok": False, "action": f"virtual_goods_{method_name}", "error": "service_method_not_available"})
            return
        result = runner(max_events=max(int(args.max_events or 20), 1))
        _json_out(
            {
                "ok": True,
                "action": f"virtual_goods_{method_name}",
                **(result if isinstance(result, dict) else {"result": result}),
            }
        )
        return

    if action == "replay":
        if not args.event_id and not str(args.dedupe_key or "").strip():
            _json_out({"ok": False, "action": "virtual_goods_replay", "error": "Specify --event-id or --dedupe-key"})
            return
        runner = getattr(service, "replay", None)
        if not callable(runner):
            _json_out({"ok": False, "action": "virtual_goods_replay", "error": "service_method_not_available"})
            return
        result = runner(event_id=args.event_id, dedupe_key=args.dedupe_key)
        _json_out(
            {
                "ok": True,
                "action": "virtual_goods_replay",
                **(result if isinstance(result, dict) else {"result": result}),
            }
        )
        return

    if action == "manual":
        manual_action = str(args.manual_action or "").strip().lower()
        if manual_action == "list":
            runner = getattr(service, "manual_list", None)
            if not callable(runner):
                _json_out({"ok": False, "action": "virtual_goods_manual_list", "error": "service_method_not_available"})
                return
            result = runner(order_ids=list(args.order_ids or []))
            _json_out(
                {
                    "ok": True,
                    "action": "virtual_goods_manual_list",
                    **(result if isinstance(result, dict) else {"result": result}),
                }
            )
            return

        if manual_action == "set":
            if not args.order_id:
                _json_out({"ok": False, "action": "virtual_goods_manual_set", "error": "Specify --order-id"})
                return
            runner = getattr(service, "manual_set", None)
            if not callable(runner):
                _json_out({"ok": False, "action": "virtual_goods_manual_set", "error": "service_method_not_available"})
                return
            result = runner(order_id=args.order_id, enabled=bool(args.enabled))
            _json_out(
                {
                    "ok": True,
                    "action": "virtual_goods_manual_set",
                    **(result if isinstance(result, dict) else {"result": result}),
                }
            )
            return

        _json_out({"ok": False, "action": "virtual_goods_manual", "error": "Unknown --manual-action"})
        return

    if action == "inspect":
        runner = getattr(service, "inspect", None)
        if not callable(runner):
            _json_out({"ok": False, "action": "virtual_goods_inspect", "error": "service_method_not_available"})
            return
        result = runner(event_id=args.event_id, order_id=args.order_id)
        _json_out(
            {
                "ok": True,
                "action": "virtual_goods_inspect",
                **(result if isinstance(result, dict) else {"result": result}),
            }
        )
        return

    _json_out({"ok": False, "action": "virtual_goods", "error": f"Unknown virtual-goods action: {action}"})


# ---------------------------------------------------------------------------
# Argument parser registration
# ---------------------------------------------------------------------------


def add_parser(sub: argparse._SubParsersAction) -> None:
    # orders
    p = sub.add_parser("orders", help="订单履约")
    p.add_argument(
        "--action",
        required=True,
        choices=["upsert", "deliver", "after-sales", "takeover", "resume", "trace"],
    )
    p.add_argument("--order-id", help="订单 ID")
    p.add_argument("--status", help="原始订单状态")
    p.add_argument("--session-id", help="关联会话 ID")
    p.add_argument("--item-type", choices=["virtual", "physical"], default="virtual", help="订单类型")
    p.add_argument("--quote-fee", type=float, default=None, help="关联报价金额")
    p.add_argument("--issue-type", default="delay", help="售后类型：delay/refund/quality")
    p.add_argument("--db-path", default="data/orders.db", help="订单数据库路径")
    p.add_argument("--dry-run", action="store_true", help="仅模拟执行")
    p.add_argument("--ship-order-no", default=None, help="物流发货时的第三方订单号（默认复用 --order-id）")
    p.add_argument("--waybill-no", default=None, help="物流单号")
    p.add_argument("--express-code", default=None, help="快递公司编码（如 YTO）")
    p.add_argument("--express-name", default=None, help="快递公司名称（如 圆通，可自动换算编码）")
    p.add_argument("--ship-name", default=None, help="寄件人姓名")
    p.add_argument("--ship-mobile", default=None, help="寄件人手机号")
    p.add_argument("--ship-province", default=None, help="寄件省份")
    p.add_argument("--ship-city", default=None, help="寄件城市")
    p.add_argument("--ship-area", default=None, help="寄件区县")
    p.add_argument("--ship-address", default=None, help="寄件详细地址")
    p.add_argument("--xgj-app-key", default=None, help="闲管家 AppKey（启用 API 发货）")
    p.add_argument("--xgj-app-secret", default=None, help="闲管家 AppSecret（启用 API 发货）")
    p.add_argument("--xgj-merchant-id", default=None, help="闲管家商家 ID（如需要）")
    p.add_argument("--xgj-base-url", default="https://open.goofish.pro", help="闲管家 API 地址")

    # virtual-goods
    p = sub.add_parser("virtual-goods", help="虚拟商品回调调度/重放/人工接管")
    p.add_argument("--action", required=True, choices=["scheduler", "replay", "manual", "inspect"])
    p.add_argument("--db-path", default="data/orders.db", help="虚拟商品数据库路径")
    p.add_argument("--dry-run", action="store_true", help="scheduler 仅预览，不执行")
    p.add_argument("--max-events", type=int, default=20, help="scheduler 每次最多处理事件数")
    p.add_argument("--event-id", default=None, help="回调事件ID（用于 replay/inspect）")
    p.add_argument("--dedupe-key", default=None, help="回调去重键（用于 replay）")
    p.add_argument("--manual-action", choices=["list", "set"], default=None, help="manual 子动作")
    p.add_argument("--order-id", default=None, help="订单ID（manual set / inspect）")
    p.add_argument("--order-ids", nargs="*", default=[], help="订单ID列表（manual list）")
    p.add_argument("--enabled", action="store_true", help="manual set 开关（默认关闭）")
