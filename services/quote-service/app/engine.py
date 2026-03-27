"""Quote calculation engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.cost_table import CostTableRepository
from app.providers import MockQuoteProvider, ProviderQuote, QuoteProvider

logger = logging.getLogger(__name__)


@dataclass
class QuoteResult:
    """Quote calculation result."""

    courier: str
    price: float
    currency: str
    eta_days: int
    eta_days_max: int | None = None
    volume_formula: str | None = None
    is_vip_price: bool = False
    breakdown: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class QuoteEngine:
    """Quote calculation engine."""

    # Volume weight divisor (kg per cubic meter)
    # Industry standard: 1 CBM = 167 kg for air freight
    VOLUME_WEIGHT_DIVISOR = 6  # 1/6 = 167 kg per CBM

    def __init__(
        self,
        cost_repository: CostTableRepository | None = None,
        providers: list[QuoteProvider] | None = None,
    ) -> None:
        """Initialize quote engine.

        Args:
            cost_repository: Cost table repository.
            providers: List of external quote providers.
        """
        self.cost_repo = cost_repository or CostTableRepository()
        self.providers = providers or [MockQuoteProvider("mock")]
        self._vip_discount = 0.9  # 10% discount for VIP

    def calculate_volume_weight(
        self,
        length: float,
        width: float,
        height: float,
    ) -> float:
        """Calculate volume weight.

        Volume weight is used when it's greater than actual weight.
        Formula: (L * W * H) / volume_weight_divisor

        Args:
            length: Length in cm.
            width: Width in cm.
            height: Height in cm.

        Returns:
            Volume weight in kg.
        """
        volume_cbm = (length * width * height) / 1_000_000  # Convert to cubic meters
        volume_weight = volume_cbm * 167  # Standard air freight conversion
        return round(volume_weight, 2)

    def calculate_volume_weight_from_cbm(self, volume: float) -> float:
        """Calculate volume weight from cubic meters.

        Args:
            volume: Volume in cubic meters.

        Returns:
            Volume weight in kg.
        """
        return round(volume * 167, 2)

    async def calculate_quote(
        self,
        origin: str,
        dest: str,
        weight: float,
        courier: str | None = None,
        volume: float | None = None,
        dimensions: tuple[float, float, float] | None = None,
        is_vip: bool = False,
    ) -> QuoteResult | None:
        """Calculate shipping quote.

        Args:
            origin: Origin address/region.
            dest: Destination address/region.
            weight: Actual weight in kg.
            courier: Preferred courier (optional).
            volume: Volume in cubic meters (optional).
            dimensions: Package dimensions in cm (L, W, H) (optional).
            is_vip: Whether user is VIP member.

        Returns:
            Quote result or None if no quote available.
        """
        # Calculate volume weight if dimensions provided
        volume_formula = None
        chargeable_weight = weight

        if dimensions:
            length, width, height = dimensions
            volume_weight = self.calculate_volume_weight(length, width, height)
            chargeable_weight = max(weight, volume_weight)
            volume_formula = f"max({weight}kg, ({length}*{width}*{height})/6000={volume_weight}kg)"
        elif volume:
            volume_weight = self.calculate_volume_weight_from_cbm(volume)
            chargeable_weight = max(weight, volume_weight)
            volume_formula = f"max({weight}kg, {volume}m³*167={volume_weight}kg)"

        # Try to get quote from cost table first
        result = await self._calculate_from_cost_table(
            origin, dest, chargeable_weight, courier, volume, is_vip
        )

        if result:
            if volume_formula:
                result.volume_formula = volume_formula
            return result

        # Fallback to external providers
        for provider in self.providers:
            try:
                provider_quote = await provider.get_quote(
                    origin, dest, chargeable_weight, volume
                )
                if provider_quote:
                    price = provider_quote.price
                    if is_vip:
                        price = round(price * self._vip_discount, 2)

                    return QuoteResult(
                        courier=provider_quote.courier,
                        price=price,
                        currency=provider_quote.currency,
                        eta_days=provider_quote.eta_days,
                        is_vip_price=is_vip,
                        volume_formula=volume_formula,
                        metadata=provider_quote.metadata,
                    )
            except Exception as e:
                logger.error("Error getting quote from %s: %s", provider.__class__.__name__, e)

        return None

    async def _calculate_from_cost_table(
        self,
        origin: str,
        dest: str,
        weight: float,
        courier: str | None,
        volume: float | None,
        is_vip: bool,
    ) -> QuoteResult | None:
        """Calculate quote using cost table.

        Args:
            origin: Origin region.
            dest: Destination region.
            weight: Chargeable weight.
            courier: Preferred courier.
            volume: Volume in cubic meters.
            is_vip: VIP status.

        Returns:
            Quote result or None.
        """
        entry = self.cost_repo.get_cost(origin, dest, courier)

        if not entry and courier:
            # Try without courier filter
            entry = self.cost_repo.get_cost(origin, dest, None)

        if not entry:
            return None

        # Calculate price breakdown
        breakdown = self.cost_repo.calculate_price(entry, weight, volume)
        final_price = breakdown["final_price"]

        # Apply VIP discount
        if is_vip:
            final_price = round(final_price * self._vip_discount, 2)
            breakdown["vip_discount"] = f"{self._vip_discount * 100:.0f}%"
            breakdown["vip_price"] = final_price

        return QuoteResult(
            courier=entry.courier,
            price=final_price,
            currency="CNY",
            eta_days=entry.eta_days_min,
            eta_days_max=entry.eta_days_max,
            is_vip_price=is_vip,
            breakdown=breakdown,
            metadata={
                "region_from": entry.region_from,
                "region_to": entry.region_to,
                "weight_used": weight,
            },
        )

    async def calculate_quotes(
        self,
        origin: str,
        dest: str,
        weight: float,
        volume: float | None = None,
        dimensions: tuple[float, float, float] | None = None,
        is_vip: bool = False,
    ) -> list[QuoteResult]:
        """Calculate quotes from all available couriers.

        Args:
            origin: Origin address/region.
            dest: Destination address/region.
            weight: Actual weight in kg.
            volume: Volume in cubic meters (optional).
            dimensions: Package dimensions in cm (optional).
            is_vip: Whether user is VIP member.

        Returns:
            List of quote results, sorted by price.
        """
        results = []
        couriers = self.cost_repo.get_couriers()

        # If no couriers in cost repo, use default list
        if not couriers:
            couriers = ["sf", "jd", "ems"]

        for courier_name in couriers:
            result = await self.calculate_quote(
                origin, dest, weight, courier_name, volume, dimensions, is_vip
            )
            if result:
                results.append(result)

        # Sort by price
        results.sort(key=lambda x: x.price)

        return results

    def get_available_couriers(self) -> list[str]:
        """Get list of available couriers.

        Returns:
            List of courier names.
        """
        couriers = self.cost_repo.get_couriers()
        for provider in self.providers:
            if hasattr(provider, 'courier_name'):
                couriers.append(provider.courier_name)
        return sorted(set(couriers))
