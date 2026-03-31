"""Cost table handler — pricing config, cost summary, route cost queries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.config import get_config
from src.dashboard.helpers.utils import _now_iso
from src.modules.quote.cost_table import CostTableRepository
from src.modules.quote.setup import QuoteSetupService


class CostTableHandler:
    """Handles cost table queries, pricing config, and cost summary."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._cost_table_repo: Any = None

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

    def _get_cost_table_repo(self):
        if self._cost_table_repo is None:
            self._cost_table_repo = CostTableRepository(table_dir=str(self._quote_dir()))
        return self._cost_table_repo

    def get_pricing_config(self) -> dict[str, Any]:
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
        try:
            from src.modules.messages.service import _active_service

            if _active_service is not None:
                _active_service.reload_quote_engine()
        except Exception:
            pass

        return {"success": True, "updated_at": _now_iso()}

    def get_cost_summary(self) -> dict[str, Any]:
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
