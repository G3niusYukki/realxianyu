"""QuoteService facade — delegates to handlers for backward compatibility."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.dashboard.services.quote.cost_handler import CostTableHandler
from src.dashboard.services.quote.markup_handler import MarkupHandler
from src.dashboard.services.quote.route_handler import RouteTableHandler


class QuoteService:
    """Handles quote-related dashboard operations: routes, markup rules, pricing, cost tables."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._route_handler = RouteTableHandler(project_root)
        self._markup_handler = MarkupHandler(project_root)
        self._cost_handler = CostTableHandler(project_root)

    @property
    def config_path(self) -> Path:
        return self.project_root / "config" / "config.yaml"

    def _quote_dir(self) -> Path:
        return self._route_handler._quote_dir()

    @property
    def _MARKUP_FILE_EXTS(self) -> set[str]:
        return self._markup_handler._MARKUP_FILE_EXTS

    def route_stats(self) -> dict[str, Any]:
        return self._route_handler.route_stats()

    def _route_stats_nonblocking(self) -> dict[str, Any]:
        return self._route_handler._route_stats_nonblocking()

    def import_route_files(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        return self._route_handler.import_route_files(files)

    def export_routes_zip(self) -> tuple[bytes, str]:
        return self._route_handler.export_routes_zip()

    def import_markup_files(self, files: list[tuple[str, bytes]]) -> dict[str, Any]:
        return self._markup_handler.import_markup_files(files)

    def get_markup_rules(self) -> dict[str, Any]:
        return self._markup_handler.get_markup_rules()

    def save_markup_rules(self, rules: Any) -> dict[str, Any]:
        return self._markup_handler.save_markup_rules(rules)

    def _to_non_negative_float(self, value: Any, default: float = 0.0) -> float:
        return self._markup_handler._to_non_negative_float(value, default)

    def _normalize_markup_rules(self, rules: Any) -> dict[str, dict[str, float]]:
        return self._markup_handler._normalize_markup_rules(rules)

    def get_pricing_config(self) -> dict[str, Any]:
        return self._cost_handler.get_pricing_config()

    def save_pricing_config(
        self,
        markup_categories: Any = None,
        xianyu_discount: Any = None,
        volume_divisor_default: Any = None,
        volume_divisors: Any = None,
        freight_courier_priority: Any = None,
    ) -> dict[str, Any]:
        return self._cost_handler.save_pricing_config(
            markup_categories=markup_categories,
            xianyu_discount=xianyu_discount,
            volume_divisor_default=volume_divisor_default,
            volume_divisors=volume_divisors,
            freight_courier_priority=freight_courier_priority,
        )

    def _get_cost_table_repo(self):
        return self._cost_handler._get_cost_table_repo()

    def get_cost_summary(self) -> dict[str, Any]:
        return self._cost_handler.get_cost_summary()

    def query_route_cost(self, origin: str, destination: str) -> dict[str, Any]:
        return self._cost_handler.query_route_cost(origin, destination)

    def reset_database(self, db_type: str) -> dict[str, Any]:
        return self._route_handler.reset_database(db_type)
