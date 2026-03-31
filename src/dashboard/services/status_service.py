"""Service status, control, recover, and auto-fix logic."""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.core.config import get_config
from src.dashboard.helpers.utils import _now_iso
from src.dashboard.module_console import MODULE_TARGETS, ModuleConsole
from src.dashboard.services.cookie_service import CookieService
from src.dashboard.services.env_service import EnvService
from src.dashboard.services.log_service import LogService
from src.dashboard.services.quote_service import QuoteService
from src.dashboard.services.xgj_service import XGJService

logger = logging.getLogger(__name__)


class StatusService:
    """Handles service status aggregation, control, recover, and auto-fix."""

    def __init__(
        self,
        project_root: Path,
        module_console: ModuleConsole,
        cookie_service: CookieService,
        quote_service: QuoteService,
        log_service: LogService,
        xgj_service: XGJService,
        env_service: EnvService,
    ) -> None:
        self.project_root = project_root
        self.module_console = module_console
        self._cookie_service = cookie_service
        self._quote_service = quote_service
        self._log_service = log_service
        self._xgj_service = xgj_service
        self._env_service = env_service
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
        self._shared_cookie_checker: Any = None

    def _get_cookie(self) -> dict[str, Any]:
        return {
            "success": bool(self._env_service._get_env_value("XIANYU_COOKIE_1").strip()),
            "cookie": self._env_service._get_env_value("XIANYU_COOKIE_1").strip(),
            "length": len(self._env_service._get_env_value("XIANYU_COOKIE_1").strip()),
        }

    def _maybe_auto_recover_presales(
        self,
        *,
        service_status: str,
        token_error: str | None,
        cookie_text: str,
        presales_alive: bool,
    ) -> dict[str, Any]:
        if not cookie_text:
            return {"stage": "no_cookie"}
        if service_status in ("running",) and not token_error and presales_alive:
            return {"stage": "monitoring", "last_auto_recover_at": self._last_auto_recover_at}
        if token_error in ("FAIL_SYS_USER_VALIDATE", "TOKEN_API_FAILED"):
            return {"stage": "cookie_expired", "last_auto_recover_at": self._last_auto_recover_at}
        if service_status in ("degraded",) and cookie_text:
            now = _now_iso()
            result = self.module_console.control(action="recover", target="presales")
            has_error = bool(result.get("error")) if isinstance(result, dict) else True
            with self._recover_lock:
                self._last_auto_recover_at = now
                self._last_auto_recover_result = result if isinstance(result, dict) else {}
            return {
                "stage": "recover_triggered" if not has_error else "recover_failed",
                "last_auto_recover_at": now,
                "result": result,
            }
        return {"stage": "monitoring", "last_auto_recover_at": self._last_auto_recover_at}

    def service_status(self) -> dict[str, Any]:
        module_status = self.module_console.status(window_minutes=60, limit=20)
        cookie = self._get_cookie()
        cookie_text = str(cookie.get("cookie", "") or "")
        route_stats = self._quote_service._route_stats_nonblocking()
        xgj_settings = self._xgj_service.get_xianguanjia_settings()
        risk_control = self._log_service._risk_control_status_from_logs(target="presales", tail_lines=300)
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
        message_stats = self._log_service._query_message_stats_from_workflow() or {
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
        for key, value in self._cookie_service._extract_cookie_pairs_from_header(cookie_text):
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

        cc_configured = self._cookie_service._is_cookie_cloud_configured()

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
