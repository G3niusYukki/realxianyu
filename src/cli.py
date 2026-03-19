"""
Compatibility shim: re-export everything from the new src.cli package so that
``from src.cli import ...`` and ``python -m src.cli`` continue to work unchanged.

The canonical location for CLI code is now ``src/cli/``.
"""

# Re-export the public API from the package.
from src.cli import (
    # base helpers
    _clear_module_runtime_state,
    _json_out,
    _messages_requires_browser_runtime,
    _messages_transport_mode,
    _module_check_summary,
    _module_logs,
    _module_process_status,
    _pct,
    _pick_bench_message,
    _resolve_workflow_state,
    _run_messages_sla_benchmark,
    _start_background_module,
    _stop_background_module,
    # top-level
    build_parser,
    # commands
    cmd_accounts,
    cmd_ai,
    cmd_analytics,
    cmd_automation,
    cmd_compliance,
    cmd_delist,
    cmd_doctor,
    cmd_growth,
    cmd_messages,
    cmd_module,
    cmd_orders,
    cmd_polish,
    cmd_price,
    cmd_publish,
    cmd_quote,
    cmd_relist,
    cmd_virtual_goods,
    main,
)

__all__ = [
    # base helpers
    "_clear_module_runtime_state",
    "_json_out",
    "_messages_requires_browser_runtime",
    "_messages_transport_mode",
    "_module_check_summary",
    "_module_logs",
    "_module_process_status",
    "_pct",
    "_pick_bench_message",
    "_resolve_workflow_state",
    "_run_messages_sla_benchmark",
    "_start_background_module",
    "_stop_background_module",
    # top-level
    "build_parser",
    # commands
    "cmd_accounts",
    "cmd_ai",
    "cmd_analytics",
    "cmd_automation",
    "cmd_compliance",
    "cmd_delist",
    "cmd_doctor",
    "cmd_growth",
    "cmd_messages",
    "cmd_module",
    "cmd_orders",
    "cmd_polish",
    "cmd_price",
    "cmd_publish",
    "cmd_quote",
    "cmd_relist",
    "cmd_virtual_goods",
    "main",
]
