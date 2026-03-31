"""轻量后台可视化与模块控制服务。"""

from __future__ import annotations

import logging
import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from src.core.config import get_config
from src.dashboard.module_console import MODULE_TARGETS, ModuleConsole
from src.dashboard.services import (
    CookieService,
    EnvService,
    LogService,
    QuoteService,
    ReplyTestService,
    TemplateService,
    XGJService,
)
from src.dashboard.services.vg_dashboard_service import VirtualGoodsDashboardService

logger = logging.getLogger(__name__)

from src.dashboard.helpers.utils import (  # noqa: E402
    DEFAULT_VOLUME_TEMPLATE,
    DEFAULT_WEIGHT_TEMPLATE,
    _PRODUCT_IMAGE_CACHE_TTL,
    _error_payload,
    _extract_json_payload,
    _now_iso,
    _product_image_cache,
    _run_async,
    _safe_int,
    _test_xgj_connection,
)


class MimicOps:
    """模仿 XianyuAutoAgent 的页面与操作能力。"""

    _ROUTE_FILE_EXTS = {".xlsx", ".xls", ".csv"}
    _MARKUP_FILE_EXTS = {".xlsx", ".xls", ".csv", ".json", ".yaml", ".yml", ".txt", ".md"}
    _MARKUP_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}
    _MARKUP_REQUIRED_FIELDS = ("normal_first_add", "member_first_add", "normal_extra_add", "member_extra_add")
    _MARKUP_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
        "courier": ("运力", "快递", "快递公司", "物流", "渠道", "公司", "courier", "carrier", "name"),
        "normal_first_add": (
            "normal_first_add",
            "普通首重",
            "首重普通",
            "首重溢价普通",
            "首重加价普通",
            "first_normal",
            "normal_first",
        ),
        "member_first_add": (
            "member_first_add",
            "会员首重",
            "首重会员",
            "首重溢价会员",
            "首重加价会员",
            "first_member",
            "member_first",
            "vip_first",
        ),
        "normal_extra_add": (
            "normal_extra_add",
            "普通续重",
            "续重普通",
            "续重溢价普通",
            "续重加价普通",
            "extra_normal",
            "normal_extra",
        ),
        "member_extra_add": (
            "member_extra_add",
            "会员续重",
            "续重会员",
            "续重溢价会员",
            "续重加价会员",
            "extra_member",
            "member_extra",
            "vip_extra",
        ),
    }
    _COOKIE_REQUIRED_KEYS = ("_tb_token_", "cookie2", "sgcookie", "unb")
    _COOKIE_RECOMMENDED_KEYS = ("XSRF-TOKEN", "last_u_xianyu_web", "tfstk", "t", "cna")
    _COOKIE_DOMAIN_ALLOWLIST = ("goofish.com", "passport.goofish.com")
    _COOKIE_IMPORT_EXTS = {".txt", ".json", ".log", ".cookies", ".csv", ".tsv", ".har"}
    _COOKIE_HINT_KEYS = ("_tb_token_", "cookie2", "sgcookie", "unb", "_m_h5_tk", "_m_h5_tk_enc")
    _COOKIE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
    _ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    _LOG_TIME_RE = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})")
    _RISK_BLOCK_PATTERNS = (
        "fail_sys_user_validate",
        "rgv587",
        "账号异常",
        "账号风险",
        "安全验证",
        "访问受限",
        "封控",
        "封禁",
    )
    _RISK_WARN_PATTERNS = (
        "http 400",
        "http 403",
        "forbidden",
        "unauthorized",
        "token api failed",
        "需要验证码",
        "验证码",
        "校验失败",
    )
    _RISK_SIGNAL_WINDOW_MINUTES = 120

    def __init__(self, project_root: str | Path, module_console: ModuleConsole):
        self.project_root = Path(project_root).resolve()
        self.module_console = module_console
        self._service_started_at = _now_iso()
        self._instance_id = f"dashboard-{os.getpid()}-{int(time.time())}"
        self._python_exec = sys.executable
        self._service_state: dict[str, Any] = {
            "suspended": False,
            "stopped": False,
            "updated_at": _now_iso(),
        }
        self._last_cookie_fp = ""
        self._last_token_error: str | None = None
        self._last_auto_recover_cookie_fp = ""
        self._last_auto_recover_at = ""
        self._last_auto_recover_result: dict[str, Any] = {}
        self._last_presales_dead_restart_at: float = 0.0
        self._recover_lock = threading.Lock()
        self._cost_table_repo: Any = None
        self._shared_cookie_checker: Any = None
        self._risk_log_cache: dict[str, Any] | None = None
        self._risk_log_cache_ts: float = 0.0
        # Service instances (extracted)
        self._cookie_service = CookieService(self.project_root)
        self._xgj_service = XGJService(self.project_root)
        self._log_service = LogService(self.project_root)
        self._quote_service = QuoteService(self.project_root)
        self._template_service = TemplateService(self.project_root)
        self._reply_test_service = ReplyTestService(self.project_root)
        self._env_service = EnvService(self.project_root)
        self._vg_dashboard_service = VirtualGoodsDashboardService(
            project_root=self.project_root,
            xgj_config_provider=self._xgj_service._xianguanjia_service_config,
        )

    # ── auto-delegation sets ──────────────────────────────────────────
    _COOKIE_DELEGATE_METHODS: frozenset[str] = frozenset(
        {
            "_cookie_fingerprint",
            "_cookie_pairs_to_text",
            "_extract_cookie_pairs_from_json",
            "_is_allowed_cookie_domain",
            "_extract_cookie_pairs_from_header",
            "_extract_cookie_pairs_from_lines",
            "parse_cookie_text",
            "_recovery_stage_label",
            "_is_cookie_cloud_configured",
            "_recovery_advice",
            "_cookie_domain_filter_stats",
            "diagnose_cookie",
            "_parse_m_h5_tk_ttl",
            "_is_cookie_import_file",
            "_looks_like_cookie_plugin_bundle",
            "_cookie_hint_hit_keys",
            "_score_cookie_candidate",
            "export_cookie_plugin_bundle",
        }
    )

    _XGJ_DELEGATE_METHODS: frozenset[str] = frozenset(
        {
            "get_xianguanjia_settings",
            "save_xianguanjia_settings",
            "retry_xianguanjia_delivery",
            "retry_xianguanjia_price",
            "handle_order_callback",
            "handle_order_push",
            "handle_product_callback",
            "_xianguanjia_service_config",
        }
    )

    _QUOTE_DELEGATE_METHODS: frozenset[str] = frozenset(
        {
            "route_stats",
            "_route_stats_nonblocking",
            "import_route_files",
            "export_routes_zip",
            "get_template",
            "save_template",
            "get_markup_rules",
            "save_markup_rules",
            "get_pricing_config",
            "save_pricing_config",
            "get_cost_summary",
            "query_route_cost",
            "import_markup_files",
            "get_reply_templates",
            "get_replies",
            "config_path",
            "_quote_dir",
            "reset_database",
        }
    )

    _LOG_DELEGATE_METHODS: frozenset[str] = frozenset(
        {
            "list_log_files",
            "read_log_content",
            "_strip_ansi",
            "_extract_log_time",
            "_parse_log_datetime",
            "_risk_control_status_from_logs",
            "_risk_control_status_from_logs_uncached",
            "get_unmatched_message_stats",
            "_query_message_stats_from_workflow",
            "_module_runtime_log",
            "_workflow_db_path",
        }
    )

    _REPLY_TEST_DELEGATE_METHODS: frozenset[str] = frozenset(
        {
            "_get_sandbox_service",
            "test_reply",
        }
    )

    def __getattr__(self, name: str):
        """Auto-delegate to sub-services."""
        if name in self._COOKIE_DELEGATE_METHODS:
            return getattr(self._cookie_service, name)
        if name in self._XGJ_DELEGATE_METHODS:
            return getattr(self._xgj_service, name)
        if name in self._QUOTE_DELEGATE_METHODS:
            return getattr(self._quote_service, name)
        if name in self._LOG_DELEGATE_METHODS:
            return getattr(self._log_service, name)
        if name in self._REPLY_TEST_DELEGATE_METHODS:
            return getattr(self._reply_test_service, name)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    @property
    def env_path(self) -> Path:
        return self._env_service.env_path

    @property
    def logs_dir(self) -> Path:
        return self._env_service.logs_dir

    @property
    def cookie_plugin_dir(self) -> Path:
        return self._env_service.cookie_plugin_dir

    def get_virtual_goods_metrics(self) -> dict[str, Any]:
        return self._vg_dashboard_service.get_virtual_goods_metrics()

    def get_dashboard_readonly_aggregate(self) -> dict[str, Any]:
        return self._vg_dashboard_service.get_dashboard_readonly_aggregate()

    def inspect_virtual_goods_order(self, order_id: str) -> dict[str, Any]:
        return self._vg_dashboard_service.inspect_virtual_goods_order(order_id)

    def get_cookie(self) -> dict[str, Any]:
        return {
            "success": bool(self._env_service._get_env_value("XIANYU_COOKIE_1").strip()),
            "cookie": self._env_service._get_env_value("XIANYU_COOKIE_1").strip(),
            "length": len(self._env_service._get_env_value("XIANYU_COOKIE_1").strip()),
        }

    def _trigger_presales_recover_after_cookie_update(self, cookie_text: str) -> dict[str, Any]:
        cookie_fp = self._cookie_fingerprint(cookie_text)
        if not cookie_fp:
            return {"triggered": False, "message": "cookie_empty"}

        result = self.module_console.control(action="recover", target="presales")
        has_error = bool(result.get("error")) if isinstance(result, dict) else True
        now = _now_iso()
        with self._recover_lock:
            self._last_auto_recover_cookie_fp = cookie_fp
            self._last_auto_recover_at = now
            self._last_auto_recover_result = result if isinstance(result, dict) else {}
            self._last_cookie_fp = cookie_fp
        return {
            "triggered": not has_error,
            "result": result,
            "at": now,
            "message": "recover_ok" if not has_error else "recover_failed",
        }

    def update_cookie(self, cookie: str, *, auto_recover: bool = False) -> dict[str, Any]:
        parsed = self.parse_cookie_text(str(cookie or ""))
        if not parsed.get("success"):
            return parsed
        cookie_text = str(parsed.get("cookie") or "").strip()
        if not cookie_text:
            return {"success": False, "error": "Cookie string cannot be empty"}
        self._env_service._set_env_value("XIANYU_COOKIE_1", cookie_text)
        diagnosis = self.diagnose_cookie(cookie_text)
        payload: dict[str, Any] = {
            "success": True,
            "message": "Cookie updated",
            "length": len(cookie_text),
            "cookie_items": int(parsed.get("cookie_items", 0) or 0),
            "detected_format": str(parsed.get("detected_format") or "header"),
            "missing_required": parsed.get("missing_required", []),
            "cookie_grade": diagnosis.get("grade", "未知"),
            "cookie_actions": diagnosis.get("actions", []),
            "cookie_diagnosis": diagnosis,
        }
        try:
            from src.modules.messages.ws_live import notify_ws_cookie_changed

            notify_ws_cookie_changed()
        except Exception:
            pass

        should_recover = auto_recover and str(diagnosis.get("grade") or "") != "不可用"
        if should_recover:
            recover = self._trigger_presales_recover_after_cookie_update(cookie_text)
            payload["auto_recover"] = recover
            if recover.get("triggered"):
                payload["message"] = "Cookie updated and presales recovery triggered"
            else:
                payload["message"] = "Cookie updated, but presales recovery failed"
        return payload

    def import_cookie_plugin_files(
        self, files: list[tuple[str, bytes]], *, auto_recover: bool = False
    ) -> dict[str, Any]:
        return self._cookie_service.import_cookie_plugin_files(
            files, module_console=self.module_console, auto_recover=auto_recover
        )

    def reset_database(self, db_type: str) -> dict[str, Any]:
        """Reset database files (routes and/or chat workflow)."""
        target = str(db_type or "all").strip().lower()
        result: dict[str, Any] = {"success": True, "results": {}}

        if target in {"routes", "all"}:
            quote_result = self._quote_service.reset_database(db_type=target)
            result["results"]["routes"] = quote_result.get("results", {}).get("routes", {"message": "done"})

        if target in {"chat", "all"}:
            removed: list[str] = []
            for rel in ("data/workflow.db", "data/message_workflow_state.json", "data/messages_followup_state.json"):
                p = self.project_root / rel
                if p.exists():
                    p.unlink()
                    removed.append(rel)
            result["results"]["chat"] = {"message": f"Removed {len(removed)} chat workflow file(s)", "files": removed}

        return result

    def service_status(self) -> dict[str, Any]:
        module_status = self.module_console.status(window_minutes=60, limit=20)
        cookie = self.get_cookie()
        cookie_text = str(cookie.get("cookie", "") or "")
        route_stats = self._route_stats_nonblocking()
        xgj_settings = self.get_xianguanjia_settings()
        risk_control = self._risk_control_status_from_logs(target="presales", tail_lines=300)
        modules = module_status.get("modules") if isinstance(module_status, dict) else {}
        if not isinstance(modules, dict):
            modules = {}

        if self._service_state.get("stopped"):
            service_status = "stopped"
        elif self._service_state.get("suspended"):
            service_status = "suspended"
        else:
            service_status = "running"

        alive_count = int(module_status.get("alive_count", 0)) if isinstance(module_status, dict) else 0
        total_modules = (
            int(module_status.get("total_modules", len(MODULE_TARGETS)))
            if isinstance(module_status, dict)
            else len(MODULE_TARGETS)
        )

        presales_mod = modules.get("presales", {}) if isinstance(modules.get("presales"), dict) else {}
        presales_sla = presales_mod.get("sla", {}) if isinstance(presales_mod.get("sla"), dict) else {}
        presales_process = presales_mod.get("process", {}) if isinstance(presales_mod.get("process"), dict) else {}
        workflow = presales_mod.get("workflow", {}) if isinstance(presales_mod.get("workflow"), dict) else {}
        route_stat_payload = route_stats.get("stats", {}) if isinstance(route_stats, dict) else {}
        route_stats_by_courier = (
            route_stat_payload.get("courier_details", {}) if isinstance(route_stat_payload, dict) else {}
        )
        risk_level = str(risk_control.get("level", "unknown") or "unknown").lower()
        risk_signals_raw = risk_control.get("signals", [])
        risk_signals = (
            [str(x).strip() for x in risk_signals_raw if str(x).strip()] if isinstance(risk_signals_raw, list) else []
        )
        risk_signal_text = " ".join(risk_signals)
        risk_event_text = str(risk_control.get("last_event", "") or "")
        risk_text = f"{risk_signal_text} {risk_event_text}".lower()

        workflow_states = workflow.get("states", {}) if isinstance(workflow.get("states"), dict) else {}
        workflow_jobs = workflow.get("jobs", {}) if isinstance(workflow.get("jobs"), dict) else {}
        fallback_total_replied = int(workflow_states.get("REPLIED", 0) or 0) + int(
            workflow_states.get("QUOTED", 0) or 0
        )
        fallback_total_conversations = sum(int(v or 0) for v in workflow_states.values())
        fallback_total_messages = sum(int(v or 0) for v in workflow_jobs.values())
        message_stats = self._query_message_stats_from_workflow() or {
            "total_replied": fallback_total_replied,
            "today_replied": 0,
            "recent_replied": int(presales_sla.get("event_count", 0) or 0),
            "total_conversations": fallback_total_conversations,
            "today_conversations": 0,
            "total_messages": fallback_total_messages,
            "hourly_replies": {},
            "daily_replies": {},
        }

        token_error: str | None = None
        if risk_level not in ("stale", "normal"):
            if "fail_sys_user_validate" in risk_text:
                token_error = "FAIL_SYS_USER_VALIDATE"
            elif "rgv587" in risk_text or "被挤爆" in risk_text:
                token_error = "RGV587_SERVER_BUSY"
            elif "token api failed" in risk_text:
                token_error = "TOKEN_API_FAILED"
            elif "websocket" in risk_text and "http 400" in risk_text:
                token_error = "WS_HTTP_400"

        cookie_update_required = bool(token_error == "FAIL_SYS_USER_VALIDATE")
        token_available = bool(cookie.get("success", False)) and token_error is None
        xianyu_connected = (
            bool(presales_process.get("alive", False)) and token_error is None and risk_level != "blocked"
        )
        if service_status == "running" and (not xianyu_connected or risk_level in {"warning", "blocked"}):
            service_status = "degraded"
        recovery = self._maybe_auto_recover_presales(
            service_status=service_status,
            token_error=token_error,
            cookie_text=cookie_text,
            presales_alive=bool(presales_process.get("alive", False)),
        )
        recovery_stage = str(recovery.get("stage") or "monitoring").strip().lower() or "monitoring"
        next_retry_at: str | None = None
        if recovery_stage in {"recover_triggered", "waiting_reconnect"}:
            last_auto_recover_at = str(recovery.get("last_auto_recover_at") or "").strip()
            if last_auto_recover_at:
                try:
                    dt = datetime.fromisoformat(last_auto_recover_at.replace("Z", "+00:00"))
                    next_retry_at = (dt + timedelta(seconds=20)).strftime("%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    next_retry_at = None

        user_id = None
        for key, value in self._extract_cookie_pairs_from_header(cookie_text):
            if str(key or "").strip() == "unb":
                user_id = str(value or "").strip() or None
                break

        cookie_health_info: dict[str, Any] = {"healthy": False, "message": "未检查", "score": 0}
        try:
            if cookie_text:
                from src.core.cookie_health import CookieHealthChecker

                if self._shared_cookie_checker is None:
                    self._shared_cookie_checker = CookieHealthChecker(cookie_text, timeout_seconds=5.0)
                else:
                    self._shared_cookie_checker.cookie_text = cookie_text
                ck_result = self._shared_cookie_checker.check_sync(force=False)
                cookie_health_info = {
                    "healthy": bool(ck_result.get("healthy")),
                    "message": ck_result.get("message", ""),
                    "score": 100 if ck_result.get("healthy") else 0,
                }
            else:
                cookie_health_info = {"healthy": False, "message": "Cookie 未配置", "score": 0}
        except Exception:
            pass

        cc_configured = self._is_cookie_cloud_configured()

        return {
            "success": True,
            "service": dict(self._service_state),
            "module": module_status,
            "cookie_exists": bool(cookie.get("success", False)),
            "cookie_valid": bool(cookie.get("success", False)),
            "cookie_length": int(cookie.get("length", 0) or 0),
            "cookie_health": cookie_health_info,
            "xianyu_connected": xianyu_connected,
            "token_available": token_available,
            "token_error": token_error,
            "cookie_update_required": cookie_update_required,
            "cookie_cloud_configured": cc_configured,
            "slider_auto_solve_enabled": bool(
                get_config()
                .get_section("messages", {})
                .get("ws", {})
                .get("slider_auto_solve", {})
                .get("enabled", False)
            ),
            "user_id": user_id,
            "last_token_refresh": risk_control.get("last_event_at") if token_error is None else None,
            "service_start_time": self._service_started_at,
            "instance_id": self._instance_id,
            "project_root": str(self.project_root),
            "python_exec": self._python_exec,
            "started_at": self._service_started_at,
            "route_stats": route_stat_payload,
            "route_stats_by_courier": route_stats_by_courier,
            "message_stats": message_stats,
            "xianguanjia": xgj_settings,
            "risk_control": risk_control,
            "recovery": recovery,
            "recovery_stage": recovery_stage,
            "next_retry_at": next_retry_at,
            "risk_signals": risk_signals,
            "system_running": alive_count > 0,
            "alive_count": alive_count,
            "total_modules": total_modules,
            "service_status": service_status,
        }

    def service_control(self, action: str) -> dict[str, Any]:
        act = str(action or "").strip().lower()
        if act not in {"suspend", "resume", "stop", "start"}:
            return {"success": False, "error": f"Unsupported action: {act}"}

        if act == "suspend":
            stop_result = self.module_console.control(action="stop", target="all")
            self._service_state["suspended"] = True
            self._service_state["stopped"] = False
            self._service_state["updated_at"] = _now_iso()
            return {
                "success": True,
                "action": act,
                "status": "suspended",
                "message": "服务已挂起",
                "result": stop_result,
                "service": dict(self._service_state),
            }

        if act == "stop":
            stop_result = self.module_console.control(action="stop", target="all")
            self._service_state["suspended"] = False
            self._service_state["stopped"] = True
            self._service_state["updated_at"] = _now_iso()
            return {
                "success": True,
                "action": act,
                "status": "stopped",
                "message": "服务已停止",
                "result": stop_result,
                "service": dict(self._service_state),
            }

        start_result = self.module_console.control(action="start", target="all")
        self._service_state["suspended"] = False
        self._service_state["stopped"] = False
        self._service_state["updated_at"] = _now_iso()
        return {
            "success": True,
            "action": act,
            "status": "running",
            "message": "服务已恢复运行" if act == "resume" else "服务已启动",
            "result": start_result,
            "service": dict(self._service_state),
        }

    def service_recover(self, target: str = "presales") -> dict[str, Any]:
        tgt = str(target or "presales").strip().lower()
        if tgt not in MODULE_TARGETS:
            return {"success": False, "error": f"Unsupported target: {tgt}"}

        result = self.module_console.control(action="recover", target=tgt)
        has_error = bool(result.get("error")) if isinstance(result, dict) else True
        status = self.service_status()
        return {
            "success": not has_error,
            "target": tgt,
            "action": "recover",
            "result": result,
            "service_status": status.get("service_status"),
            "xianyu_connected": bool(status.get("xianyu_connected", False)),
            "token_error": status.get("token_error"),
            "cookie_update_required": bool(status.get("cookie_update_required", False)),
            "message": "售前链路恢复完成" if not has_error else f"恢复失败: {result.get('error', 'unknown')}",
        }

    def service_auto_fix(self) -> dict[str, Any]:
        actions: list[str] = []
        status_before = self.service_status()
        svc_state = str(status_before.get("service_status") or "")

        if svc_state == "stopped":
            _ = self.service_control("start")
            actions.append("start_service")
        elif svc_state == "suspended":
            _ = self.service_control("resume")
            actions.append("resume_service")

        if bool(status_before.get("cookie_update_required", False)):
            return {
                "success": False,
                "action": "auto_fix",
                "actions": actions,
                "needs_cookie_update": True,
                "message": "当前为鉴权失效，需先更新 Cookie，系统无法自动修复此项。",
                "status_before": status_before,
                "status_after": self.service_status(),
            }

        recover = self.service_recover("presales")
        actions.append("recover_presales")
        check = self.module_console.check(skip_gateway=True)
        status_after = self.service_status()

        can_work = bool(status_after.get("xianyu_connected", False)) and not bool(
            status_after.get("cookie_update_required", False)
        )
        return {
            "success": bool(can_work),
            "action": "auto_fix",
            "actions": actions,
            "recover": recover,
            "doctor": check,
            "status_before": status_before,
            "status_after": status_after,
            "needs_cookie_update": bool(status_after.get("cookie_update_required", False)),
            "message": "自动修复完成" if can_work else "已执行自动修复，但仍需检查 Cookie 或平台风控状态。",
        }


# Embedded HTML hack removed. UI is strictly served from client/dist now.
