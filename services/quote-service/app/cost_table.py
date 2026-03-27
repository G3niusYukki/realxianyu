"""Cost table repository for managing shipping rates."""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CostEntry:
    """Single cost table entry."""

    region_from: str
    region_to: str
    courier: str
    base_price: float
    weight_rate: float
    volume_rate: float
    min_price: float
    max_price: float | None = None
    eta_days_min: int = 1
    eta_days_max: int = 7


class CostTableRepository:
    """Repository for managing cost tables."""

    def __init__(self, data_path: str | Path | None = None) -> None:
        """Initialize cost table repository.

        Args:
            data_path: Path to cost table data files.
        """
        self.data_path = Path(data_path) if data_path else Path(__file__).parent / "data"
        self._entries: list[CostEntry] = []
        self._couriers: set[str] = set()
        self._regions: set[str] = set()

    def load_from_csv(self, filepath: str | Path) -> None:
        """Load cost table from CSV file.

        Args:
            filepath: Path to CSV file.

        CSV format:
            region_from,region_to,courier,base_price,weight_rate,volume_rate,min_price,max_price,eta_days_min,eta_days_max
        """
        path = Path(filepath)
        if not path.exists():
            logger.warning("Cost table file not found: %s", path)
            return

        entries = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    entry = CostEntry(
                        region_from=row["region_from"],
                        region_to=row["region_to"],
                        courier=row["courier"],
                        base_price=float(row["base_price"]),
                        weight_rate=float(row["weight_rate"]),
                        volume_rate=float(row.get("volume_rate", "0")),
                        min_price=float(row.get("min_price", "0")),
                        max_price=float(row["max_price"]) if row.get("max_price") else None,
                        eta_days_min=int(row.get("eta_days_min", "1")),
                        eta_days_max=int(row.get("eta_days_max", "7")),
                    )
                    entries.append(entry)
                    self._couriers.add(entry.courier)
                    self._regions.add(entry.region_from)
                    self._regions.add(entry.region_to)
                except (KeyError, ValueError) as e:
                    logger.warning("Skipping invalid row: %s - %s", row, e)

        self._entries.extend(entries)
        logger.info("Loaded %d entries from %s", len(entries), path)

    def load_from_json(self, filepath: str | Path) -> None:
        """Load cost table from JSON file.

        Args:
            filepath: Path to JSON file.

        JSON format:
            [
                {
                    "region_from": "...",
                    "region_to": "...",
                    "courier": "...",
                    "base_price": 10.0,
                    "weight_rate": 2.0,
                    ...
                }
            ]
        """
        path = Path(filepath)
        if not path.exists():
            logger.warning("Cost table file not found: %s", path)
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries = []
        for item in data:
            try:
                entry = CostEntry(
                    region_from=item["region_from"],
                    region_to=item["region_to"],
                    courier=item["courier"],
                    base_price=float(item["base_price"]),
                    weight_rate=float(item["weight_rate"]),
                    volume_rate=float(item.get("volume_rate", 0)),
                    min_price=float(item.get("min_price", 0)),
                    max_price=float(item["max_price"]) if item.get("max_price") else None,
                    eta_days_min=int(item.get("eta_days_min", 1)),
                    eta_days_max=int(item.get("eta_days_max", 7)),
                )
                entries.append(entry)
                self._couriers.add(entry.courier)
                self._regions.add(entry.region_from)
                self._regions.add(entry.region_to)
            except (KeyError, ValueError) as e:
                logger.warning("Skipping invalid entry: %s - %s", item, e)

        self._entries.extend(entries)
        logger.info("Loaded %d entries from %s", len(entries), path)

    def get_cost(
        self,
        origin: str,
        dest: str,
        courier: str | None = None,
    ) -> CostEntry | None:
        """Get cost entry for route.

        Args:
            origin: Origin region.
            dest: Destination region.
            courier: Optional courier filter.

        Returns:
            Matching cost entry or None.
        """
        # Try exact match first
        for entry in self._entries:
            if entry.region_from == origin and entry.region_to == dest:
                if courier is None or entry.courier == courier:
                    return entry

        # Try wildcard match
        for entry in self._entries:
            if (entry.region_from == origin or entry.region_from == "*") and \
               (entry.region_to == dest or entry.region_to == "*"):
                if courier is None or entry.courier == courier:
                    return entry

        return None

    def get_couriers(self) -> list[str]:
        """Get list of available couriers.

        Returns:
            List of courier names.
        """
        return sorted(self._couriers)

    def get_regions(self) -> list[str]:
        """Get list of known regions.

        Returns:
            List of region names.
        """
        return sorted(self._regions)

    def calculate_price(
        self,
        entry: CostEntry,
        weight: float,
        volume: float | None = None,
    ) -> dict[str, Any]:
        """Calculate price based on cost entry.

        Args:
            entry: Cost entry.
            weight: Weight in kg.
            volume: Optional volume in cubic meters.

        Returns:
            Price breakdown.
        """
        # Calculate weight-based price
        weight_price = entry.base_price + (entry.weight_rate * weight)

        # Calculate volume-based price if applicable
        volume_price = 0.0
        if volume and entry.volume_rate > 0:
            volume_price = entry.volume_rate * volume

        # Use higher of weight or volume price
        base_price = max(weight_price, volume_price)

        # Apply minimum price
        final_price = max(base_price, entry.min_price)

        # Apply maximum price if set
        if entry.max_price is not None:
            final_price = min(final_price, entry.max_price)

        return {
            "base_price": round(entry.base_price, 2),
            "weight_price": round(weight_price, 2),
            "volume_price": round(volume_price, 2) if volume else None,
            "min_price": round(entry.min_price, 2),
            "max_price": round(entry.max_price, 2) if entry.max_price else None,
            "final_price": round(final_price, 2),
        }

    def load_defaults(self) -> None:
        """Load default cost table data."""
        # Default entries for common routes
        defaults = [
            CostEntry("北京", "北京", "sf", 8.0, 1.5, 50.0, 8.0, None, 1, 2),
            CostEntry("北京", "上海", "sf", 12.0, 2.0, 80.0, 12.0, None, 2, 3),
            CostEntry("北京", "广州", "sf", 15.0, 2.5, 100.0, 15.0, None, 2, 4),
            CostEntry("上海", "上海", "sf", 8.0, 1.5, 50.0, 8.0, None, 1, 2),
            CostEntry("上海", "北京", "sf", 12.0, 2.0, 80.0, 12.0, None, 2, 3),
            CostEntry("上海", "广州", "sf", 12.0, 2.0, 80.0, 12.0, None, 2, 3),
            CostEntry("广州", "广州", "sf", 8.0, 1.5, 50.0, 8.0, None, 1, 2),
            CostEntry("广州", "北京", "sf", 15.0, 2.5, 100.0, 15.0, None, 2, 4),
            CostEntry("广州", "上海", "sf", 12.0, 2.0, 80.0, 12.0, None, 2, 3),
            CostEntry("*", "*", "sf", 18.0, 3.0, 120.0, 18.0, None, 3, 7),
            CostEntry("北京", "北京", "jd", 7.0, 1.2, 40.0, 7.0, None, 1, 2),
            CostEntry("北京", "上海", "jd", 10.0, 1.8, 60.0, 10.0, None, 2, 3),
            CostEntry("上海", "上海", "jd", 7.0, 1.2, 40.0, 7.0, None, 1, 2),
            CostEntry("*", "*", "jd", 15.0, 2.5, 100.0, 15.0, None, 3, 5),
        ]

        for entry in defaults:
            self._entries.append(entry)
            self._couriers.add(entry.courier)
            self._regions.add(entry.region_from)
            self._regions.add(entry.region_to)

        logger.info("Loaded %d default cost entries", len(defaults))
