"""Route table handler — import/export route files and statistics."""

from __future__ import annotations

import io
import logging
import re
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.config import get_config
from src.modules.quote.cost_table import CostTableRepository

logger = logging.getLogger(__name__)


class RouteTableHandler:
    """Handles route table file import, export, and statistics."""

    _ROUTE_FILE_EXTS = {".xlsx", ".xls", ".csv"}

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._cost_table_repo: Any = None
        self._route_stats_cache: dict[str, Any] | None = None
        self._route_stats_mtime: float = 0.0
        self._route_stats_ts: float = 0.0
        self._ROUTE_STATS_TTL: float = 120.0
        self._route_stats_lock = threading.Lock()

    @property
    def config_path(self) -> Path:
        return self.project_root / "config" / "config.yaml"

    def _quote_dir(self) -> Path:
        cfg = get_config().get_section("quote", {})
        table_dir = str(cfg.get("cost_table_dir", "data/quote_costs"))
        path = Path(table_dir)
        if not path.is_absolute():
            path = self.project_root / path
        path.mkdir(parents=True, exist_ok=True)
        return path

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
        if self._route_stats_cache is not None:
            return self._route_stats_cache
        return {"success": True, "stats": {}}

    @staticmethod
    def _safe_filename(name: str) -> str:
        base_name = Path(str(name or "")).name
        ext = Path(base_name).suffix.lower()
        stem_raw = Path(base_name).stem
        stem = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fa5]+", "_", stem_raw).strip("_-")
        if not stem:
            stem = f"upload_{int(time.time())}"
        if ext not in RouteTableHandler._ROUTE_FILE_EXTS:
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

    @staticmethod
    def _decode_text_bytes(content: bytes) -> str:
        data = bytes(content or b"")
        for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk", "big5"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="ignore")

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

    def reset_database(self, db_type: str) -> dict[str, Any]:
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
