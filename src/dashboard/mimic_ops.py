"""轻量后台可视化与模块控制服务。"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from src.dashboard.module_console import ModuleConsole
from src.dashboard.services import (
    CookieService,
    EnvService,
    LogService,
    QuoteService,
    ReplyTestService,
    StatusService,
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
        self._cost_table_repo: Any = None
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
        self._status_service = StatusService(
            project_root=self.project_root,
            module_console=self.module_console,
            cookie_service=self._cookie_service,
            quote_service=self._quote_service,
            log_service=self._log_service,
            xgj_service=self._xgj_service,
            env_service=self._env_service,
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
        with self._status_service._recover_lock:
            self._status_service._last_auto_recover_cookie_fp = cookie_fp
            self._status_service._last_auto_recover_at = now
            self._status_service._last_auto_recover_result = result if isinstance(result, dict) else {}
            self._status_service._last_cookie_fp = cookie_fp
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
        return self._status_service.service_status()

    def service_control(self, action: str) -> dict[str, Any]:
        return self._status_service.service_control(action)

    def service_recover(self, target: str = "presales") -> dict[str, Any]:
        return self._status_service.service_recover(target)

    def service_auto_fix(self) -> dict[str, Any]:
        return self._status_service.service_auto_fix()

    @property
    def _service_started_at(self) -> str:
        return self._status_service._service_started_at


# Embedded HTML hack removed. UI is strictly served from client/dist now.
