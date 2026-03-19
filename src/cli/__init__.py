"""
闲鱼自动化工具 CLI 包

重新导出所有公开 API，确保现有的 ``from src.cli import ...`` 用法无需修改即可继续工作。
"""

from .base import (
    _clear_module_runtime_state,
    _json_out,
    _messages_requires_browser_runtime,
    _messages_transport_mode,
    _module_check_summary,
    _module_logs,
    _module_process_status,
    _pick_bench_message,
    _pct,
    _resolve_workflow_state,
    _run_messages_sla_benchmark,
    _start_background_module,
    _stop_background_module,
)
from .cmd_main import (
    cmd_accounts,
    cmd_analytics,
    cmd_delist,
    cmd_messages,
    cmd_polish,
    cmd_price,
    cmd_publish,
    cmd_relist,
)
from .cmd_module import (
    cmd_ai,
    cmd_automation,
    cmd_compliance,
    cmd_doctor,
    cmd_growth,
    cmd_module,
)
from .cmd_orders import (
    cmd_orders,
    cmd_virtual_goods,
)
from .cmd_quote import cmd_quote
from .main import build_parser, main
