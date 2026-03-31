"""Dashboard quote service — route tables, markup rules, pricing config, cost tables."""

from __future__ import annotations

import io
import json
import logging
import re
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from src.core.config import get_config
from src.modules.quote.cost_table import CostTableRepository, normalize_courier_name
from src.modules.quote.setup import DEFAULT_MARKUP_RULES, QuoteSetupService

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    from src.dashboard.mimic_ops import _now_iso
    return _now_iso()


class QuoteService:
    """Handles quote-related dashboard operations: routes, markup rules, pricing, cost tables."""

    _ROUTE_FILE_EXTS = {".xlsx", ".xls", ".csv"}
    _MARKUP_FILE_EXTS = {".xlsx", ".xls", ".csv", ".json", ".yaml", ".yml", ".txt", ".md"}
    _MARKUP_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}
    _MARKUP_REQUIRED_FIELDS = ("normal_first_add", "member_first_add", "normal_extra_add", "member_extra_add")
    _MARKUP_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
        "courier": ("运力", "快递", "快递公司", "物流", "渠道", "公司", "courier", "carrier", "name"),
        "normal_first_add": (
            "normal_first_add", "普通首重", "首重普通", "首重溢价普通", "首重加价普通", "first_normal", "normal_first",
        ),
        "member_first_add": (
            "member_first_add", "会员首重", "首重会员", "首重溢价会员", "首重加价会员",
            "first_member", "member_first", "vip_first",
        ),
        "normal_extra_add": (
            "normal_extra_add", "普通续重", "续重普通", "续重溢价普通", "续重加价普通", "extra_normal", "normal_extra",
        ),
        "member_extra_add": (
            "member_extra_add", "会员续重", "续重会员", "续重溢价会员", "续重加价会员",
            "extra_member", "member_extra", "vip_extra",
        ),
    }

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._cost_table_repo: Any = None

        # route_stats cache
        self._route_stats_cache: dict[str, Any] | None = None
        self._route_stats_mtime: float = 0.0
        self._route_stats_ts: float = 0.0
        self._ROUTE_STATS_TTL: float = 120.0
        self._route_stats_lock = threading.Lock()

    # ── properties ──────────────────────────────────────────────────

    @property
    def config_path(self) -> Path:
        return self.project_root / "config" / "config.yaml"

    @property
    def _MARKUP_FILE_EXTS(self) -> set[str]:
        return self._MARKUP_FILE_EXTS

    # ── quote dir ──────────────────────────────────────────────────

    def _quote_dir(self) -> Path:
        cfg = get_config().get_section("quote", {})
        table_dir = str(cfg.get("cost_table_dir", "data/quote_costs"))
        path = Path(table_dir)
        if not path.is_absolute():
            path = self.project_root / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ── route stats ────────────────────────────────────────────────

    def route_stats(self) -> dict[str, Any]:
        now = time.time()
        if self._route_stats_cache is not None and (now - self._route_stats_ts) < self._ROUTE_STATS_TTL:
            return self._route_stats_cache

        if not self._route_stats_lock.acquire(blocking=True, timeout=30):
            if self._route_stats_cache is not None:
                return self._route_stats_cache
            return {"success": True, "stats": {}}

        try:
            if self._route_stats_cache is not None and (time.time() - self._route_stats_ts) < self._ROUTE_STATS_TTL:
                return self._route_stats_cache

            cfg = get_config().get_section("quote", {})
            patterns = cfg.get("cost_table_patterns", ["*.xlsx", "*.xls", "*.csv"])
            if not isinstance(patterns, list):
                patterns = ["*.xlsx", "*.xls", "*.csv"]
            for required in ("*.xlsx", "*.xls", "*.csv"):
                if required not in patterns:
                    patterns.append(required)
            quote_dir = self._quote_dir()
            files = []
            latest_mtime = 0.0
            for pattern in patterns:
                for fp in quote_dir.glob(str(pattern)):
                    if fp.is_file():
                        files.append(fp)
                        latest_mtime = max(latest_mtime, fp.stat().st_mtime)

            route_count = 0
            courier_set: set[str] = set()
            courier_details: dict[str, int] = {}
            parse_errors: list[str] = []

            try:
                repo = CostTableRepository(table_dir=quote_dir)
                repo._reload_if_needed()
                records = repo._records
                route_count += len(records)
                for rec in records:
                    courier = str(getattr(rec, "courier", "") or "").strip()
                    if not courier:
                        continue
                    courier_set.add(courier)
                    courier_details[courier] = int(courier_details.get(courier, 0) or 0) + 1
            except Exception as exc:
                parse_errors.append(f"quote_costs: {exc}")

            last_updated = "-"
            if latest_mtime > 0:
                last_updated = datetime.fromtimestamp(latest_mtime).strftime("%Y-%m-%d %H:%M:%S")

            stats = {
                "couriers": len(courier_set),
                "routes": int(route_count),
                "tables": len(set(files)),
                "last_updated": last_updated,
                "courier_details": dict(sorted(courier_details.items(), key=lambda x: x[0])),
                "files": [str(p.name) for p in sorted(set(files))[:200]],
            }
            if parse_errors:
                stats["parse_error"] = " | ".join(parse_errors[:5])
            result = {"success": True, "stats": stats}
            self._route_stats_cache = result
            self._route_stats_mtime = latest_mtime
            self._route_stats_ts = time.time()
            return result
        finally:
            self._route_stats_lock.release()

    def _route_stats_nonblocking(self) -> dict[str, Any]:
        """Return cached route_stats if available; never block on cold Excel parsing."""
        if self._route_stats_cache is not None:
            return self._route_stats_cache
        return {"success": True, "stats": {}}

    # ── file name / zip helpers ────────────────────────────────────

    @staticmethod
    def _safe_filename(name: str) -> str:
        base_name = Path(str(name or "")).name
        ext = Path(base_name).suffix.lower()
        stem_raw = Path(base_name).stem
        stem = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fa5]+", "_", stem_raw).strip("_-")
        if not stem:
            stem = f"upload_{int(time.time())}"
        if ext not in QuoteService._ROUTE_FILE_EXTS:
            ext = ".xlsx"
        return f"{stem}{ext}"

    @staticmethod
    def _repair_zip_name(name: str) -> str:
        raw = str(name or "")
        if not raw:
            return raw
        try:
            return raw.encode("cp437").decode("utf-8")
        except Exception:
            pass
        for enc in ("gbk", "gb18030", "big5"):
            try:
                return raw.encode("cp437").decode(enc)
            except Exception:
                continue
        return raw

    @classmethod
    def _is_route_table_file(cls, filename: str) -> bool:
        return Path(filename).suffix.lower() in cls._ROUTE_FILE_EXTS

    def _save_route_content(self, quote_dir: Path, filename: str, content: bytes) -> str:
        base_name = Path(filename).name
        clean = self._safe_filename(base_name)
        if not self._is_route_table_file(clean):
            raise ValueError(f"Unsupported file type: {base_name}")

        target = quote_dir / clean
        if target.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            candidate = quote_dir / f"{target.stem}_{ts}{target.suffix}"
            idx = 1
            while candidate.exists():
                idx += 1
                candidate = quote_dir / f"{target.stem}_{ts}_{idx}{target.suffix}"
            target = candidate
        target.write_bytes(content)
        return target.name

    # ── route import / export ──────────────────────────────────────

    def import_route_files(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        if not files:
            return {"success": False, "error": "No files uploaded"}
        quote_dir = self._quote_dir()
        saved: list[str] = []
        skipped: list[str] = []
        errors: list[str] = []
        zip_count = 0
        for filename, content in files:
            file_name = str(filename or "").strip()
            suffix = Path(file_name).suffix.lower()

            if suffix == ".zip":
                zip_count += 1
                try:
                    with zipfile.ZipFile(io.BytesIO(content), mode="r") as zf:
                        for info in zf.infolist():
                            if info.is_dir():
                                continue
                            repaired_name = self._repair_zip_name(info.filename)
                            member_name = Path(repaired_name).name
                            if not member_name:
                                continue
                            if "__MACOSX" in repaired_name or member_name.startswith("._"):
                                skipped.append(repaired_name)
                                continue
                            if not self._is_route_table_file(member_name):
                                skipped.append(repaired_name)
                                continue
                            try:
                                data = zf.read(info)
                                saved_name = self._save_route_content(quote_dir, member_name, data)
                                saved.append(saved_name)
                            except Exception as exc:
                                skipped.append(repaired_name)
                                errors.append(f"{file_name}:{repaired_name} -> {exc}")
                except zipfile.BadZipFile:
                    skipped.append(file_name)
                    errors.append(f"{file_name} -> invalid zip file")
                except Exception as exc:
                    skipped.append(file_name)
                    errors.append(f"{file_name} -> {exc}")
                continue

            if self._is_route_table_file(file_name):
                try:
                    saved_name = self._save_route_content(quote_dir, file_name, content)
                    saved.append(saved_name)
                except Exception as exc:
                    skipped.append(file_name)
                    errors.append(f"{file_name} -> {exc}")
            else:
                skipped.append(file_name)

        if not saved:
            return {
                "success": False,
                "error": "No supported route files found. Use .xlsx/.xls/.csv or a .zip containing them.",
                "skipped_files": skipped,
                "details": errors,
            }

        stats = self.route_stats().get("stats", {})
        self._cost_table_repo = None
        message = f"Imported {len(saved)} file(s)"
        if zip_count > 0:
            message += f" from {zip_count} zip archive(s)"
        return {
            "success": True,
            "message": message,
            "saved_files": saved,
            "skipped_files": skipped,
            "details": errors,
            "stats": stats,
        }

    def export_routes_zip(self) -> tuple[bytes, str]:
        quote_dir = self._quote_dir()
        files = sorted([*quote_dir.glob("*.xlsx"), *quote_dir.glob("*.xls"), *quote_dir.glob("*.csv")])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for fp in files:
                zf.write(fp, arcname=fp.name)
        filename = f"routes_export_{datetime.now().strftime('%Y%m%d')}.zip"
        return buf.getvalue(), filename

    # ── markup helpers ─────────────────────────────────────────────

    @staticmethod
    def _decode_text_bytes(content: bytes) -> str:
        data = bytes(content or b"")
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="ignore")

    @staticmethod
    def _markup_float(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        text = text.replace("，", ",").replace(",", "")
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    @staticmethod
    def _clean_markup_token(value: Any) -> str:
        text = str(value or "").strip().lower()
        if not text:
            return ""
        text = text.replace("（", "(").replace("）", ")")
        text = re.sub(r"[\s_\-:|/\\,，;；。'\"]+", "", text)
        return text

    @classmethod
    def _normalize_markup_courier(cls, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        if "默认" in raw or re.search(r"\bdefault\b", raw, flags=re.IGNORECASE):
            return "default"

        normalized = normalize_courier_name(raw)
        if normalized in DEFAULT_MARKUP_RULES:
            return normalized

        for key in DEFAULT_MARKUP_RULES:
            if cls._clean_markup_token(key) == cls._clean_markup_token(raw):
                return key

        return raw

    @classmethod
    def _match_markup_header(cls, header: str, field: str) -> bool:
        h = cls._clean_markup_token(header)
        for alias in cls._MARKUP_FIELD_ALIASES.get(field, ()):
            if cls._clean_markup_token(alias) == h:
                return True
        return False

    @classmethod
    def _resolve_markup_header_map(cls, rows: list[list[Any]]) -> tuple[dict[str, int], int]:
        header_map: dict[str, int] = {}
        data_start = 0
        for idx, row in enumerate(rows):
            if not row:
                continue
            row_texts = [str(cell or "").strip() for cell in row]
            if any(cls._clean_markup_token(cell) for cell in row_texts):
                courier_col = -1
                field_col: dict[str, int] = {}
                for col_idx, cell_text in enumerate(row_texts):
                    ct = cls._clean_markup_token(cell_text)
                    if not ct:
                        continue
                    if courier_col == -1:
                        courier_col = col_idx
                        continue
                    for field_key, aliases in cls._MARKUP_FIELD_ALIASES.items():
                        if ct in {cls._clean_markup_token(a) for a in aliases}:
                            field_col[field_key] = col_idx
                            break
                if courier_col >= 0 and field_col:
                    header_map = field_col
                    header_map["_courier"] = courier_col
                    data_start = idx + 1
                    break
            data_start = idx + 1

        return header_map, data_start

    @staticmethod
    def _build_markup_rule(courier: str, row: list[Any], header_map: dict[str, int]) -> dict[str, float] | None:
        if not courier:
            return None
        rule: dict[str, float] = {}
        for field in QuoteService._MARKUP_REQUIRED_FIELDS:
            col = header_map.get(field)
            if col is None or col >= len(row):
                return None
            val = QuoteService._markup_float(row[col])
            if val is None:
                return None
            rule[field] = val
        return rule

    @staticmethod
    def _coerce_markup_row(value: Any) -> dict[str, float] | None:
        if isinstance(value, dict):
            rule: dict[str, float] = {}
            for field in QuoteService._MARKUP_REQUIRED_FIELDS:
                v = value.get(field)
                fv = QuoteService._markup_float(v)
                if fv is None:
                    return None
                rule[field] = fv
            return rule
        return None

    @classmethod
    def _parse_markup_rules_from_mapping(cls, mapping: Any) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        if not isinstance(mapping, dict):
            return result
        for courier, raw in mapping.items():
            rule = cls._coerce_markup_row(raw)
            if rule:
                result[cls._normalize_markup_courier(courier)] = rule
        return result

    @staticmethod
    def _split_text_rows(text: str) -> list[list[str]]:
        rows: list[list[str]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            cells = re.split(r"[\t,;，；]", line)
            rows.append([c.strip() for c in cells])
        return rows

    @classmethod
    def _parse_markup_rules_from_rows(cls, rows: list[list[Any]]) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        header_map, data_start = cls._resolve_markup_header_map(rows)
        if not header_map or "_courier" not in header_map:
            return result

        for row in rows[data_start:]:
            if not row or len(row) <= header_map["_courier"]:
                continue
            courier_raw = str(row[header_map["_courier"]] or "").strip()
            if not courier_raw:
                continue
            courier = cls._normalize_markup_courier(courier_raw)
            rule = cls._build_markup_rule(courier, row, header_map)
            if rule:
                result[courier] = rule
        return result

    @classmethod
    def _parse_markup_rules_from_text(cls, text: str) -> dict[str, dict[str, float]]:
        rows = cls._split_text_rows(text)
        return cls._parse_markup_rules_from_rows(rows)

    @classmethod
    def _parse_markup_rules_from_json_like(cls, payload: Any) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        if isinstance(payload, dict):
            return cls._parse_markup_rules_from_mapping(payload)
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    courier = str(item.get("courier") or item.get("name") or "").strip()
                    rule = cls._coerce_markup_row(item)
                    if courier and rule:
                        result[cls._normalize_markup_courier(courier)] = rule
        return result

    @staticmethod
    def _extract_text_from_image(content: bytes) -> str:
        try:
            img = Image.open(io.BytesIO(content))
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")
            import pytesseract  # type: ignore
            return pytesseract.image_to_string(img, lang="chi_sim+eng").strip()
        except Exception:
            return ""

    @classmethod
    def _parse_markup_rules_from_xlsx_bytes(cls, content: bytes) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        try:
            import openpyxl  # type: ignore
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            for sheet in wb.worksheets:
                rows: list[list[Any]] = []
                for row in sheet.iter_rows(values_only=True):
                    rows.append([cell for cell in row])
                parsed = cls._parse_markup_rules_from_rows(rows)
                for k, v in parsed.items():
                    if k not in result:
                        result[k] = v
        except Exception:
            pass
        return result

    @classmethod
    def _infer_markup_rules_from_route_table(cls, filename: str, content: bytes) -> dict[str, dict[str, float]]:
        suffix = Path(filename).suffix.lower()
        if suffix in {".xlsx", ".xls"}:
            return cls._parse_markup_rules_from_xlsx_bytes(content)
        return {}

    @classmethod
    def _parse_markup_rules_from_file(cls, filename: str, content: bytes) -> tuple[dict[str, dict[str, float]], str]:
        suffix = Path(filename).suffix.lower()

        if suffix in cls._MARKUP_IMAGE_EXTS:
            text = cls._extract_text_from_image(content)
            if text:
                return cls._parse_markup_rules_from_text(text), "ocr"
            return {}, ""

        if suffix == ".xlsx":
            parsed = cls._parse_markup_rules_from_xlsx_bytes(content)
            if parsed:
                return parsed, "xlsx"

        text = cls._decode_text_bytes(content)

        if suffix == ".json":
            try:
                parsed = json.loads(text)
                return cls._parse_markup_rules_from_mapping(parsed), "json"
            except Exception:
                pass

        if suffix in {".yaml", ".yml"}:
            try:
                parsed = yaml.safe_load(text)
                if isinstance(parsed, dict):
                    return cls._parse_markup_rules_from_mapping(parsed), "yaml"
            except Exception:
                pass

        return cls._parse_markup_rules_from_text(text), "text"

    # ── markup import ───────────────────────────────────────────────

    def import_markup_files(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        imported_files: list[str] = []
        skipped_files: list[str] = []
        details: list[str] = []
        formats: dict[str, int] = {}
        parsed_rules: dict[str, dict[str, float]] = {}

        def _collect_one(name: str, data: bytes, source_prefix: str = "") -> None:
            source = f"{source_prefix}:{name}" if source_prefix else name
            try:
                rules, fmt = self._parse_markup_rules_from_file(name, data)
                formats[fmt] = formats.get(fmt, 0) + 1
                if rules:
                    for courier, rule in rules.items():
                        if courier not in parsed_rules:
                            parsed_rules[courier] = rule
                    imported_files.append(name)
                else:
                    skipped_files.append(name)
                    details.append(f"{source}: no valid rules found")
            except Exception as exc:
                skipped_files.append(name)
                details.append(f"{source}: {exc}")

        for zip_member_name, content in files:
            suffix = Path(zip_member_name).suffix.lower()
            if suffix == ".zip":
                try:
                    with zipfile.ZipFile(io.BytesIO(content), mode="r") as zf:
                        for info in zf.infolist():
                            if info.is_dir() or "__MACOSX" in info.filename or info.filename.startswith("._"):
                                continue
                            repaired = self._repair_zip_name(info.filename)
                            try:
                                member_data = zf.read(info)
                            except Exception as exc:
                                skipped_files.append(repaired)
                                details.append(f"zip:{repaired}: {exc}")
                                continue
                            _collect_one(repaired, member_data, "zip")
                except zipfile.BadZipFile:
                    skipped_files.append(zip_member_name)
                    details.append(f"{zip_member_name}: invalid zip")
                except Exception as exc:
                    skipped_files.append(zip_member_name)
                    details.append(f"{zip_member_name}: {exc}")
            else:
                _collect_one(zip_member_name, content)

        if not imported_files:
            return {
                "success": False,
                "error": "No valid markup rules found in uploaded files.",
                "skipped_files": skipped_files,
                "details": details,
            }

        normalized = self._normalize_markup_rules(parsed_rules)
        saved = self.save_markup_rules(normalized)
        return {
            **saved,
            "imported_files": imported_files,
            "skipped_files": skipped_files,
            "details": details,
            "detected_formats": dict(sorted(formats.items(), key=lambda item: item[0])),
            "imported_couriers": [k for k in sorted(parsed_rules.keys()) if k != "default"],
        }

    # ── markup rules CRUD ─────────────────────────────────────────

    @staticmethod
    def _to_non_negative_float(value: Any, default: float = 0.0) -> float:
        try:
            val = float(value)
            if val < 0:
                return 0.0
            return round(val, 4)
        except (TypeError, ValueError):
            return float(default)

    def _normalize_markup_rules(self, rules: Any) -> dict[str, dict[str, float]]:
        base_default = dict(DEFAULT_MARKUP_RULES.get("default", {}))
        if not isinstance(rules, dict):
            return {"default": base_default}

        normalized: dict[str, dict[str, float]] = {}
        for key, raw in rules.items():
            courier = str(key or "").strip()
            if not courier:
                continue
            payload = raw if isinstance(raw, dict) else {}
            normalized[courier] = {
                "normal_first_add": self._to_non_negative_float(
                    payload.get("normal_first_add"), base_default.get("normal_first_add", 0.5)
                ),
                "member_first_add": self._to_non_negative_float(
                    payload.get("member_first_add"), base_default.get("member_first_add", 0.25)
                ),
                "normal_extra_add": self._to_non_negative_float(
                    payload.get("normal_extra_add"), base_default.get("normal_extra_add", 0.5)
                ),
                "member_extra_add": self._to_non_negative_float(
                    payload.get("member_extra_add"), base_default.get("member_extra_add", 0.3)
                ),
            }

        if "default" not in normalized:
            normalized["default"] = base_default

        ordered: dict[str, dict[str, float]] = {"default": normalized.pop("default")}
        for key in sorted(normalized.keys()):
            ordered[key] = normalized[key]
        return ordered

    def get_markup_rules(self) -> dict[str, Any]:
        setup = QuoteSetupService(config_path=str(self.config_path))
        data, _ = setup._load_yaml()
        quote_cfg = data.get("quote", {}) if isinstance(data, dict) else {}
        rules = quote_cfg.get("markup_rules", {}) if isinstance(quote_cfg, dict) else {}
        normalized = self._normalize_markup_rules(rules if rules else DEFAULT_MARKUP_RULES)
        return {
            "success": True,
            "markup_rules": normalized,
            "couriers": [k for k in normalized.keys() if k != "default"],
            "updated_at": _now_iso(),
        }

    def save_markup_rules(self, rules: Any) -> dict[str, Any]:
        normalized = self._normalize_markup_rules(rules)
        if not normalized:
            return {"success": False, "error": "No valid markup rules"}

        setup = QuoteSetupService(config_path=str(self.config_path))
        data, existed = setup._load_yaml()
        quote_cfg = data.get("quote")
        if not isinstance(quote_cfg, dict):
            quote_cfg = {}
            data["quote"] = quote_cfg
        quote_cfg["markup_rules"] = normalized

        backup_path = setup._backup_existing_file() if existed else None
        setup._write_yaml(data)
        try:
            get_config().reload(str(self.config_path))
        except Exception:
            pass

        return {
            "success": True,
            "message": "Markup rules saved",
            "backup_path": str(backup_path) if backup_path else "",
            "markup_rules": normalized,
        }

    # ── pricing config CRUD ────────────────────────────────────────

    def get_pricing_config(self) -> dict[str, Any]:
        """读取 YAML 中的 markup_categories、xianyu_discount、抛比和大件运力优先级。"""
        setup = QuoteSetupService(config_path=str(self.config_path))
        data, _ = setup._load_yaml()
        quote_cfg = data.get("quote", {}) if isinstance(data, dict) else {}
        return {
            "success": True,
            "markup_categories": quote_cfg.get("markup_categories", {}),
            "xianyu_discount": quote_cfg.get("xianyu_discount", {}),
            "volume_divisor_default": quote_cfg.get("volume_divisor_default", 8000),
            "volume_divisors": quote_cfg.get("volume_divisors", {}),
            "freight_courier_priority": quote_cfg.get("freight_courier_priority", []),
            "service_categories": [
                "线上快递",
                "线下快递",
                "线上快运",
                "线下快运",
                "同城寄",
                "电动车",
                "分销",
                "商家寄件",
            ],
            "updated_at": _now_iso(),
        }

    def save_pricing_config(
        self,
        markup_categories: Any = None,
        xianyu_discount: Any = None,
        volume_divisor_default: Any = None,
        volume_divisors: Any = None,
        freight_courier_priority: Any = None,
    ) -> dict[str, Any]:
        """保存加价表、让利表、抛比和大件运力优先级到 YAML。"""
        setup = QuoteSetupService(config_path=str(self.config_path))
        data, existed = setup._load_yaml()
        quote_cfg = data.get("quote")
        if not isinstance(quote_cfg, dict):
            quote_cfg = {}
            data["quote"] = quote_cfg

        if isinstance(markup_categories, dict):
            quote_cfg["markup_categories"] = markup_categories
        if isinstance(xianyu_discount, dict):
            quote_cfg["xianyu_discount"] = xianyu_discount
        if volume_divisor_default is not None:
            try:
                val = float(volume_divisor_default)
                if val > 0:
                    quote_cfg["volume_divisor_default"] = val
            except (TypeError, ValueError):
                pass
        if isinstance(volume_divisors, dict):
            normalized: dict[str, Any] = {}
            for cat, courier_cfg in volume_divisors.items():
                if not isinstance(courier_cfg, dict):
                    continue
                inner: dict[str, float] = {}
                for k, v in courier_cfg.items():
                    try:
                        fv = float(v)
                        if fv > 0:
                            inner[str(k).strip()] = fv
                    except (TypeError, ValueError):
                        pass
                if inner:
                    normalized[str(cat).strip()] = inner
            quote_cfg["volume_divisors"] = normalized
        if isinstance(freight_courier_priority, list):
            quote_cfg["freight_courier_priority"] = [str(c).strip() for c in freight_courier_priority if str(c).strip()]

        setup._backup_existing_file() if existed else None
        setup._write_yaml(data)
        # Bridge: also persist to system_config.json
        try:
            sys_path = self.project_root / "data" / "system_config.json"
            sys_data: dict[str, Any] = {}
            if sys_path.exists():
                try:
                    sys_data = json.loads(sys_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
            sys_data["quote"] = dict(quote_cfg)
            from src.dashboard.config_service import write_system_config as _write_sys
            _write_sys(sys_data)
        except Exception:
            pass
        try:
            get_config().reload(str(self.config_path))
        except Exception:
            pass
        # Hot-reload the live MessagesService quote engine
        try:
            from src.modules.messages.service import _active_service
            if _active_service is not None:
                _active_service.reload_quote_engine()
        except Exception:
            pass

        return {"success": True, "updated_at": _now_iso()}

    # ── cost table ─────────────────────────────────────────────────

    def _get_cost_table_repo(self):
        if self._cost_table_repo is None:
            self._cost_table_repo = CostTableRepository(table_dir=str(self._quote_dir()))
        return self._cost_table_repo

    def get_cost_summary(self) -> dict[str, Any]:
        """从成本表 xlsx 读取各运力概览数据（只读）。"""
        repo = self._get_cost_table_repo()
        stats = repo.get_stats()

        repo._reload_if_needed()
        courier_summary: dict[str, dict] = {}
        for record in repo._records:
            key = record.courier
            total = record.first_cost + record.extra_cost
            if key not in courier_summary:
                courier_summary[key] = {
                    "courier": key,
                    "service_type": record.service_type,
                    "base_weight": record.base_weight,
                    "route_count": 0,
                    "cheapest_first": record.first_cost,
                    "cheapest_extra": record.extra_cost,
                    "_cheapest_total": total,
                    "cheapest_route": f"{record.origin}->{record.destination}",
                }
            info = courier_summary[key]
            info["route_count"] += 1
            if total < info["_cheapest_total"]:
                info["cheapest_first"] = record.first_cost
                info["cheapest_extra"] = record.extra_cost
                info["_cheapest_total"] = total
                info["cheapest_route"] = f"{record.origin}->{record.destination}"

        for info in courier_summary.values():
            info.pop("_cheapest_total", None)

        return {
            "success": True,
            "couriers": list(courier_summary.values()),
            "total_records": stats["total_records"],
            "total_files": stats["total_files"],
        }

    def query_route_cost(self, origin: str, destination: str) -> dict[str, Any]:
        """查询指定路线下各运力的成本明细。"""
        origin = (origin or "").strip()
        destination = (destination or "").strip()
        if not origin or not destination:
            return {"success": False, "error": "请输入始发地和目的地"}

        repo = self._get_cost_table_repo()
        candidates = repo.find_candidates(origin=origin, destination=destination, courier=None, limit=500)

        courier_summary: dict[str, dict] = {}
        for record in candidates:
            key = record.courier
            total = record.first_cost + record.extra_cost
            if key not in courier_summary:
                courier_summary[key] = {
                    "courier": key,
                    "service_type": record.service_type,
                    "base_weight": record.base_weight,
                    "route_count": 0,
                    "cheapest_first": record.first_cost,
                    "cheapest_extra": record.extra_cost,
                    "_cheapest_total": total,
                    "cheapest_route": f"{record.origin}->{record.destination}",
                }
            info = courier_summary[key]
            info["route_count"] += 1
            if total < info["_cheapest_total"]:
                info["cheapest_first"] = record.first_cost
                info["cheapest_extra"] = record.extra_cost
                info["_cheapest_total"] = total
                info["cheapest_route"] = f"{record.origin}->{record.destination}"

        for info in courier_summary.values():
            info.pop("_cheapest_total", None)

        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "couriers": list(courier_summary.values()),
        }

    def reset_database(self, db_type: str) -> dict[str, Any]:
        """Reset route cost table files."""
        target = str(db_type or "all").strip().lower()
        result: dict[str, Any] = {"success": True, "results": {}}

        if target in {"routes", "all"}:
            quote_dir = self._quote_dir()
            deleted = 0
            for fp in [*quote_dir.glob("*.xlsx"), *quote_dir.glob("*.xls"), *quote_dir.glob("*.csv")]:
                fp.unlink(missing_ok=True)
                deleted += 1
            result["results"]["routes"] = {"message": f"Deleted {deleted} cost table files"}
            self._cost_table_repo = None

        return result
