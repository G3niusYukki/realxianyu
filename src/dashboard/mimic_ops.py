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
        self._env_service = EnvService(self.project_root)
        self._cookie_service = CookieService(self.project_root, env_service=self._env_service)
        self._xgj_service = XGJService(self.project_root)
        self._log_service = LogService(self.project_root)
        self._quote_service = QuoteService(self.project_root)
        self._template_service = TemplateService(self.project_root)
        self._reply_test_service = ReplyTestService(self.project_root)
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

    # ── cookie service forwarding ─────────────────────────────
    def parse_cookie_text(self, text: str) -> dict[str, Any]:
        return self._cookie_service.parse_cookie_text(text)

    def diagnose_cookie(self, cookie_text: str) -> dict[str, Any]:
        return self._cookie_service.diagnose_cookie(cookie_text)

    def export_cookie_plugin_bundle(self) -> tuple[bytes, str]:
        return self._cookie_service.export_cookie_plugin_bundle()

    def _cookie_fingerprint(self, text: str) -> str:
        return self._cookie_service._cookie_fingerprint(text)

    def _extract_cookie_pairs_from_header(self, text: str) -> list[tuple[str, str]]:
        return self._cookie_service._extract_cookie_pairs_from_header(text)

    def _cookie_domain_filter_stats(self, text: str) -> dict[str, Any]:
        return self._cookie_service._cookie_domain_filter_stats(text)

    def _is_cookie_cloud_configured(self) -> bool:
        return self._cookie_service._is_cookie_cloud_configured()

    # ── xgj service forwarding ───────────────────────────────
    def get_xianguanjia_settings(self) -> dict[str, Any]:
        return self._xgj_service.get_xianguanjia_settings()

    def save_xianguanjia_settings(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._xgj_service.save_xianguanjia_settings(data)

    def retry_xianguanjia_delivery(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._xgj_service.retry_xianguanjia_delivery(data)

    def retry_xianguanjia_price(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._xgj_service.retry_xianguanjia_price(data)

    def handle_order_callback(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._xgj_service.handle_order_callback(data)

    def handle_order_push(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._xgj_service.handle_order_push(data)

    def handle_product_callback(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._xgj_service.handle_product_callback(data)

    def _xianguanjia_service_config(self) -> dict[str, Any]:
        return self._xgj_service._xianguanjia_service_config()

    def _resolve_session_id_for_order(self, order_id: str) -> str | None:
        return self._xgj_service._resolve_session_id_for_order(order_id)

    # ── quote service forwarding ───────────────────────────────
    def route_stats(self) -> dict[str, Any]:
        return self._quote_service.route_stats()

    def export_routes_zip(self) -> tuple[bytes, str]:
        return self._quote_service.export_routes_zip()

    def get_template(self, default: bool = False) -> dict[str, Any]:
        return self._quote_service.get_template(default=default)

    def get_markup_rules(self) -> dict[str, Any]:
        return self._quote_service.get_markup_rules()

    def import_route_files(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        return self._quote_service.import_route_files(files)

    def import_markup_files(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        return self._quote_service.import_markup_files(files)

    def save_template(self, name: str, content: str) -> dict[str, Any]:
        return self._quote_service.save_template(name, content)

    def save_markup_rules(self, markup_rules: Any) -> dict[str, Any]:
        return self._quote_service.save_markup_rules(markup_rules)

    def get_pricing_config(self) -> dict[str, Any]:
        return self._quote_service.get_pricing_config()

    def save_pricing_config(self, config: dict[str, Any]) -> dict[str, Any]:
        return self._quote_service.save_pricing_config(config)

    def get_cost_summary(self) -> dict[str, Any]:
        return self._quote_service.get_cost_summary()

    def query_route_cost(self, origin: str, destination: str) -> dict[str, Any]:
        return self._quote_service.query_route_cost(origin, destination)

    # ── log service forwarding ───────────────────────────────
    def list_log_files(self) -> list[str]:
        return self._log_service.list_log_files()

    def read_log_content(self, file_name: str | None = None, tail: int | None = None) -> dict[str, Any]:
        return self._log_service.read_log_content(file_name=file_name, tail=tail)

    def get_unmatched_message_stats(self, max_lines: int = 3000, top_n: int = 10) -> dict[str, Any]:
        return self._log_service.get_unmatched_message_stats(max_lines=max_lines, top_n=top_n)

    # ── reply test / template forwarding ─────────────────────
    def test_reply(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._reply_test_service.test_reply(body)

    def get_reply_templates(self) -> dict[str, Any]:
        return self._template_service.get_reply_templates()

    def get_replies(self) -> dict[str, Any]:
        return self._template_service.get_replies()

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
        return self._cookie_service.update_cookie(
            cookie,
            auto_recover=auto_recover,
            recover_callback=self._trigger_presales_recover_after_cookie_update if auto_recover else None,
        )

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
