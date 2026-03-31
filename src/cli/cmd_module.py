"""
Module-level commands: module, doctor, automation, compliance, ai, growth.
These commands depend on _module_* helpers from base.py.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any

from src.core.logger import get_logger

# Import _json_out from src.cli (the compatibility shim) so that tests patching
# src.cli._json_out correctly intercept all calls across all modules.
from src.cli import _json_out as _json_out_mod  # noqa: F401

from .base import (
    _EXPECTED_PROJECT_ROOT,
    _MODULE_TARGETS,
    _messages_requires_browser_runtime,
    _module_logs,
)
from .base import (
    _module_process_status as _module_process_status_mod,  # noqa: F401
)

# _json_out above is a fallback for use in internal helpers that are NOT called
# from tests.  Command functions re-bind it dynamically (see below).


# ---------------------------------------------------------------------------
# Internal helpers (used by cmd_module and doctor/automation internally)
# ---------------------------------------------------------------------------


async def _create_presales_browser_client_if_available() -> Any | None:
    if _messages_requires_browser_runtime():
        from src.core.browser_client import create_browser_client

        return await create_browser_client()

    try:
        from src.core.browser_client import create_browser_client

        client = await create_browser_client()
        get_logger().info("Presales browser client connected for WS empty-queue DOM fallback")
        return client
    except Exception as exc:
        get_logger().warning("Presales browser fallback unavailable in ws mode: %s", exc)
        return None


async def _start_presales_module(args: argparse.Namespace) -> dict[str, Any]:
    from src.modules.messages.service import MessagesService
    from src.modules.messages.workflow import WorkflowWorker

    client = await _create_presales_browser_client_if_available()

    service: MessagesService | None = None
    try:
        service = MessagesService(controller=client)
        worker = WorkflowWorker(
            message_service=service,
            config={
                "db_path": args.workflow_db,
                "poll_interval_seconds": args.interval,
                "scan_limit": args.limit,
                "claim_limit": args.claim_limit,
            },
        )
        if args.mode == "daemon":
            result = await worker.run_forever(
                dry_run=bool(args.dry_run),
                max_loops=args.max_loops,
            )
        else:
            result = await worker.run_once(dry_run=bool(args.dry_run))
        return {"target": "presales", "mode": args.mode, "result": result}
    finally:
        if service is not None:
            await service.close()
        if client is not None:
            await client.disconnect()


def _init_default_operation_tasks(args: argparse.Namespace) -> dict[str, Any]:
    from src.core.config import get_config
    from src.modules.accounts.scheduler import Scheduler, TaskType

    scheduler = Scheduler()
    created: list[dict[str, Any]] = []

    if not bool(args.init_default_tasks):
        return {"scheduler": scheduler, "created": created}

    tasks = scheduler.list_tasks()
    has_polish = any(t.task_type == TaskType.POLISH for t in tasks)
    has_metrics = any(t.task_type == TaskType.METRICS for t in tasks)

    cfg = get_config().get_section("scheduler", {})
    polish_cfg = cfg.get("polish", {}) if isinstance(cfg.get("polish"), dict) else {}
    metrics_cfg = cfg.get("metrics", {}) if isinstance(cfg.get("metrics"), dict) else {}

    if not args.skip_polish and not has_polish:
        cron_expr = str(args.polish_cron or polish_cfg.get("cron") or "0 9 * * *")
        task = scheduler.create_polish_task(cron_expression=cron_expr, max_items=int(args.polish_max_items or 50))
        created.append({"task_id": task.task_id, "task_type": task.task_type, "name": task.name})

    if not args.skip_metrics and not has_metrics:
        cron_expr = str(args.metrics_cron or metrics_cfg.get("cron") or "0 */4 * * *")
        task = scheduler.create_metrics_task(cron_expression=cron_expr)
        created.append({"task_id": task.task_id, "task_type": task.task_type, "name": task.name})

    return {"scheduler": scheduler, "created": created}


async def _start_operations_module(args: argparse.Namespace) -> dict[str, Any]:
    from src.modules.accounts.scheduler import TaskType

    setup = _init_default_operation_tasks(args)
    scheduler = setup["scheduler"]
    created = setup["created"]

    if args.mode == "once":
        task_results = []
        for task in scheduler.list_tasks(enabled_only=True):
            if args.skip_polish and task.task_type == TaskType.POLISH:
                continue
            if args.skip_metrics and task.task_type == TaskType.METRICS:
                continue
            task_results.append(await scheduler.execute_task(task))

        success = sum(1 for item in task_results if bool(item.get("success", False)))
        return {
            "target": "operations",
            "mode": "once",
            "created_tasks": created,
            "executed_tasks": len(task_results),
            "success_tasks": success,
            "failed_tasks": len(task_results) - success,
            "results": task_results,
        }

    await scheduler.start()
    loops = 0
    try:
        while True:
            loops += 1
            if args.max_loops and loops >= args.max_loops:
                break
            await asyncio.sleep(max(1.0, float(args.interval or 30.0)))
    finally:
        await scheduler.stop()

    return {
        "target": "operations",
        "mode": "daemon",
        "loops": loops,
        "created_tasks": created,
        "status": scheduler.get_scheduler_status(),
    }


async def _run_aftersales_once(args: argparse.Namespace, message_service: Any | None = None) -> dict[str, Any]:
    from src.modules.orders.service import OrderFulfillmentService

    service = OrderFulfillmentService(db_path=args.orders_db or "data/orders.db")
    cases = service.list_orders(
        status="after_sales",
        limit=max(int(args.limit or 20), 1),
        include_manual=bool(args.include_manual),
    )

    details: list[dict[str, Any]] = []
    for case in cases:
        order_id = str(case.get("order_id", ""))
        session_id = str(case.get("session_id", ""))
        issue_type = str(args.issue_type or "delay")
        reply_text = service.generate_after_sales_reply(issue_type=issue_type)

        sent = False
        reason = ""
        if not session_id:
            reason = "missing_session_id"
        elif bool(args.dry_run):
            sent = True
            reason = "dry_run"
        elif message_service is None:
            reason = "message_service_unavailable"
        else:
            sent = await message_service.reply_to_session(session_id, reply_text)
            reason = "sent" if sent else "send_failed"

        service.record_after_sales_followup(
            order_id=order_id,
            issue_type=issue_type,
            reply_text=reply_text,
            sent=sent,
            dry_run=bool(args.dry_run),
            reason=reason,
            session_id=session_id,
        )
        details.append(
            {
                "order_id": order_id,
                "session_id": session_id,
                "manual_takeover": bool(case.get("manual_takeover", False)),
                "issue_type": issue_type,
                "reply_template": reply_text,
                "sent": sent,
                "reason": reason,
            }
        )

    success = sum(1 for item in details if bool(item.get("sent", False)))
    return {
        "target": "aftersales",
        "total_cases": len(cases),
        "success_cases": success,
        "failed_cases": len(cases) - success,
        "dry_run": bool(args.dry_run),
        "details": details,
    }


async def _start_aftersales_module(args: argparse.Namespace) -> dict[str, Any]:
    from src.modules.messages.service import MessagesService
    from src.modules.orders.service import OrderFulfillmentService

    service = OrderFulfillmentService(db_path=args.orders_db or "data/orders.db")
    if args.mode == "once":
        if bool(args.dry_run):
            result = await _run_aftersales_once(args, message_service=None)
        else:
            client = None
            if _messages_requires_browser_runtime():
                from src.core.browser_client import create_browser_client

                client = await create_browser_client()
            message_service: MessagesService | None = None
            try:
                message_service = MessagesService(controller=client)
                result = await _run_aftersales_once(args, message_service=message_service)
            finally:
                if message_service is not None:
                    await message_service.close()
                if client is not None:
                    await client.disconnect()

        return {
            "target": "aftersales",
            "mode": "once",
            "result": result,
            "summary": service.get_summary(),
        }

    loops = 0
    batches: list[dict[str, Any]] = []
    if bool(args.dry_run):
        while True:
            loops += 1
            batch = await _run_aftersales_once(args, message_service=None)
            batches.append(
                {
                    "loop": loops,
                    "total_cases": batch.get("total_cases", 0),
                    "success_cases": batch.get("success_cases", 0),
                    "failed_cases": batch.get("failed_cases", 0),
                }
            )
            if args.max_loops and loops >= args.max_loops:
                break
            await asyncio.sleep(max(1.0, float(args.interval or 30.0)))
    else:
        client = None
        if _messages_requires_browser_runtime():
            from src.core.browser_client import create_browser_client

            client = await create_browser_client()
        message_service: MessagesService | None = None
        try:
            message_service = MessagesService(controller=client)
            while True:
                loops += 1
                batch = await _run_aftersales_once(args, message_service=message_service)
                batches.append(
                    {
                        "loop": loops,
                        "total_cases": batch.get("total_cases", 0),
                        "success_cases": batch.get("success_cases", 0),
                        "failed_cases": batch.get("failed_cases", 0),
                    }
                )
                if args.max_loops and loops >= args.max_loops:
                    break
                await asyncio.sleep(max(1.0, float(args.interval or 30.0)))
        finally:
            if message_service is not None:
                await message_service.close()
            if client is not None:
                await client.disconnect()

    return {
        "target": "aftersales",
        "mode": "daemon",
        "loops": loops,
        "batches": batches,
        "summary": service.get_summary(),
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


async def cmd_module(args: argparse.Namespace) -> None:
    from src.cli import (
        _clear_module_runtime_state,
        _json_out,
        _module_check_summary,
        _module_process_status,
        _start_background_module,
        _stop_background_module,
    )
    from src.core.doctor import run_doctor
    from src.modules.accounts.scheduler import Scheduler
    from src.modules.messages.workflow import WorkflowStore
    from src.modules.orders.service import OrderFulfillmentService

    action = args.action
    target = args.target

    def _status_payload(single_target: str) -> dict[str, Any]:
        if single_target == "presales":
            store = WorkflowStore(db_path=args.workflow_db)
            return {
                "target": single_target,
                "process": _module_process_status(single_target),
                "workflow": store.get_workflow_summary(),
                "sla": store.get_sla_summary(window_minutes=args.window_minutes or 1440),
            }

        if single_target == "aftersales":
            service = OrderFulfillmentService(db_path=args.orders_db or "data/orders.db")
            preview = service.list_orders(
                status="after_sales",
                limit=max(int(args.limit or 20), 1),
                include_manual=True,
            )
            return {
                "target": single_target,
                "process": _module_process_status(single_target),
                "summary": service.get_summary(),
                "recent_after_sales_cases": [
                    {
                        "order_id": item.get("order_id"),
                        "session_id": item.get("session_id"),
                        "manual_takeover": bool(item.get("manual_takeover", False)),
                        "updated_at": item.get("updated_at", ""),
                    }
                    for item in preview
                ],
            }

        scheduler = Scheduler()
        return {
            "target": single_target,
            "process": _module_process_status(single_target),
            "scheduler": scheduler.get_scheduler_status(),
        }

    if action == "check":
        report = run_doctor(skip_quote=(target not in {"presales", "all"}))

        if target == "all":
            modules = {name: _module_check_summary(target=name, doctor_report=report) for name in _MODULE_TARGETS}
            blockers: list[dict[str, Any]] = []
            for name, item in modules.items():
                for blocker in item.get("blockers", []):
                    payload = dict(blocker)
                    payload["target"] = name
                    blockers.append(payload)
            result = {
                "target": "all",
                "runtime": next(iter(modules.values())).get("runtime", "auto"),
                "ready": all(bool(item.get("ready", False)) for item in modules.values()),
                "modules": modules,
                "blockers": blockers,
                "next_steps": report.get("next_steps", []),
                "doctor_summary": report.get("summary", {}),
            }
            _json_out(result)
            if bool(args.strict) and not result["ready"]:
                raise SystemExit(2)
            return

        summary = _module_check_summary(target=target, doctor_report=report)
        _json_out(summary)
        if bool(args.strict) and not bool(summary.get("ready", False)):
            raise SystemExit(2)
        return

    if action == "status":
        if target == "all":
            modules = {name: _status_payload(name) for name in _MODULE_TARGETS}
            alive_count = sum(1 for item in modules.values() if bool(item.get("process", {}).get("alive", False)))
            _json_out(
                {
                    "target": "all",
                    "modules": modules,
                    "alive_count": alive_count,
                    "total_modules": len(modules),
                }
            )
            return

        _json_out(_status_payload(target))
        return

    if action == "start":
        if target == "all":
            if not bool(args.background):
                _json_out({"error": "start --target all requires --background to avoid blocking"})
                raise SystemExit(2)
            if args.mode != "daemon":
                _json_out({"error": "start --target all only supports --mode daemon"})
                raise SystemExit(2)
            _json_out(
                {
                    "target": "all",
                    "action": "start",
                    "modules": {name: _start_background_module(target=name, args=args) for name in _MODULE_TARGETS},
                }
            )
            return

        if bool(args.background):
            if args.mode != "daemon":
                _json_out({"error": "background start only supports --mode daemon"})
                raise SystemExit(2)
            _json_out(_start_background_module(target=target, args=args))
            return

        if target == "presales":
            result = await _start_presales_module(args)
        elif target == "operations":
            result = await _start_operations_module(args)
        else:
            result = await _start_aftersales_module(args)
        _json_out(result)
        return

    if action == "stop":
        if target == "all":
            _json_out(
                {
                    "target": "all",
                    "action": "stop",
                    "modules": {
                        name: _stop_background_module(target=name, timeout_seconds=float(args.stop_timeout or 6.0))
                        for name in _MODULE_TARGETS
                    },
                }
            )
            return

        _json_out(_stop_background_module(target=target, timeout_seconds=float(args.stop_timeout or 6.0)))
        return

    if action == "restart":
        if target == "all":
            results: dict[str, Any] = {}
            for name in _MODULE_TARGETS:
                stopped = _stop_background_module(target=name, timeout_seconds=float(args.stop_timeout or 6.0))
                started = _start_background_module(target=name, args=args)
                results[name] = {"target": name, "stopped": stopped, "started": started}
            _json_out({"target": "all", "action": "restart", "modules": results})
            return

        stopped = _stop_background_module(target=target, timeout_seconds=float(args.stop_timeout or 6.0))
        started = _start_background_module(target=target, args=args)
        _json_out({"target": target, "stopped": stopped, "started": started})
        return

    if action == "recover":

        def _recover_one(single_target: str) -> dict[str, Any]:
            stopped = _stop_background_module(target=single_target, timeout_seconds=float(args.stop_timeout or 6.0))
            cleanup = _clear_module_runtime_state(target=single_target)
            started = _start_background_module(target=single_target, args=args)
            recovered = bool(started.get("started")) or str(started.get("reason", "")) == "already_running"
            return {
                "target": single_target,
                "stopped": stopped,
                "cleanup": cleanup,
                "started": started,
                "recovered": recovered,
            }

        if target == "all":
            modules = {name: _recover_one(name) for name in _MODULE_TARGETS}
            _json_out({"target": "all", "action": "recover", "modules": modules})
            return

        _json_out(_recover_one(target))
        return

    if action == "cookie-health":
        from src.core.cookie_health import CookieHealthChecker

        cookie_text = os.getenv("XIANYU_COOKIE_1", "")
        checker = CookieHealthChecker(cookie_text=cookie_text, timeout_seconds=10.0)
        result = checker.check_sync(force=True)
        _json_out(result)
        if not result.get("healthy", False):
            raise SystemExit(2)
        return

    if action == "logs":
        if target == "all":
            _json_out(
                {
                    "target": "all",
                    "action": "logs",
                    "modules": {
                        name: _module_logs(target=name, tail_lines=int(args.tail_lines or 80))
                        for name in _MODULE_TARGETS
                    },
                }
            )
            return

        _json_out(_module_logs(target=target, tail_lines=int(args.tail_lines or 80)))
        return

    _json_out({"error": f"Unknown module action: {action}"})


async def cmd_doctor(args: argparse.Namespace) -> None:
    from pathlib import Path

    from src.cli import _json_out
    from src.core.doctor import run_doctor

    report = run_doctor(skip_quote=bool(args.skip_quote))
    strict = bool(args.strict)
    project_root = str(Path.cwd().resolve())
    project_root_match = (not _EXPECTED_PROJECT_ROOT) or (project_root == _EXPECTED_PROJECT_ROOT)
    strict_ready = (
        bool(report.get("ready", False))
        and report.get("summary", {}).get("warning_failed", 0) == 0
        and project_root_match
    )

    output = {
        **report,
        "strict": strict,
        "strict_ready": strict_ready,
        "project_root": project_root,
        "expected_project_root": _EXPECTED_PROJECT_ROOT,
        "project_root_match": project_root_match,
    }
    _json_out(output)

    if not output["ready"] or (strict and not strict_ready):
        raise SystemExit(2)


async def cmd_automation(args: argparse.Namespace) -> None:
    from src.cli import _json_out
    from src.modules.messages.notifications import FeishuNotifier
    from src.modules.messages.setup import AutomationSetupService

    action = args.action
    setup_service = AutomationSetupService(config_path=args.config_path or "config/config.yaml")

    if action == "status":
        _json_out(setup_service.status())
        return

    if action == "setup":
        feishu_enabled = bool(args.enable_feishu or str(args.feishu_webhook or "").strip())
        result = setup_service.apply(
            poll_interval_seconds=float(args.poll_interval or 1.0),
            scan_limit=int(args.scan_limit or 20),
            claim_limit=int(args.claim_limit or 10),
            reply_target_seconds=float(args.reply_target_seconds or 3.0),
            feishu_enabled=feishu_enabled,
            feishu_webhook=str(args.feishu_webhook or "").strip(),
            notify_on_start=bool(args.notify_on_start),
            notify_on_alert=not bool(args.disable_notify_on_alert),
            notify_recovery=not bool(args.disable_notify_recovery),
            heartbeat_minutes=int(args.heartbeat_minutes or 30),
        )
        _json_out(result)
        return

    if action == "test-feishu":
        webhook = str(args.feishu_webhook or "").strip() or setup_service.get_feishu_webhook()
        if not webhook:
            _json_out({"error": "No feishu webhook configured. Use --feishu-webhook or run automation setup first."})
            raise SystemExit(2)

        notifier = FeishuNotifier(webhook_url=webhook)
        text = str(args.message or "【闲鱼自动化】飞书通知测试成功")
        ok = await notifier.send_text(text)
        _json_out({"success": ok, "message": text})
        if not ok:
            raise SystemExit(2)
        return

    _json_out({"error": f"Unknown automation action: {action}"})


async def cmd_compliance(args: argparse.Namespace) -> None:
    from src.cli import _json_out
    from src.modules.compliance.center import ComplianceCenter

    center = ComplianceCenter(policy_path=args.policy_path, db_path=args.db_path)
    action = args.action

    if action == "reload":
        center.reload()
        _json_out({"success": True, "policy_path": args.policy_path})
        return

    if action == "check":
        decision = center.evaluate_before_send(
            args.content or "",
            actor=args.actor or "cli",
            account_id=args.account_id,
            session_id=args.session_id,
            action=args.audit_action or "message_send",
        )
        _json_out(decision.to_dict())
        return

    if action == "replay":
        result = center.replay(
            account_id=args.account_id,
            session_id=args.session_id,
            blocked_only=bool(args.blocked_only),
            limit=args.limit or 50,
        )
        _json_out({"total": len(result), "events": result})
        return

    _json_out({"error": f"Unknown compliance action: {action}"})


async def cmd_ai(args: argparse.Namespace) -> None:
    from src.cli import _json_out
    from src.modules.content.service import ContentService

    service = ContentService()
    action = args.action

    if action == "cost-stats":
        _json_out(service.get_ai_cost_stats())
        return

    if action == "simulate-publish":
        title = service.generate_title(
            product_name=args.product_name or "iPhone 15 Pro",
            features=["95新", "国行", "自用"],
            category=args.category or "数码手机",
        )
        desc = service.generate_description(
            product_name=args.product_name or "iPhone 15 Pro",
            condition="95新",
            reason="升级换机",
            tags=["闲置", "自用"],
        )
        _json_out({"title": title, "description": desc, "stats": service.get_ai_cost_stats()})
        return

    _json_out({"error": f"Unknown ai action: {action}"})


async def cmd_growth(args: argparse.Namespace) -> None:
    from src.cli import _json_out
    from src.modules.growth.service import GrowthService

    service = GrowthService(db_path=args.db_path or "data/growth.db")
    action = args.action

    if action == "set-strategy":
        if not args.strategy_type or not args.version:
            _json_out({"error": "Specify --strategy-type and --version"})
            return
        _json_out(
            service.set_strategy_version(
                strategy_type=args.strategy_type,
                version=args.version,
                active=bool(args.active),
                baseline=bool(args.baseline),
            )
        )
        return

    if action == "rollback":
        if not args.strategy_type:
            _json_out({"error": "Specify --strategy-type"})
            return
        _json_out({"rolled_back": service.rollback_to_baseline(args.strategy_type)})
        return

    if action == "assign":
        if not args.experiment_id or not args.subject_id:
            _json_out({"error": "Specify --experiment-id and --subject-id"})
            return
        variants = tuple((args.variants or "A,B").split(","))
        _json_out(
            service.assign_variant(
                experiment_id=args.experiment_id,
                subject_id=args.subject_id,
                variants=variants,
                strategy_version=args.version,
            )
        )
        return

    if action == "event":
        if not args.subject_id or not args.stage:
            _json_out({"error": "Specify --subject-id and --stage"})
            return
        _json_out(
            service.record_event(
                subject_id=args.subject_id,
                stage=args.stage,
                experiment_id=args.experiment_id,
                variant=args.variant,
                strategy_version=args.version,
            )
        )
        return

    if action == "funnel":
        _json_out(service.funnel_stats(days=args.days or 7, bucket=args.bucket or "day"))
        return

    if action == "compare":
        if not args.experiment_id:
            _json_out({"error": "Specify --experiment-id"})
            return
        _json_out(
            service.compare_variants(
                experiment_id=args.experiment_id,
                from_stage=args.from_stage or "inquiry",
                to_stage=args.to_stage or "ordered",
            )
        )
        return

    _json_out({"error": f"Unknown growth action: {action}"})


# ---------------------------------------------------------------------------
# Argument parser registration
# ---------------------------------------------------------------------------


def add_parser(sub: argparse._SubParsersAction) -> None:
    # compliance
    p = sub.add_parser("compliance", help="合规策略中心")
    p.add_argument("--action", required=True, choices=["reload", "check", "replay"])
    p.add_argument("--policy-path", default="config/compliance_policies.yaml", help="策略配置路径")
    p.add_argument("--db-path", default="data/compliance.db", help="合规审计库路径")
    p.add_argument("--content", default="", help="待检查内容")
    p.add_argument("--actor", default="cli", help="执行者标识")
    p.add_argument("--account-id", default=None, help="账号ID")
    p.add_argument("--session-id", default=None, help="会话ID")
    p.add_argument("--audit-action", default="message_send", help="审计动作类型")
    p.add_argument("--blocked-only", action="store_true", help="仅查看拦截事件")

    # ai
    p = sub.add_parser("ai", help="AI 调用降本与统计")
    p.add_argument("--action", required=True, choices=["cost-stats", "simulate-publish"])
    p.add_argument("--product-name", default="iPhone 15 Pro", help="模拟商品名")
    p.add_argument("--category", default="数码手机", help="模拟商品分类")

    # doctor
    p = sub.add_parser("doctor", help="运行系统自检并输出修复建议")
    p.add_argument("--skip-quote", action="store_true", help="跳过自动报价成本源检查")
    p.add_argument("--strict", action="store_true", help="警告也按失败处理（返回非0）")

    # automation
    p = sub.add_parser("automation", help="自动化推进配置与飞书接入")
    p.add_argument("--action", required=True, choices=["setup", "status", "test-feishu"])
    p.add_argument("--config-path", default="config/config.yaml", help="配置文件路径")
    p.add_argument("--poll-interval", type=float, default=1.0, help="workflow 轮询间隔（秒）")
    p.add_argument("--scan-limit", type=int, default=20, help="每轮扫描会话数")
    p.add_argument("--claim-limit", type=int, default=10, help="每轮最大认领任务数")
    p.add_argument("--reply-target-seconds", type=float, default=3.0, help="自动首响目标时延（秒）")
    p.add_argument("--enable-feishu", action="store_true", help="启用飞书 webhook 通知")
    p.add_argument("--feishu-webhook", default="", help="飞书机器人 webhook URL")
    p.add_argument("--notify-on-start", action="store_true", help="worker 启动时发送通知")
    p.add_argument("--disable-notify-on-alert", action="store_true", help="关闭 SLA 告警通知")
    p.add_argument("--disable-notify-recovery", action="store_true", help="关闭告警恢复通知")
    p.add_argument("--heartbeat-minutes", type=int, default=30, help="心跳通知周期（分钟，0=关闭）")
    p.add_argument("--message", default="【闲鱼自动化】飞书通知测试成功", help="test-feishu 测试消息")

    # module
    p = sub.add_parser("module", help="模块化可用性检查与启动（售前/运营/售后）")
    p.add_argument(
        "--action",
        required=True,
        choices=["check", "status", "start", "stop", "restart", "recover", "logs", "cookie-health"],
    )
    p.add_argument("--target", required=True, choices=["presales", "operations", "aftersales", "all"])
    p.add_argument("--strict", action="store_true", help="check 未通过时返回非0")
    p.add_argument("--mode", choices=["once", "daemon"], default="once", help="start 运行模式")
    p.add_argument("--background", action="store_true", help="start 时后台运行（仅 daemon）")
    p.add_argument("--window-minutes", type=int, default=1440, help="status 时 SLA 统计窗口（分钟）")
    p.add_argument("--workflow-db", default=None, help="presales workflow 数据库路径")
    p.add_argument("--orders-db", default="data/orders.db", help="aftersales 订单数据库路径")
    p.add_argument("--limit", type=int, default=20, help="presales 扫描会话数 / aftersales 处理工单数")
    p.add_argument("--claim-limit", type=int, default=10, help="presales 每轮认领任务数")
    p.add_argument("--interval", type=float, default=1.0, help="轮询间隔（秒）")
    p.add_argument("--dry-run", action="store_true", help="presales/aftersales 仅生成回复不发送")
    p.add_argument("--issue-type", default="delay", help="aftersales 售后类型：delay/refund/quality")
    p.add_argument("--include-manual", action="store_true", help="aftersales 包含人工接管订单")
    p.add_argument("--max-loops", type=int, default=None, help="daemon 模式下最多循环次数")
    p.add_argument("--init-default-tasks", action="store_true", help="operations 自动初始化默认任务")
    p.add_argument("--skip-polish", action="store_true", help="operations 跳过擦亮任务")
    p.add_argument("--skip-metrics", action="store_true", help="operations 跳过数据任务")
    p.add_argument("--polish-max-items", type=int, default=50, help="默认擦亮任务最大数量")
    p.add_argument("--polish-cron", default="", help="默认擦亮任务 cron")
    p.add_argument("--metrics-cron", default="", help="默认数据任务 cron")
    p.add_argument("--tail-lines", type=int, default=80, help="logs 返回行数")
    p.add_argument("--stop-timeout", type=float, default=6.0, help="stop/restart 等待进程退出超时（秒）")

    # growth
    p = sub.add_parser("growth", help="增长实验与漏斗")
    p.add_argument(
        "--action",
        required=True,
        choices=["set-strategy", "rollback", "assign", "event", "funnel", "compare"],
    )
    p.add_argument("--db-path", default="data/growth.db", help="增长数据库路径")
    p.add_argument("--strategy-type", default=None, help="策略类型（reply/quote/followup）")
    p.add_argument("--version", default=None, help="策略版本")
    p.add_argument("--active", action="store_true", help="设置为当前生效版本")
    p.add_argument("--baseline", action="store_true", help="标记为基线版本")
    p.add_argument("--experiment-id", default=None, help="实验ID")
    p.add_argument("--subject-id", default=None, help="主体ID（会话/用户）")
    p.add_argument("--variants", default="A,B", help="变体列表，逗号分隔")
    p.add_argument("--variant", default=None, help="事件所属变体")
    p.add_argument("--stage", default=None, help="漏斗阶段")
    p.add_argument("--days", type=int, default=7, help="漏斗窗口天数")
    p.add_argument("--bucket", choices=["day", "week"], default="day", help="聚合粒度")
    p.add_argument("--from-stage", default="inquiry", help="转化起始阶段")
    p.add_argument("--to-stage", default="ordered", help="转化目标阶段")
