"""
Shared helpers, constants, and utilities used across all CLI commands.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _json_out(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


# ---------------------------------------------------------------------------
# Benchmark messages
# ---------------------------------------------------------------------------


_BENCH_QUOTE_MESSAGES = [
    "安徽到上海 1kg 圆通多少钱",
    "从合肥寄到杭州 2.5kg 申通报价",
    "广州到北京 3kg 运费多少",
    "深圳到成都 0.8kg 韵达价格",
    "南京到西安 4kg 快递费",
    "武汉到重庆 1.2kg 中通多少钱",
]

_BENCH_QUOTE_MISSING_MESSAGES = [
    "寄到上海多少钱",
    "从合肥发快递运费",
    "圆通报价",
    "快递费怎么收",
]

_BENCH_NON_QUOTE_MESSAGES = [
    "宝贝还在吗",
    "可以便宜点吗",
    "什么时候发货",
    "这个是全新的吗",
]


def _pct(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    ordered = sorted(int(v) for v in values)
    idx = round((len(ordered) - 1) * max(0.0, min(1.0, float(ratio))))
    return ordered[idx]


def _pick_bench_message(rng: random.Random, quote_ratio: float, quote_only: bool) -> str:
    if quote_only:
        return rng.choice(_BENCH_QUOTE_MESSAGES)
    if rng.random() <= max(0.0, min(1.0, quote_ratio)):
        pool = _BENCH_QUOTE_MESSAGES if rng.random() > 0.25 else _BENCH_QUOTE_MISSING_MESSAGES
        return rng.choice(pool)
    return rng.choice(_BENCH_NON_QUOTE_MESSAGES)


# ---------------------------------------------------------------------------
# SLA benchmark
# ---------------------------------------------------------------------------


async def _run_messages_sla_benchmark(
    *,
    count: int,
    concurrency: int,
    quote_ratio: float,
    quote_only: bool,
    seed: int,
    slowest: int,
    warmup: int,
) -> dict[str, Any]:
    from src.modules.messages.service import MessagesService

    service = MessagesService(controller=None)
    rng = random.Random(seed)
    sample_count = max(1, int(count))
    max_concurrency = max(1, int(concurrency))
    keep_slowest = max(1, int(slowest))
    warmup_count = max(0, int(warmup))

    async def _run_one(index: int) -> dict[str, Any]:
        msg = _pick_bench_message(rng, quote_ratio=quote_ratio, quote_only=quote_only)
        session = {
            "session_id": f"sla_bench_{index + 1}",
            "peer_name": "bench_user",
            "item_title": "测试商品",
            "last_message": msg,
            "unread_count": 1,
        }
        detail = await service.process_session(session=session, dry_run=True, actor="sla_benchmark")
        detail["sample_message"] = msg
        return detail

    for i in range(warmup_count):
        await _run_one(-(i + 1))

    if max_concurrency == 1:
        details = [await _run_one(i) for i in range(sample_count)]
    else:
        sem = asyncio.Semaphore(max_concurrency)

        async def _guarded(i: int) -> dict[str, Any]:
            async with sem:
                return await _run_one(i)

        details = await asyncio.gather(*(_guarded(i) for i in range(sample_count)))

    latencies_ms = [int(float(item.get("latency_seconds", 0.0)) * 1000) for item in details]
    within_target_count = sum(1 for item in details if bool(item.get("within_target")))
    quote_rows = [item for item in details if bool(item.get("is_quote"))]
    quote_success = sum(1 for item in quote_rows if bool(item.get("quote_success")))
    quote_fallback = sum(1 for item in quote_rows if bool(item.get("quote_fallback")))
    quote_missing = sum(1 for item in quote_rows if bool(item.get("quote_missing_fields")))

    slowest_rows = sorted(details, key=lambda x: float(x.get("latency_seconds", 0.0)), reverse=True)[:keep_slowest]
    slim_slowest = [
        {
            "session_id": row.get("session_id", ""),
            "latency_ms": int(float(row.get("latency_seconds", 0.0)) * 1000),
            "within_target": bool(row.get("within_target")),
            "is_quote": bool(row.get("is_quote")),
            "quote_success": bool(row.get("quote_success")),
            "sample_message": row.get("sample_message", ""),
        }
        for row in slowest_rows
    ]

    quote_total = len(quote_rows)
    return {
        "action": "messages_sla_benchmark",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "config": {
            "count": sample_count,
            "concurrency": max_concurrency,
            "quote_ratio": round(float(quote_ratio), 4),
            "quote_only": bool(quote_only),
            "seed": int(seed),
            "warmup": warmup_count,
            "target_reply_seconds": float(getattr(service, "reply_target_seconds", 3.0)),
        },
        "summary": {
            "samples": sample_count,
            "within_target_count": within_target_count,
            "within_target_rate": round((within_target_count / sample_count) if sample_count else 0.0, 4),
            "latency_p50_ms": _pct(latencies_ms, 0.5),
            "latency_p95_ms": _pct(latencies_ms, 0.95),
            "latency_p99_ms": _pct(latencies_ms, 0.99),
            "latency_max_ms": max(latencies_ms) if latencies_ms else 0,
            "quote_total": quote_total,
            "quote_success_rate": round((quote_success / quote_total) if quote_total else 0.0, 4),
            "quote_fallback_rate": round((quote_fallback / quote_total) if quote_total else 0.0, 4),
            "quote_missing_fields_rate": round((quote_missing / quote_total) if quote_total else 0.0, 4),
        },
        "slowest_samples": slim_slowest,
    }


# ---------------------------------------------------------------------------
# Messages transport
# ---------------------------------------------------------------------------


def _messages_transport_mode() -> str:
    from src.core.config import get_config

    cfg = get_config().get_section("messages", {})
    mode = str(cfg.get("transport", "ws") or "ws").strip().lower()
    if mode not in {"dom", "ws", "auto"}:
        return "dom"
    return mode


def _messages_requires_browser_runtime() -> bool:
    return _messages_transport_mode() in {"dom", "auto"}


# ---------------------------------------------------------------------------
# Module check summary
# ---------------------------------------------------------------------------


_EXPECTED_PROJECT_ROOT = ""  # 无固定预期路径，doctor strict 时 project_root_match 恒为 True


def _module_check_summary(target: str, doctor_report: dict[str, Any]) -> dict[str, Any]:
    # Dynamic lookup so tests patching src.cli._messages_transport_mode always
    # intercept the correct binding at call time.
    from src.cli import _messages_requires_browser_runtime, _messages_transport_mode  # noqa: F401
    from src.core.startup_checks import resolve_runtime_mode

    runtime = resolve_runtime_mode()
    messages_transport = _messages_transport_mode()
    uses_ws_only = messages_transport == "ws" and target in {"presales", "aftersales"}
    checks = doctor_report.get("checks", [])
    check_map = {str(item.get("name", "")): item for item in checks}

    required_names = {"Python版本", "数据库", "配置文件", "闲鱼Cookie", "模块解释器锁定"}
    if target == "presales":
        required_names.add("消息首响SLA")

    required_checks = [check_map[name] for name in required_names if name in check_map]
    blockers = [item for item in required_checks if not bool(item.get("passed", False))]

    lite_item = check_map.get("Lite 浏览器驱动")

    if uses_ws_only:
        pass
    elif runtime == "pro":
        pass
    elif runtime == "lite":
        if lite_item is not None:
            required_checks.append(lite_item)
            if not bool(lite_item.get("passed", False)):
                blockers.append(lite_item)
    else:
        # auto: lite 驱动可用即通过，否则阻塞。
        browser_ready = bool(lite_item and lite_item.get("passed", False))
        if lite_item is not None:
            required_checks.append(lite_item)
        if not browser_ready:
            blockers.append(
                {
                    "name": "浏览器运行时",
                    "passed": False,
                    "critical": True,
                    "message": "auto 模式下 Lite 驱动不可用",
                    "suggestion": ("请执行 ./start.sh 或安装 DrissionPage（pip install DrissionPage）。"),
                    "meta": {"runtime": runtime},
                }
            )

    return {
        "target": target,
        "runtime": runtime,
        "messages_transport": messages_transport,
        "ready": len(blockers) == 0,
        "required_checks": required_checks,
        "blockers": blockers,
        "next_steps": doctor_report.get("next_steps", []),
        "doctor_summary": doctor_report.get("summary", {}),
    }


# ---------------------------------------------------------------------------
# Module runtime state helpers
# ---------------------------------------------------------------------------

_MODULE_TARGETS = ("presales", "operations", "aftersales")
_MODULE_RUNTIME_DIR = Path("data/module_runtime")


def _resolve_python_exec() -> str:
    configured = str(os.getenv("PYTHON_EXEC", "")).strip()
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            candidate = (Path.cwd() / candidate).resolve()
        try:
            if candidate.exists() and candidate.is_file():
                return str(candidate)
        except OSError:
            pass
    # Use abspath for cross-platform compatibility (avoids WindowsPath issue on Linux)
    return os.path.abspath(sys.executable)


def _module_state_path(target: str) -> Path:
    _MODULE_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return _MODULE_RUNTIME_DIR / f"{target}.json"


def _module_log_path(target: str) -> Path:
    _MODULE_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return _MODULE_RUNTIME_DIR / f"{target}.log"


def _read_module_state(target: str) -> dict[str, Any]:
    path = _module_state_path(target)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_module_state(target: str, data: dict[str, Any]) -> None:
    path = _module_state_path(target)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _build_module_start_command(target: str, args: Any) -> list[str]:
    python_exec = _resolve_python_exec()
    cmd = [
        python_exec,
        "-m",
        "src.cli",
        "module",
        "--action",
        "start",
        "--target",
        target,
        "--mode",
        "daemon",
    ]

    if args.max_loops:
        cmd.extend(["--max-loops", str(args.max_loops)])
    if args.interval:
        cmd.extend(["--interval", str(args.interval)])

    if target == "presales":
        cmd.extend(["--limit", str(args.limit), "--claim-limit", str(args.claim_limit)])
        if args.workflow_db:
            cmd.extend(["--workflow-db", str(args.workflow_db)])
        if bool(args.dry_run):
            cmd.append("--dry-run")
    elif target == "operations":
        if bool(args.init_default_tasks):
            cmd.append("--init-default-tasks")
        if bool(args.skip_polish):
            cmd.append("--skip-polish")
        if bool(args.skip_metrics):
            cmd.append("--skip-metrics")
        if args.polish_max_items:
            cmd.extend(["--polish-max-items", str(args.polish_max_items)])
        if args.polish_cron:
            cmd.extend(["--polish-cron", str(args.polish_cron)])
        if args.metrics_cron:
            cmd.extend(["--metrics-cron", str(args.metrics_cron)])
    else:
        cmd.extend(["--limit", str(args.limit), "--issue-type", str(args.issue_type or "delay")])
        if args.orders_db:
            cmd.extend(["--orders-db", str(args.orders_db)])
        if bool(args.include_manual):
            cmd.append("--include-manual")
        if bool(args.dry_run):
            cmd.append("--dry-run")

    return cmd


def _start_background_module(target: str, args: Any) -> dict[str, Any]:
    state = _read_module_state(target)
    old_pid = int(state.get("pid", 0) or 0)
    if old_pid > 0 and _process_alive(old_pid):
        return {
            "target": target,
            "started": False,
            "reason": "already_running",
            "pid": old_pid,
            "log_file": str(_module_log_path(target)),
        }

    cmd = _build_module_start_command(target=target, args=args)
    log_file = _module_log_path(target)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handle = open(log_file, "a", encoding="utf-8")
    python_exec = cmd[0] if cmd else _resolve_python_exec()
    handle.write(
        f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] start target={target} "
        f"python_exec={python_exec} cmd={' '.join(cmd)}\n"
    )
    handle.flush()

    popen_kwargs: dict[str, Any] = {
        "stdout": handle,
        "stderr": handle,
        "cwd": os.getcwd(),
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        popen_kwargs["preexec_fn"] = os.setsid

    proc = subprocess.Popen(cmd, **popen_kwargs)
    handle.close()
    state = {
        "target": target,
        "pid": proc.pid,
        "python_exec": python_exec,
        "log_file": str(log_file),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "command": cmd,
    }
    _write_module_state(target, state)
    return {"target": target, "started": True, "pid": proc.pid, "log_file": str(log_file)}


def _stop_background_module(target: str, timeout_seconds: float = 6.0) -> dict[str, Any]:
    state = _read_module_state(target)
    pid = int(state.get("pid", 0) or 0)
    if pid <= 0:
        return {"target": target, "stopped": False, "reason": "not_running"}
    if not _process_alive(pid):
        return {"target": target, "stopped": False, "reason": "pid_not_alive", "pid": pid}

    try:
        if os.name == "nt":
            os.kill(pid, signal.SIGTERM)
        else:
            os.killpg(pid, signal.SIGTERM)
    except Exception as exc:
        return {"target": target, "stopped": False, "reason": f"signal_failed: {exc}", "pid": pid}

    start = time.time()
    while time.time() - start <= timeout_seconds:
        if not _process_alive(pid):
            return {"target": target, "stopped": True, "pid": pid}
        time.sleep(0.2)

    try:
        if os.name == "nt":
            os.kill(pid, signal.SIGKILL)
        else:
            os.killpg(pid, signal.SIGKILL)
    except Exception:
        pass

    return {"target": target, "stopped": not _process_alive(pid), "pid": pid, "forced": True}


def _module_process_status(target: str) -> dict[str, Any]:
    state = _read_module_state(target)
    pid = int(state.get("pid", 0) or 0)
    alive = _process_alive(pid) if pid > 0 else False
    return {
        "pid": pid if pid > 0 else None,
        "alive": alive,
        "log_file": state.get("log_file", str(_module_log_path(target))),
        "started_at": state.get("started_at", ""),
    }


def _module_logs(target: str, tail_lines: int = 80) -> dict[str, Any]:
    log_file = _module_log_path(target)
    if not log_file.exists():
        return {"target": target, "log_file": str(log_file), "lines": []}

    lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    return {"target": target, "log_file": str(log_file), "lines": lines[-max(int(tail_lines), 1) :]}


def _clear_module_runtime_state(target: str) -> dict[str, Any]:
    """清理模块运行态文件，避免 pid 状态残留导致误判。"""
    removed: list[str] = []
    for suffix in (".json", ".pid", ".lock"):
        fp = _MODULE_RUNTIME_DIR / f"{target}{suffix}"
        try:
            if fp.exists():
                fp.unlink()
                removed.append(str(fp))
        except Exception:
            continue
    return {"target": target, "removed": removed}


def _resolve_workflow_state(stage: str | None) -> Any:
    if not stage:
        return None

    from src.modules.messages.workflow import WorkflowState

    normalized = stage.strip().lower().replace("-", "_")
    aliases = {
        "new": WorkflowState.NEW,
        "replied": WorkflowState.REPLIED,
        "reply": WorkflowState.REPLIED,
        "quoted": WorkflowState.QUOTED,
        "quote": WorkflowState.QUOTED,
        "followed": WorkflowState.FOLLOWED,
        "followup": WorkflowState.FOLLOWED,
        "follow_up": WorkflowState.FOLLOWED,
        "ordered": WorkflowState.ORDERED,
        "order": WorkflowState.ORDERED,
        "closed": WorkflowState.CLOSED,
        "close": WorkflowState.CLOSED,
        "manual": WorkflowState.MANUAL,
        "takeover": WorkflowState.MANUAL,
    }
    return aliases.get(normalized)
