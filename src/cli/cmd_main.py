"""
Primary listing / operations commands: publish, polish, price, delist, relist,
analytics, accounts, messages.
"""

from __future__ import annotations

import argparse

# _run_messages_sla_benchmark and _json_out are imported from src.cli (the compatibility
# shim) via local imports inside command functions so that tests patching those names
# at src.cli always see the correct (possibly-patched) binding at call time.
from .base import _messages_requires_browser_runtime, _resolve_workflow_state, _run_messages_sla_benchmark  # noqa: F401

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
#
# _json_out is looked up dynamically inside each function (via a local import)
# so that tests patching src.cli._json_out always intercept the correct binding.
# ---------------------------------------------------------------------------


async def cmd_publish(args: argparse.Namespace) -> None:
    # Dynamic lookup so tests patching src.cli._json_out work correctly.
    from src.cli import _json_out  # noqa: F401
    from src.core.browser_client import create_browser_client
    from src.modules.listing.models import Listing
    from src.modules.listing.service import ListingService

    client = await create_browser_client()
    try:
        service = ListingService(controller=client)
        listing = Listing(
            title=args.title,
            description=args.description or "",
            price=args.price,
            original_price=args.original_price,
            category=args.category or "其他闲置",
            images=args.images or [],
            tags=args.tags or [],
        )
        result = await service.create_listing(listing)
        _json_out(
            {
                "success": result.success,
                "product_id": result.product_id,
                "product_url": result.product_url,
                "error": result.error_message,
            }
        )
    finally:
        await client.disconnect()


async def cmd_polish(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401
    from src.core.browser_client import create_browser_client
    from src.modules.operations.service import OperationsService

    client = await create_browser_client()
    try:
        service = OperationsService(controller=client)
        if args.all:
            result = await service.batch_polish(max_items=args.max)
        elif args.id:
            result = await service.polish_listing(args.id)
        else:
            _json_out({"error": "Specify --all or --id <product_id>"})
            return
        _json_out(result)
    finally:
        await client.disconnect()


async def cmd_price(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401
    from src.core.browser_client import create_browser_client
    from src.modules.operations.service import OperationsService

    client = await create_browser_client()
    try:
        service = OperationsService(controller=client)
        result = await service.update_price(args.id, args.price, args.original_price)
        _json_out(result)
    finally:
        await client.disconnect()


async def cmd_delist(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401
    from src.core.browser_client import create_browser_client
    from src.modules.operations.service import OperationsService

    client = await create_browser_client()
    try:
        service = OperationsService(controller=client)
        result = await service.delist(args.id, reason=args.reason or "不卖了")
        _json_out(result)
    finally:
        await client.disconnect()


async def cmd_relist(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401
    from src.core.browser_client import create_browser_client
    from src.modules.operations.service import OperationsService

    client = await create_browser_client()
    try:
        service = OperationsService(controller=client)
        result = await service.relist(args.id)
        _json_out(result)
    finally:
        await client.disconnect()


async def cmd_analytics(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401
    from src.modules.analytics.service import AnalyticsService

    service = AnalyticsService()
    action = args.action

    if action == "dashboard":
        result = await service.get_dashboard_stats()
    elif action == "daily":
        result = await service.get_daily_report()
    elif action == "trend":
        result = await service.get_trend_data(
            metric=args.metric or "views",
            days=args.days or 30,
        )
    elif action == "export":
        filepath = await service.export_data(
            data_type=args.type or "products",
            format=args.format or "csv",
        )
        result = {"filepath": filepath}
    else:
        result = {"error": f"Unknown analytics action: {action}"}

    _json_out(result)


async def cmd_accounts(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401
    from src.modules.accounts.service import AccountsService

    service = AccountsService()
    action = args.action

    if action == "list":
        result = service.get_accounts()
    elif action == "health":
        if not args.id:
            _json_out({"error": "Specify --id <account_id>"})
            return
        result = service.get_account_health(args.id)
    elif action == "validate":
        if not args.id:
            _json_out({"error": "Specify --id <account_id>"})
            return
        result = {"valid": service.validate_cookie(args.id)}
    elif action == "refresh-cookie":
        if not args.id or not args.cookie:
            _json_out({"error": "Specify --id and --cookie"})
            return
        result = service.refresh_cookie(args.id, args.cookie)
    else:
        result = {"error": f"Unknown accounts action: {action}"}

    _json_out(result)


async def cmd_messages(args: argparse.Namespace) -> None:
    from src.cli import _json_out  # noqa: F401

    action = args.action

    if action == "sla-benchmark":
        # Dynamic import so tests patching src.cli._run_messages_sla_benchmark work.
        from src.cli import _run_messages_sla_benchmark  # noqa: F401

        result = await _run_messages_sla_benchmark(
            count=int(args.benchmark_count or 120),
            concurrency=int(args.concurrency or 1),
            quote_ratio=float(args.quote_ratio or 0.75),
            quote_only=bool(args.quote_only),
            seed=int(args.seed or 42),
            slowest=int(args.slowest or 8),
            warmup=int(args.warmup or 3),
        )
        _json_out(result)
        return

    if action in {"workflow-stats", "workflow-status"}:
        from src.modules.messages.workflow import WorkflowStore

        store = WorkflowStore(db_path=args.workflow_db)
        _json_out(
            {
                "workflow": store.get_workflow_summary(),
                "sla": store.get_sla_summary(window_minutes=args.window_minutes or 1440),
            }
        )
        return

    if action == "workflow-transition":
        from src.modules.messages.workflow import WorkflowStore

        if not args.session_id or not args.stage:
            _json_out({"error": "Specify --session-id and --stage"})
            return

        target_state = _resolve_workflow_state(args.stage)
        if target_state is None:
            _json_out({"error": f"Unknown workflow stage: {args.stage}"})
            return

        store = WorkflowStore(db_path=args.workflow_db)
        ok = store.transition_state(
            session_id=args.session_id,
            to_state=target_state,
            reason="cli_workflow_transition",
            metadata={"source": "cli", "requested_stage": args.stage},
        )
        forced = False
        if not ok and bool(args.force_state):
            ok = store.force_state(
                session_id=args.session_id,
                to_state=target_state,
                reason="cli_workflow_transition_force",
                metadata={"source": "cli", "requested_stage": args.stage, "force_state": True},
            )
            forced = bool(ok)

        _json_out(
            {
                "session_id": args.session_id,
                "target_state": target_state.value,
                "success": bool(ok),
                "forced": forced,
                "session": store.get_session(args.session_id),
            }
        )
        return

    from src.modules.messages.service import MessagesService

    client = None
    service: MessagesService | None = None
    if _messages_requires_browser_runtime():
        from src.core.browser_client import create_browser_client

        client = await create_browser_client()

    try:
        service = MessagesService(controller=client)

        if action == "list-unread":
            result = await service.get_unread_sessions(limit=args.limit or 20)
            _json_out({"total": len(result), "sessions": result})
            return

        if action == "reply":
            if not args.session_id or not args.text:
                _json_out({"error": "Specify --session-id and --text"})
                return
            sent = await service.reply_to_session(args.session_id, args.text)
            _json_out(
                {
                    "session_id": args.session_id,
                    "reply": args.text,
                    "success": bool(sent),
                }
            )
            return

        if action == "auto-reply":
            result = await service.auto_reply_unread(limit=args.limit or 20, dry_run=bool(args.dry_run))
            _json_out(result)
            return

        if action == "auto-workflow":
            from src.modules.messages.workflow import WorkflowWorker

            worker = WorkflowWorker(
                message_service=service,
                config={
                    "db_path": args.workflow_db,
                    "poll_interval_seconds": args.interval,
                    "scan_limit": args.limit,
                },
            )

            if args.daemon:
                result = await worker.run_forever(
                    dry_run=bool(args.dry_run),
                    max_loops=args.max_loops,
                )
            else:
                result = await worker.run_once(dry_run=bool(args.dry_run))
            _json_out(result)
            return

        _json_out({"error": f"Unknown messages action: {action}"})
    finally:
        if service is not None:
            await service.close()
        if client is not None:
            await client.disconnect()


# ---------------------------------------------------------------------------
# Argument parser registration
# ---------------------------------------------------------------------------


def add_parser(sub: argparse._SubParsersAction) -> None:
    # publish
    p = sub.add_parser("publish", help="发布商品")
    p.add_argument("--title", required=True, help="商品标题")
    p.add_argument("--price", type=float, required=True, help="售价")
    p.add_argument("--description", default="", help="商品描述")
    p.add_argument("--original-price", type=float, default=None, help="原价")
    p.add_argument("--category", default="其他闲置", help="分类")
    p.add_argument("--images", nargs="*", default=[], help="图片路径列表")
    p.add_argument("--tags", nargs="*", default=[], help="标签列表")

    # polish
    p = sub.add_parser("polish", help="擦亮商品")
    p.add_argument("--all", action="store_true", help="擦亮所有商品")
    p.add_argument("--id", help="擦亮指定商品")
    p.add_argument("--max", type=int, default=50, help="最大擦亮数量")

    # price
    p = sub.add_parser("price", help="调整价格")
    p.add_argument("--id", required=True, help="商品 ID")
    p.add_argument("--price", type=float, required=True, help="新价格")
    p.add_argument("--original-price", type=float, default=None, help="原价")

    # delist
    p = sub.add_parser("delist", help="下架商品")
    p.add_argument("--id", required=True, help="商品 ID")
    p.add_argument("--reason", default="不卖了", help="下架原因")

    # relist
    p = sub.add_parser("relist", help="重新上架")
    p.add_argument("--id", required=True, help="商品 ID")

    # analytics
    p = sub.add_parser("analytics", help="数据分析")
    p.add_argument("--action", required=True, choices=["dashboard", "daily", "trend", "export"])
    p.add_argument("--metric", default="views", help="趋势指标")
    p.add_argument("--days", type=int, default=30, help="天数")
    p.add_argument("--type", default="products", help="导出类型")
    p.add_argument("--format", default="csv", help="导出格式")

    # accounts
    p = sub.add_parser("accounts", help="账号管理")
    p.add_argument("--action", required=True, choices=["list", "health", "validate", "refresh-cookie"])
    p.add_argument("--id", help="账号 ID")
    p.add_argument("--cookie", help="新的 Cookie 值")

    # messages
    p = sub.add_parser("messages", help="消息自动回复")
    p.add_argument(
        "--action",
        required=True,
        choices=[
            "list-unread",
            "reply",
            "auto-reply",
            "auto-workflow",
            "sla-benchmark",
            "workflow-stats",
            "workflow-status",
            "workflow-transition",
        ],
    )
    p.add_argument("--limit", type=int, default=20, help="最多处理会话数")
    p.add_argument("--session-id", help="会话 ID（reply 时必填）")
    p.add_argument("--text", help="回复内容（reply 时必填）")
    p.add_argument("--stage", help="工作流目标阶段（workflow-transition 时必填）")
    p.add_argument("--force-state", action="store_true", help="非法迁移时强制写入状态")
    p.add_argument("--dry-run", action="store_true", help="仅生成回复，不真正发送")
    p.add_argument("--daemon", action="store_true", help="常驻运行 workflow worker")
    p.add_argument("--max-loops", type=int, default=None, help="daemon 模式下最多循环次数")
    p.add_argument("--interval", type=float, default=1.0, help="worker 轮询间隔（秒）")
    p.add_argument("--workflow-db", default=None, help="workflow 数据库路径")
    p.add_argument("--window-minutes", type=int, default=1440, help="SLA 统计窗口（分钟）")
    p.add_argument("--benchmark-count", type=int, default=120, help="sla-benchmark 样本数量")
    p.add_argument("--concurrency", type=int, default=1, help="sla-benchmark 并发度")
    p.add_argument("--quote-ratio", type=float, default=0.75, help="sla-benchmark 报价消息比例")
    p.add_argument("--quote-only", action="store_true", help="sla-benchmark 仅生成完整报价消息")
    p.add_argument("--seed", type=int, default=42, help="sla-benchmark 随机种子")
    p.add_argument("--warmup", type=int, default=3, help="sla-benchmark 预热样本数（不计入统计）")
    p.add_argument("--slowest", type=int, default=8, help="sla-benchmark 输出最慢样本数")
