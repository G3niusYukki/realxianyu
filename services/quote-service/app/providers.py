"""Quote provider interfaces and implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderQuote:
    """Quote data from external provider."""

    courier: str
    price: float
    eta_days: int
    currency: str = "CNY"
    metadata: dict[str, Any] | None = None


class QuoteProvider(ABC):
    """Abstract base class for quote providers."""

    @abstractmethod
    async def get_quote(
        self,
        origin: str,
        dest: str,
        weight: float,
        volume: float | None = None,
    ) -> ProviderQuote | None:
        """Get quote from provider.

        Args:
            origin: Origin address/region code.
            dest: Destination address/region code.
            weight: Weight in kg.
            volume: Optional volume in cubic meters.

        Returns:
            ProviderQuote if available, None otherwise.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy.

        Returns:
            True if provider is available.
        """
        ...


class MockQuoteProvider(QuoteProvider):
    """Mock provider for development and testing."""

    def __init__(self, courier_name: str = "mock") -> None:
        """Initialize mock provider.

        Args:
            courier_name: Name of the courier service.
        """
        self.courier_name = courier_name
        self._base_rates: dict[str, dict[str, float]] = {
            "local": {"base": 8.0, "per_kg": 1.5},
            "regional": {"base": 12.0, "per_kg": 2.0},
            "remote": {"base": 18.0, "per_kg": 3.0},
        }

    def _get_zone(self, origin: str, dest: str) -> str:
        """Determine shipping zone based on origin and destination.

        Args:
            origin: Origin address.
            dest: Destination address.

        Returns:
            Zone name (local, regional, remote).
        """
        # Simple zone determination based on address matching
        origin_prefix = origin[:2] if len(origin) >= 2 else origin
        dest_prefix = dest[:2] if len(dest) >= 2 else dest

        if origin_prefix == dest_prefix:
            return "local"
        elif origin_prefix in ["北京", "上海", "广州", "深圳"] or dest_prefix in ["北京", "上海", "广州", "深圳"]:
            return "regional"
        else:
            return "remote"

    async def get_quote(
        self,
        origin: str,
        dest: str,
        weight: float,
        volume: float | None = None,
    ) -> ProviderQuote | None:
        """Get mock quote.

        Args:
            origin: Origin address.
            dest: Destination address.
            weight: Weight in kg.
            volume: Optional volume in cubic meters.

        Returns:
            Mock provider quote.
        """
        zone = self._get_zone(origin, dest)
        rates = self._base_rates.get(zone, self._base_rates["remote"])

        # Calculate base price
        price = rates["base"] + (rates["per_kg"] * weight)

        # Add volume surcharge if applicable
        if volume and volume > 0.01:  # > 10 liters
            price += volume * 100  # 100 CNY per cubic meter

        # Determine ETA based on zone
        eta_map = {
            "local": 1,
            "regional": 2,
            "remote": 3,
        }

        return ProviderQuote(
            courier=self.courier_name,
            price=round(price, 2),
            eta_days=eta_map.get(zone, 3),
            currency="CNY",
            metadata={
                "zone": zone,
                "weight": weight,
                "volume": volume,
            },
        )

    async def health_check(self) -> bool:
        """Mock provider is always healthy.

        Returns:
            Always True.
        """
        return True


class SFExpressProvider(QuoteProvider):
    """SF Express provider implementation (placeholder)."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize SF Express provider.

        Args:
            api_key: API key for SF Express.
        """
        self.api_key = api_key
        self._base_url = "https://api.sf-express.com"

    async def get_quote(
        self,
        origin: str,
        dest: str,
        weight: float,
        volume: float | None = None,
    ) -> ProviderQuote | None:
        """Get SF Express quote.

        Args:
            origin: Origin address.
            dest: Destination address.
            weight: Weight in kg.
            volume: Optional volume in cubic meters.

        Returns:
            ProviderQuote if successful, None otherwise.
        """
        # Placeholder for actual SF Express API integration
        # In production, this would call the SF Express API
        raise NotImplementedError("SF Express API integration not implemented")

    async def health_check(self) -> bool:
        """Check SF Express API health.

        Returns:
            True if API is available.
        """
        # Placeholder for actual health check
        return False
