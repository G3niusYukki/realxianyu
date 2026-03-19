"""Cookie management service extracted from MimicOps."""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import re
import time
import zipfile
from pathlib import Path
from typing import Any

from src.core.config import get_config
from src.dashboard.config_service import (
    read_system_config as _read_system_config,
)

logger = logging.getLogger(__name__)

_COOKIE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
_COOKIE_REQUIRED_KEYS = ("_tb_token_", "cookie2", "sgcookie", "unb")
_COOKIE_RECOMMENDED_KEYS = ("XSRF-TOKEN", "last_u_xianyu_web", "tfstk", "t", "cna")
_COOKIE_DOMAIN_ALLOWLIST = ("goofish.com", "passport.goofish.com")
_COOKIE_IMPORT_EXTS = {".txt", ".json", ".log", ".cookies", ".csv", ".tsv", ".har"}
_COOKIE_HINT_KEYS = ("_tb_token_", "cookie2", "sgcookie", "unb", "_m_h5_tk", "_m_h5_tk_enc")


class CookieService:
    """Service for cookie parsing, validation, import/export and diagnosis."""

    _COOKIE_NAME_RE = _COOKIE_NAME_RE
    _COOKIE_REQUIRED_KEYS = _COOKIE_REQUIRED_KEYS
    _COOKIE_RECOMMENDED_KEYS = _COOKIE_RECOMMENDED_KEYS
    _COOKIE_DOMAIN_ALLOWLIST = _COOKIE_DOMAIN_ALLOWLIST
    _COOKIE_IMPORT_EXTS = _COOKIE_IMPORT_EXTS
    _COOKIE_HINT_KEYS = _COOKIE_HINT_KEYS

    def __init__(self, project_root: Path):
        self.project_root = project_root

    @property
    def cookie_plugin_dir(self) -> Path:
        return self.project_root / "third_party" / "Get-cookies.txt-LOCALLY"

    # ------------------------------------------------------------------
    # Static / class-level helpers (pure logic, no self needed)
    # ------------------------------------------------------------------

    @staticmethod
    def _cookie_fingerprint(cookie_text: str) -> str:
        raw = str(cookie_text or "").strip()
        if not raw:
            return ""
        return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]

    @classmethod
    def _cookie_pairs_to_text(cls, pairs: list[tuple[str, str]]) -> tuple[str, int]:
        items: list[str] = []
        seen: set[str] = set()
        for name, value in pairs:
            key = str(name or "").strip()
            val = str(value or "").strip()
            if not key or not val:
                continue
            if not cls._COOKIE_NAME_RE.fullmatch(key):
                continue
            if key in seen:
                continue
            seen.add(key)
            items.append(f"{key}={val}")
        return "; ".join(items), len(items)

    @classmethod
    def _extract_cookie_pairs_from_json(cls, raw_text: str) -> list[tuple[str, str]]:
        text = str(raw_text or "").strip()
        if not text:
            return []
        try:
            payload = json.loads(text)
        except Exception:
            return []

        pairs: list[tuple[str, str]] = []

        def _collect(items: Any) -> None:
            if not isinstance(items, list):
                return
            for item in items:
                if not isinstance(item, dict):
                    continue
                name = item.get("name") or item.get("key")
                value = item.get("value")
                if name is None or value is None:
                    continue
                pairs.append((str(name), str(value)))

        if isinstance(payload, list):
            _collect(payload)
        elif isinstance(payload, dict):
            if "name" in payload and "value" in payload:
                pairs.append((str(payload.get("name")), str(payload.get("value"))))
            _collect(payload.get("cookies"))
            _collect(payload.get("items"))

        return pairs

    @classmethod
    def _is_allowed_cookie_domain(cls, domain: str) -> bool:
        value = str(domain or "").strip().lower().lstrip(".")
        if not value:
            return True
        return any(value.endswith(allowed) for allowed in cls._COOKIE_DOMAIN_ALLOWLIST)

    @classmethod
    def _extract_cookie_pairs_from_header(cls, raw_text: str) -> list[tuple[str, str]]:
        text = str(raw_text or "").replace("\ufeff", "").replace("\x00", "").strip()
        if not text:
            return []
        text = re.sub(r"^\s*cookie\s*:\s*", "", text, flags=re.IGNORECASE)
        parts = re.split(r";|\n", text)
        pairs: list[tuple[str, str]] = []
        for part in parts:
            seg = str(part or "").strip()
            if not seg or "=" not in seg:
                continue
            key, value = seg.split("=", 1)
            pairs.append((key.strip(), value.strip()))
        return pairs

    @classmethod
    def _extract_cookie_pairs_from_lines(cls, raw_text: str) -> list[tuple[str, str]]:
        text = str(raw_text or "").replace("\ufeff", "").replace("\x00", "")
        pairs: list[tuple[str, str]] = []
        for line in text.splitlines():
            s = str(line or "").strip()
            if not s or s.startswith("#"):
                continue

            # Netscape cookies.txt: domain, flag, path, secure, expiry, name, value
            if "\t" in s:
                cols = [c.strip() for c in s.split("\t") if c.strip()]
                if len(cols) >= 7:
                    if cls._is_allowed_cookie_domain(cols[0]):
                        pairs.append((cols[5], cols[6]))
                    continue
                if len(cols) >= 2 and cls._COOKIE_NAME_RE.fullmatch(cols[0]):
                    # DevTools table format: name value domain ...
                    if len(cols) >= 3 and not cls._is_allowed_cookie_domain(cols[2]):
                        continue
                    pairs.append((cols[0], cols[1]))
                    continue

            cols = [c.strip() for c in s.split() if c.strip()]
            if len(cols) >= 2 and cls._COOKIE_NAME_RE.fullmatch(cols[0]):
                pairs.append((cols[0], cols[1]))
                continue

            if "=" in s:
                key, value = s.split("=", 1)
                pairs.append((key.strip(), value.strip()))
        return pairs

    @classmethod
    def parse_cookie_text(cls, text: str) -> dict[str, Any]:
        raw = str(text or "").strip()
        if not raw:
            return {"success": False, "error": "Cookie string cannot be empty"}

        candidates: list[dict[str, Any]] = []
        for source, extractor in (
            ("json", cls._extract_cookie_pairs_from_json),
            ("header", cls._extract_cookie_pairs_from_header),
            ("table_or_netscape", cls._extract_cookie_pairs_from_lines),
        ):
            cookie_text, count = cls._cookie_pairs_to_text(extractor(raw))
            if count > 0 and cookie_text:
                candidates.append({"format": source, "cookie": cookie_text, "count": count})

        if not candidates:
            return {
                "success": False,
                "error": "Unable to parse cookie text. Please use header/json/cookies.txt format.",
            }

        candidates.sort(key=lambda x: (int(x.get("count", 0)), x.get("format") == "header"), reverse=True)
        best = candidates[0]
        cookie_text = str(best["cookie"])
        count = int(best["count"])
        missing_required = [k for k in cls._COOKIE_REQUIRED_KEYS if f"{k}=" not in cookie_text]
        return {
            "success": True,
            "cookie": cookie_text,
            "length": len(cookie_text),
            "cookie_items": count,
            "detected_format": str(best["format"]),
            "missing_required": missing_required,
        }

    @classmethod
    def _parse_m_h5_tk_ttl(cls, raw: str) -> float | None:
        """Parse _m_h5_tk value ({hex}_{epoch_ms}) and return seconds until expiry."""
        parts = str(raw or "").split("_")
        if len(parts) < 2:
            return None
        try:
            expire_ms = int(parts[1])
            return (expire_ms / 1000.0) - time.time()
        except (ValueError, OverflowError):
            return None

    @classmethod
    def _is_cookie_import_file(cls, filename: str) -> bool:
        suffix = Path(filename).suffix.lower()
        if suffix in cls._COOKIE_IMPORT_EXTS:
            return True
        return suffix == "" and bool(Path(filename).name)

    @classmethod
    def _looks_like_cookie_plugin_bundle(cls, member_names: list[str]) -> bool:
        names = [
            str(name or "").replace("\\", "/").strip().lower()
            for name in member_names
            if str(name or "").strip()
        ]
        if not names:
            return False

        if any("get-cookies.txt-locally/src/manifest.json" in item for item in names):
            return True

        basenames = {Path(item).name for item in names}
        has_manifest = "manifest.json" in basenames
        has_popup = "popup.mjs" in basenames or "popup.js" in basenames
        has_background = "background.mjs" in basenames or "background.js" in basenames
        if has_manifest and (has_popup or has_background):
            return True

        plugin_markers = (
            "get-cookies.txt-locally",
            "cookie_format.mjs",
            "get_all_cookies.mjs",
            "save_to_file.mjs",
            "popup-options.css",
        )
        if has_manifest and any(any(marker in item for marker in plugin_markers) for item in names):
            return True
        return False

    @classmethod
    def _cookie_hint_hit_keys(cls, cookie_text: str) -> list[str]:
        text = str(cookie_text or "")
        hits = [k for k in cls._COOKIE_HINT_KEYS if f"{k}=" in text]
        return hits

    @classmethod
    def _score_cookie_candidate(cls, payload: dict[str, Any]) -> tuple[int, int, int]:
        missing = payload.get("missing_required")
        missing_count = len(missing) if isinstance(missing, list) else len(cls._COOKIE_REQUIRED_KEYS)
        required_hit = max(0, len(cls._COOKIE_REQUIRED_KEYS) - missing_count)
        cookie_items = int(payload.get("cookie_items", 0) or 0)
        length = int(payload.get("length", 0) or 0)
        return required_hit, cookie_items, length

    @classmethod
    def _cookie_domain_filter_stats(cls, raw_text: str) -> dict[str, Any]:
        text = str(raw_text or "").replace("\ufeff", "").replace("\x00", "")
        checked = 0
        rejected = 0
        samples: list[str] = []

        def _check_domain(domain: str) -> None:
            nonlocal checked, rejected
            dom = str(domain or "").strip().lower()
            if not dom:
                return
            checked += 1
            if not cls._is_allowed_cookie_domain(dom):
                rejected += 1
                if len(samples) < 5:
                    samples.append(dom)

        for line in text.splitlines():
            s = str(line or "").strip()
            if not s or s.startswith("#"):
                continue
            if "\t" not in s:
                continue
            cols = [c.strip() for c in s.split("\t") if c.strip()]
            if len(cols) >= 7:
                _check_domain(cols[0])
            elif len(cols) >= 3:
                _check_domain(cols[2])

        try:
            payload = json.loads(text)
        except Exception:
            payload = None
        if payload is not None:
            queue: list[Any] = [payload]
            while queue:
                item = queue.pop()
                if isinstance(item, dict):
                    if "domain" in item:
                        _check_domain(str(item.get("domain") or ""))
                    for v in item.values():
                        if isinstance(v, (dict, list)):
                            queue.append(v)
                elif isinstance(item, list):
                    queue.extend(item)

        return {
            "allowlist": list(cls._COOKIE_DOMAIN_ALLOWLIST),
            "checked": checked,
            "rejected": rejected,
            "applied": True,
            "rejected_samples": samples,
        }

    # ------------------------------------------------------------------
    # File / zip helpers (used by import_cookie_plugin_files)
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_text_bytes(content: bytes) -> str:
        for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
            try:
                return content.decode(enc)
            except Exception:
                pass
        return content.decode("utf-8", errors="replace")

    @staticmethod
    def _repair_zip_name(name: str) -> str:
        name = name.replace("\\", "/")
        segments = name.split("/")
        return "/".join(seg for seg in segments if seg and seg != ".DS_Store")

    # ------------------------------------------------------------------
    # Instance methods (require project_root / self operations)
    # ------------------------------------------------------------------

    @classmethod
    def _recovery_stage_label(cls, stage: str) -> str:
        mapping = {
            "healthy": "链路正常",
            "token_error": "鉴权异常",
            "waiting_cookie_update": "等待更新 Cookie",
            "waiting_reconnect": "等待重连",
            "recover_triggered": "已触发自动恢复",
            "inactive": "服务未运行",
            "monitoring": "监控中",
        }
        key = str(stage or "").strip().lower()
        return mapping.get(key, "状态未知")

    @classmethod
    def _is_cookie_cloud_configured(cls) -> bool:
        sys_cfg = _read_system_config()
        cc_cfg = sys_cfg.get("cookie_cloud", {}) if isinstance(sys_cfg.get("cookie_cloud"), dict) else {}
        return bool(cc_cfg.get("cookie_cloud_uuid") and cc_cfg.get("cookie_cloud_password"))

    @classmethod
    def _recovery_advice(cls, stage: str, token_error: str | None = None) -> str:
        s = str(stage or "").strip().lower()
        t = str(token_error or "").strip().upper()
        cc = cls._is_cookie_cloud_configured()
        slider_cfg = get_config().get_section("messages", {}).get("ws", {}).get("slider_auto_solve", {})
        slider_auto = bool(slider_cfg.get("enabled", False)) if isinstance(slider_cfg, dict) else False
        if s == "recover_triggered":
            return "已触发售前恢复，建议等待 5-20 秒后刷新状态。"
        if s == "waiting_reconnect":
            return "Cookie 已更新但尚未连通，可点击\u201c售前一键恢复\u201d立即重试。"
        if s == "waiting_cookie_update":
            if t == "FAIL_SYS_USER_VALIDATE":
                if cc:
                    return "请在闲鱼网页重新登录，CookieCloud 会自动同步新 Cookie，系统将秒级自动恢复。"
                return "请在闲鱼网页重新登录后导出最新 Cookie，再执行\u201c售前一键恢复\u201d。"
            if t in ("RGV587", "RGV587_SERVER_BUSY"):
                if slider_auto:
                    return (
                        "触发平台风控（RGV587），系统正在自动尝试滑块验证...\n"
                        "如自动验证失败，会弹出浏览器窗口，请手动完成滑块拖动。\n"
                        + (
                            "CookieCloud 即时同步已启用，验证后秒级恢复。"
                            if cc
                            else "验证后请手动复制 Cookie 粘贴保存。"
                        )
                    )
                if cc:
                    return (
                        "触发平台风控（RGV587），请按以下步骤操作：\n"
                        "1. 在浏览器打开 goofish.com/im（闲鱼消息页）\n"
                        "2. 完成滑块验证\n"
                        "3. 在 CookieCloud 扩展中点「手动同步」立即生效\n"
                        "系统将秒级自动恢复（CookieCloud 即时同步已启用）。\n"
                        "提示：在「系统设置 → 集成服务」中开启自动滑块验证可实现全自动恢复。"
                    )
                return (
                    "触发平台风控（RGV587），请按以下步骤操作：\n"
                    "1. 在浏览器打开 goofish.com/im（闲鱼消息页）\n"
                    "2. 完成滑块验证\n"
                    "3. 按 F12 → Network → 复制任意请求的 Cookie\n"
                    "4. 粘贴到本页面的「手动粘贴 Cookie」区域并保存\n"
                    "5. 点击\u201c售前一键恢复\u201d\n"
                    "提示：配置 CookieCloud 可实现滑块验证后秒级自动恢复，无需手动复制。"
                )
            if cc:
                return "请更新 Cookie 后等待 CookieCloud 自动同步，系统将秒级自动恢复。"
            return "请更新 Cookie 后重试恢复。"
        if s == "token_error":
            if t == "WS_HTTP_400":
                return "连接通道异常，请先点\u201c售前一键恢复\u201d；若持续失败再更新 Cookie。"
            if t in ("RGV587", "RGV587_SERVER_BUSY"):
                if slider_auto:
                    return "触发平台风控，系统正在自动尝试滑块验证。" + (
                        " CookieCloud 即时同步已启用，验证后秒级恢复。" if cc else ""
                    )
                if cc:
                    return (
                        "触发平台风控，请在浏览器打开 goofish.com/im 完成滑块验证，"
                        "在 CookieCloud 扩展中点「手动同步」，系统将秒级自动恢复。"
                    )
                return (
                    "触发平台风控，请在闲鱼网页版打开「消息」页面通过滑块验证后，"
                    "手动复制 Cookie 并粘贴保存（F12 \u2192 Network \u2192 Cookie），然后执行\u201c售前一键恢复\u201d。\n"
                    "提示：配置 CookieCloud 可实现验证后秒级自动恢复。"
                )
            return "存在鉴权错误，建议更新 Cookie 后重连。"
        if s == "inactive":
            return "服务未运行，请先在首页启动服务。"
        if s == "healthy":
            return "当前链路可用，可正常自动回复。"
        return "监控中，请刷新状态查看最新结果。"

    @classmethod
    def diagnose_cookie(cls, cookie_text: str) -> dict[str, Any]:
        raw = str(cookie_text or "").strip()
        if not raw:
            return {
                "success": False,
                "grade": "不可用",
                "error": "Cookie text is empty",
                "actions": ["请先粘贴 Cookie 文本，或上传插件导出的 cookies 文件。"],
            }

        parsed = cls.parse_cookie_text(raw)
        domain_filter = cls._cookie_domain_filter_stats(raw)
        if not parsed.get("success"):
            return {
                "success": False,
                "grade": "不可用",
                "error": str(parsed.get("error") or "解析失败"),
                "domain_filter": domain_filter,
                "actions": [
                    "请使用 headers/json/cookies.txt 任一格式重试。",
                    "建议在登录闲鱼后立即导出 Cookie，再上传。",
                ],
            }

        normalized = str(parsed.get("cookie") or "")
        cookie_map = {k: v for k, v in cls._extract_cookie_pairs_from_header(normalized)}
        required_all = [*list(cls._COOKIE_REQUIRED_KEYS), "_m_h5_tk", "_m_h5_tk_enc"]
        required_present = [k for k in required_all if k in cookie_map]
        required_missing = [k for k in required_all if k not in cookie_map]
        recommended_present = [k for k in cls._COOKIE_RECOMMENDED_KEYS if k in cookie_map]
        recommended_missing = [k for k in cls._COOKIE_RECOMMENDED_KEYS if k not in cookie_map]
        critical_missing = [k for k in cls._COOKIE_REQUIRED_KEYS if k in required_missing]
        session_missing = [k for k in ("_m_h5_tk", "_m_h5_tk_enc") if k in required_missing]

        length = int(parsed.get("length", 0) or 0)
        cookie_items = int(parsed.get("cookie_items", 0) or 0)
        m_h5_tk_ttl = cls._parse_m_h5_tk_ttl(cookie_map.get("_m_h5_tk", ""))
        m_h5_tk_expired = m_h5_tk_ttl is not None and m_h5_tk_ttl <= 0
        m_h5_tk_expiring_soon = m_h5_tk_ttl is not None and 0 < m_h5_tk_ttl < 900

        grade = "可用"
        if critical_missing or cookie_items < 4:
            grade = "不可用"
        elif m_h5_tk_expired:
            grade = "不可用"
        elif session_missing or length < 80:
            grade = "高风险"
        elif m_h5_tk_expiring_soon:
            grade = "高风险"
        elif len(recommended_missing) >= 2:
            grade = "高风险"

        actions: list[str] = []
        if critical_missing:
            actions.append(f"缺少关键字段：{', '.join(critical_missing)}，请重新登录后导出完整 Cookie。")
        if m_h5_tk_expired:
            actions.append("_m_h5_tk 已过期，请在闲鱼网页版刷新页面后重新导出 Cookie。")
        elif m_h5_tk_expiring_soon:
            ttl_min = int((m_h5_tk_ttl or 0) / 60)
            actions.append(f"_m_h5_tk 将在 {ttl_min} 分钟内过期，建议尽快刷新页面重新导出 Cookie。")
        if session_missing:
            actions.append("缺少 _m_h5_tk/_m_h5_tk_enc，建议刷新页面后重新导出。")
        if domain_filter.get("rejected", 0):
            actions.append("检测到非 goofish 域 Cookie，系统已自动过滤。")
        if recommended_missing:
            actions.append(
                "缺少会话增强字段："
                + ", ".join(recommended_missing)
                + "；建议在插件中使用 Export All Cookies（全量导出）后重试。"
            )
        if grade == "可用":
            actions.append("可直接保存并在首页执行\u201c售前一键恢复\u201d。")

        result: dict[str, Any] = {
            "success": True,
            "grade": grade,
            "detected_format": str(parsed.get("detected_format") or "unknown"),
            "length": length,
            "cookie_items": cookie_items,
            "required_present": required_present,
            "required_missing": required_missing,
            "recommended_present": recommended_present,
            "recommended_missing": recommended_missing,
            "domain_filter": domain_filter,
            "actions": actions,
        }
        if m_h5_tk_ttl is not None:
            result["m_h5_tk_ttl_seconds"] = round(m_h5_tk_ttl)
        return result

    def import_cookie_plugin_files(
        self, files: list[tuple[str, bytes]], *, module_console: Any = None, auto_recover: bool = False
    ) -> dict[str, Any]:
        if not files:
            return {"success": False, "error": "No files uploaded"}

        candidates: list[dict[str, Any]] = []
        imported_files: list[str] = []
        skipped_files: list[str] = []
        details: list[str] = []
        plugin_bundle_detected = False

        def _collect_text_candidate(source_name: str, raw: bytes) -> None:
            text = self._decode_text_bytes(raw)
            parsed = CookieService.parse_cookie_text(text)
            if not parsed.get("success"):
                skipped_files.append(source_name)
                details.append(f"{source_name} -> {parsed.get('error', 'parse failed')}")
                return
            hit_keys = CookieService._cookie_hint_hit_keys(str(parsed.get("cookie") or ""))
            if not hit_keys:
                skipped_files.append(source_name)
                details.append(f"{source_name} -> parsed but missing known keys ({', '.join(self._COOKIE_HINT_KEYS)})")
                return

            candidates.append(
                {
                    "source_file": source_name,
                    "parsed": parsed,
                    "hit_keys": hit_keys,
                }
            )
            imported_files.append(source_name)

        for filename, content in files:
            file_name = str(filename or "").strip()
            suffix = Path(file_name).suffix.lower()

            if suffix == ".zip":
                try:
                    with zipfile.ZipFile(io.BytesIO(content), mode="r") as zf:
                        member_names = [str(info.filename or "") for info in zf.infolist()]
                        if CookieService._looks_like_cookie_plugin_bundle(member_names):
                            plugin_bundle_detected = True
                        for info in zf.infolist():
                            if info.is_dir():
                                continue
                            repaired_name = self._repair_zip_name(info.filename)
                            member_name = Path(repaired_name).name
                            if not member_name:
                                continue
                            if "__MACOSX" in repaired_name or member_name.startswith("._"):
                                skipped_files.append(f"{file_name}:{repaired_name}")
                                continue
                            if not CookieService._is_cookie_import_file(member_name):
                                skipped_files.append(f"{file_name}:{repaired_name}")
                                continue
                            try:
                                raw = zf.read(info)
                                if not raw:
                                    skipped_files.append(f"{file_name}:{repaired_name}")
                                    details.append(f"{file_name}:{repaired_name} -> empty file")
                                    continue
                                _collect_text_candidate(f"{file_name}:{member_name}", raw)
                            except Exception as exc:
                                skipped_files.append(f"{file_name}:{repaired_name}")
                                details.append(f"{file_name}:{repaired_name} -> {exc}")
                except zipfile.BadZipFile:
                    skipped_files.append(file_name)
                    details.append(f"{file_name} -> invalid zip file")
                except Exception as exc:
                    skipped_files.append(file_name)
                    details.append(f"{file_name} -> {exc}")
                continue

            if not CookieService._is_cookie_import_file(file_name):
                skipped_files.append(file_name)
                continue
            _collect_text_candidate(file_name, content)

        if not candidates:
            if plugin_bundle_detected:
                return {
                    "success": False,
                    "error": "Detected plugin installation bundle, not exported cookies.",
                    "hint": "请先在浏览器安装插件并导出 cookies.txt/JSON，再上传导出文件。",
                    "imported_files": imported_files,
                    "skipped_files": skipped_files,
                    "details": details,
                }
            return {
                "success": False,
                "error": "No valid cookie content found in uploaded files.",
                "imported_files": imported_files,
                "skipped_files": skipped_files,
                "details": details,
            }

        best = max(candidates, key=lambda item: CookieService._score_cookie_candidate(item["parsed"]))
        parsed = dict(best.get("parsed", {}))
        cookie_text = str(parsed.get("cookie") or "").strip()
        if not cookie_text:
            return {
                "success": False,
                "error": "Parsed cookie is empty.",
                "imported_files": imported_files,
                "skipped_files": skipped_files,
                "details": details,
            }

        self._set_env_value("XIANYU_COOKIE_1", cookie_text)
        try:
            from src.modules.messages.ws_live import notify_ws_cookie_changed

            notify_ws_cookie_changed()
        except Exception:
            pass
        diagnosis = CookieService.diagnose_cookie(cookie_text)
        payload: dict[str, Any] = {
            "success": True,
            "message": "Cookie imported from plugin export",
            "source_file": str(best.get("source_file") or ""),
            "cookie": cookie_text,
            "length": int(parsed.get("length", 0) or 0),
            "cookie_items": int(parsed.get("cookie_items", 0) or 0),
            "detected_format": str(parsed.get("detected_format") or "unknown"),
            "missing_required": parsed.get("missing_required", []),
            "imported_files": imported_files,
            "skipped_files": skipped_files,
            "details": details,
            "cookie_grade": diagnosis.get("grade", "未知"),
            "cookie_actions": diagnosis.get("actions", []),
            "cookie_diagnosis": diagnosis,
            "recognized_key_hits": best.get("hit_keys", []),
        }
        should_recover = auto_recover and module_console is not None and str(diagnosis.get("grade") or "") != "不可用"
        if should_recover:
            recover = CookieService._trigger_presales_recover_after_cookie_update(cookie_text, module_console)
            payload["auto_recover"] = recover
            if recover.get("triggered"):
                payload["message"] = "Cookie imported and presales recovery triggered"
            else:
                payload["message"] = "Cookie imported, but presales recovery failed"
        return payload

    def _set_env_value(self, key: str, value: str) -> None:
        """Write a key=value line to .env file (used by import_cookie_plugin_files)."""
        env_path = self.project_root / ".env"
        key_norm = f"{key}="
        lines = []
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        updated = False
        for idx, line in enumerate(lines):
            if line.startswith(key_norm):
                lines[idx] = f"{key}={value}"
                updated = True
                break
        if not updated:
            lines.append(f"{key}={value}")
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        os.environ[key] = value

    @staticmethod
    def _trigger_presales_recover_after_cookie_update(
        cookie_text: str, module_console: Any
    ) -> dict[str, Any]:
        """Trigger presales recovery after cookie update (calls module_console externally)."""
        from src.dashboard.mimic_ops import _now_iso

        cookie_fp = CookieService._cookie_fingerprint(cookie_text)
        if not cookie_fp:
            return {"triggered": False, "message": "cookie_empty"}

        result = module_console.control(action="recover", target="presales")
        has_error = bool(result.get("error")) if isinstance(result, dict) else True
        now = _now_iso()
        return {
            "triggered": not has_error,
            "result": result,
            "at": now,
            "message": "recover_ok" if not has_error else "recover_failed",
        }

    def export_cookie_plugin_bundle(self) -> tuple[bytes, str]:
        base = self.cookie_plugin_dir
        src_dir = base / "src"
        if not base.exists() or not src_dir.exists():
            raise FileNotFoundError("Bundled plugin source not found under third_party/Get-cookies.txt-LOCALLY")

        include_paths = [
            "src",
            "LICENSE",
            "README.upstream.md",
            "privacy-policy.upstream.md",
            "SOURCE_INFO.txt",
        ]

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for rel in include_paths:
                target = base / rel
                if not target.exists():
                    continue
                if target.is_file():
                    zf.write(target, arcname=f"Get-cookies.txt-LOCALLY/{rel}")
                    continue
                for fp in target.rglob("*"):
                    if not fp.is_file():
                        continue
                    arc = f"Get-cookies.txt-LOCALLY/{fp.relative_to(base).as_posix()}"
                    zf.write(fp, arcname=arc)

        filename = "Get-cookies.txt-LOCALLY_bundle.zip"
        return buf.getvalue(), filename
