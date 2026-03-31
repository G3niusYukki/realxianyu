"""Markup rules handler — import, parse, normalize, and persist markup rules."""

from __future__ import annotations

import io
import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from src.core.config import get_config
from src.dashboard.helpers.utils import _now_iso
from src.modules.quote.cost_table import normalize_courier_name
from src.modules.quote.setup import DEFAULT_MARKUP_RULES, QuoteSetupService

logger = logging.getLogger(__name__)


class MarkupHandler:
    """Handles markup rules: parsing from various file formats, normalization, and persistence."""

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

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    @property
    def config_path(self) -> Path:
        return self.project_root / "config" / "config.yaml"

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
        for field in MarkupHandler._MARKUP_REQUIRED_FIELDS:
            col = header_map.get(field)
            if col is None or col >= len(row):
                return None
            val = MarkupHandler._markup_float(row[col])
            if val is None:
                return None
            rule[field] = val
        return rule

    @staticmethod
    def _coerce_markup_row(value: Any) -> dict[str, float] | None:
        if isinstance(value, dict):
            rule: dict[str, float] = {}
            for field in MarkupHandler._MARKUP_REQUIRED_FIELDS:
                v = value.get(field)
                fv = MarkupHandler._markup_float(v)
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
                    import zipfile

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
