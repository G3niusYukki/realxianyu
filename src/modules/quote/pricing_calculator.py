"""Shared three-tier pricing logic for quote providers.

Encapsulates the common calculation pipeline used by both
CostTableMarkupQuoteProvider and ApiCostMarkupQuoteProvider:
  1. Resolve markup rules (category_markup or legacy markup_rules)
  2. Volume weight calculation
  3. Billing weight = max(actual, volume, [api_billable])
  4. Three-tier calculation: cost -> markup -> xianyu discount
  5. Extra fee calculation
  6. Oversize warning
  7. Building the explain dict
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.modules.quote.cost_table import normalize_courier_name

# ---------------------------------------------------------------------------
# Default markup rule
# ---------------------------------------------------------------------------

DEFAULT_MARKUP_RULE: dict[str, float] = {
    "normal_first_add": 0.50,
    "member_first_add": 0.25,
    "normal_extra_add": 0.50,
    "member_extra_add": 0.30,
}

# ---------------------------------------------------------------------------
# Category key aliases (bidirectional CN <-> EN)
# ---------------------------------------------------------------------------

_CATEGORY_KEY_ALIASES: dict[str, str] = {
    "线上快递": "express",
    "线下快递": "express_offline",
    "线上快运": "freight",
    "线下快运": "freight_offline",
    "express": "线上快递",
    "express_offline": "线下快递",
    "freight": "线上快运",
    "freight_offline": "线下快运",
}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _first_positive(*values: Any) -> float:
    for value in values:
        v = _to_float(value)
        if v is not None and v > 0:
            return float(v)
    return 0.0


def _eta_by_service_level(service_level: str) -> int:
    text = str(service_level or "").strip().lower()
    if text == "urgent":
        return 12 * 60
    if text == "express":
        return 24 * 60
    return 48 * 60


# ---------------------------------------------------------------------------
# Markup / discount normalisation helpers
# ---------------------------------------------------------------------------


def _normalize_markup_rules(raw_rules: dict[str, Any]) -> dict[str, dict[str, float]]:
    rules: dict[str, dict[str, float]] = {"default": dict(DEFAULT_MARKUP_RULE)}
    if not isinstance(raw_rules, dict):
        return rules

    for key, value in raw_rules.items():
        if not isinstance(value, dict):
            continue
        courier_key = normalize_courier_name(str(key).strip()) if str(key).strip() else "default"
        target = dict(DEFAULT_MARKUP_RULE)
        for field_name in DEFAULT_MARKUP_RULE:
            if field_name in value:
                target[field_name] = float(value[field_name])
        rules[courier_key or "default"] = target

    if "default" not in rules:
        rules["default"] = dict(DEFAULT_MARKUP_RULE)
    return rules


def _normalize_category_markup(raw: dict[str, Any]) -> dict[str, dict[str, dict[str, float]]]:
    """Parse category markup config.

    Returns: { category: { courier: { "first_add": x, "extra_add": y } } }
    """
    result: dict[str, dict[str, dict[str, float]]] = {}
    if not isinstance(raw, dict):
        return result
    for category, couriers in raw.items():
        cat = str(category).strip()
        if not cat or not isinstance(couriers, dict):
            continue
        cat_rules: dict[str, dict[str, float]] = {}
        for courier_key, rule in couriers.items():
            key = str(courier_key).strip()
            if not key or not isinstance(rule, dict):
                continue
            cat_rules[key if key == "default" else normalize_courier_name(key)] = {
                "first_add": float(rule.get("first_add", 0.0)),
                "extra_add": float(rule.get("extra_add", 0.0)),
            }
        if "default" not in cat_rules:
            cat_rules["default"] = {"first_add": 0.0, "extra_add": 0.0}
        result[cat] = cat_rules
    return result


def _normalize_xianyu_discount(raw: dict[str, Any]) -> dict[str, dict[str, dict[str, float]]]:
    """Parse xianyu discount config.

    Returns: { category: { courier: { "first_discount": x, "extra_discount": y } } }
    """
    result: dict[str, dict[str, dict[str, float]]] = {}
    if not isinstance(raw, dict):
        return result
    for category, couriers in raw.items():
        cat = str(category).strip()
        if not cat or not isinstance(couriers, dict):
            continue
        cat_rules: dict[str, dict[str, float]] = {}
        for courier_key, rule in couriers.items():
            key = str(courier_key).strip()
            if not key or not isinstance(rule, dict):
                continue
            cat_rules[key if key == "default" else normalize_courier_name(key)] = {
                "first_discount": float(rule.get("first_discount", 0.0)),
                "extra_discount": float(rule.get("extra_discount", 0.0)),
            }
        if "default" not in cat_rules:
            cat_rules["default"] = {"first_discount": 0.0, "extra_discount": 0.0}
        result[cat] = cat_rules
    return result


# ---------------------------------------------------------------------------
# Markup / discount resolution helpers
# ---------------------------------------------------------------------------


def _resolve_category_rules(rules: dict[str, Any], category: str) -> dict[str, Any]:
    """Look up rules by category with EN/CN alias fallback."""
    cat_rules = rules.get(category)
    if not cat_rules:
        alias = _CATEGORY_KEY_ALIASES.get(category, "")
        cat_rules = rules.get(alias) if alias else None
    return cat_rules if isinstance(cat_rules, dict) else {}


def _resolve_category_markup(
    rules: dict[str, dict[str, dict[str, float]]],
    category: str,
    courier: str,
) -> tuple[float, float]:
    """Look up markup by category and courier, returning (first_add, extra_add)."""
    cat_rules = _resolve_category_rules(rules, category)
    courier_rule = cat_rules.get(courier) or cat_rules.get("default") or {}
    return (
        float(courier_rule.get("first_add", 0.0)),
        float(courier_rule.get("extra_add", 0.0)),
    )


def _resolve_xianyu_discount_value(
    rules: dict[str, dict[str, dict[str, float]]],
    category: str,
    courier: str,
) -> tuple[float, float]:
    """Look up discount by category and courier, returning (first_discount, extra_discount)."""
    cat_rules = _resolve_category_rules(rules, category)
    courier_rule = cat_rules.get(courier) or cat_rules.get("default") or {}
    return (
        float(courier_rule.get("first_discount", 0.0)),
        float(courier_rule.get("extra_discount", 0.0)),
    )


def _resolve_markup(markup_rules: dict[str, dict[str, float]], courier: str | None) -> dict[str, float]:
    normalized = normalize_courier_name(courier)
    if normalized in markup_rules:
        return markup_rules[normalized]
    return markup_rules.get("default", dict(DEFAULT_MARKUP_RULE))


def _profile_markup(markup: dict[str, float], pricing_profile: str) -> tuple[float, float]:
    profile = str(pricing_profile or "normal").strip().lower()
    if profile == "member":
        return float(markup.get("member_first_add", 0.0)), float(markup.get("member_extra_add", 0.0))
    return float(markup.get("normal_first_add", 0.0)), float(markup.get("normal_extra_add", 0.0))


# ---------------------------------------------------------------------------
# Volume weight helpers
# ---------------------------------------------------------------------------


def _resolve_volume_divisor(
    volume_divisors: dict[str, Any],
    category: str,
    courier: str,
    global_default: float,
) -> float:
    """Resolve throw-ratio: per-courier > category default > global default."""
    if not isinstance(volume_divisors, dict):
        return float(global_default or 0.0) or 0.0
    cat_cfg = volume_divisors.get(category)
    if not isinstance(cat_cfg, dict):
        alias = _CATEGORY_KEY_ALIASES.get(category, "")
        cat_cfg = volume_divisors.get(alias) if alias else None
    if not isinstance(cat_cfg, dict):
        return float(global_default or 0.0) or 0.0
    v = _to_float(cat_cfg.get(courier))
    if v is not None and v > 0:
        return float(v)
    v = _to_float(cat_cfg.get("default"))
    if v is not None and v > 0:
        return float(v)
    return float(global_default or 0.0) or 0.0


def _derive_volume_weight_kg(volume_cm3: float, explicit_volume_weight: float, divisor: float) -> float:
    explicit = _to_float(explicit_volume_weight)
    if explicit is not None and explicit > 0:
        return float(explicit)
    volume = _to_float(volume_cm3)
    div = _to_float(divisor)
    if volume is None or volume <= 0 or div is None or div <= 0:
        return 0.0
    return round(float(volume) / float(div), 3)


# ---------------------------------------------------------------------------
# Data classes for compute_three_tier_price
# ---------------------------------------------------------------------------


@dataclass
class PricingInput:
    """All inputs needed for the three-tier price calculation."""

    first_cost: float
    extra_cost: float
    base_weight: float
    actual_weight: float
    volume_cm3: float
    volume_weight: float
    service_type: str  # "express" or "freight"
    courier: str
    category: str  # e.g. "线上快递" or "线上快运"
    service_level: str
    max_dimension_cm: float = 0.0
    api_billable_weight: float | None = None
    throw_ratio: float | None = None


@dataclass
class PricingOutput:
    """All computed values from the three-tier price calculation."""

    billing_weight: float
    first_add: float
    extra_add: float
    first_discount: float
    extra_discount: float
    mini_first: float
    mini_extra: float
    xianyu_first: float
    xianyu_extra: float
    extra_fee: float
    surcharges: dict[str, float]
    oversize_warning: bool
    oversize_threshold: float
    actual_weight: float
    volume_weight: float
    volume_divisor: float
    extra_weight: float


# ---------------------------------------------------------------------------
# Core calculation function
# ---------------------------------------------------------------------------


def compute_three_tier_price(
    inp: PricingInput,
    *,
    category_markup: dict[str, dict[str, dict[str, float]]],
    xianyu_discount_rules: dict[str, dict[str, dict[str, float]]],
    markup_rules: dict[str, dict[str, float]],
    pricing_profile: str,
    volume_divisors: dict[str, Any],
    volume_divisor_default: float,
) -> PricingOutput:
    """Run the shared three-tier pricing calculation.

    Parameters
    ----------
    inp:
        All per-quote inputs (costs, weights, service metadata).
    category_markup:
        Parsed category-based markup rules (from _normalize_category_markup).
    xianyu_discount_rules:
        Parsed xianyu discount rules (from _normalize_xianyu_discount).
    markup_rules:
        Parsed legacy courier-based markup rules (from _normalize_markup_rules).
        Used as fallback when *category_markup* is empty.
    pricing_profile:
        ``"normal"`` or ``"member"`` -- selects the markup tier.
    volume_divisors:
        Per-category/courier volume divisor overrides.
    volume_divisor_default:
        Global default volume divisor.

    Returns
    -------
    PricingOutput with all computed intermediate values.
    """
    # 1. Resolve markup / discount
    if category_markup:
        first_add, extra_add = _resolve_category_markup(category_markup, inp.category, inp.courier)
        first_discount, extra_discount = _resolve_xianyu_discount_value(
            xianyu_discount_rules, inp.category, inp.courier
        )
    else:
        markup = _resolve_markup(markup_rules, inp.courier)
        first_add, extra_add = _profile_markup(markup, pricing_profile)
        first_discount = 0.0
        extra_discount = 0.0

    # 2. Volume weight
    courier_divisor = _resolve_volume_divisor(volume_divisors, inp.category, inp.courier, volume_divisor_default)
    divisor = _first_positive(courier_divisor, inp.throw_ratio, volume_divisor_default)
    volume_weight = _derive_volume_weight_kg(
        volume_cm3=inp.volume_cm3,
        explicit_volume_weight=inp.volume_weight,
        divisor=divisor,
    )

    # 3. Billing weight
    actual_weight = max(0.0, float(inp.actual_weight))
    candidates = [actual_weight, volume_weight]
    if inp.api_billable_weight is not None:
        candidates.append(float(inp.api_billable_weight))
    billing_weight = max(candidates)

    # 4. Extra weight
    extra_weight = max(0.0, billing_weight - inp.base_weight)

    # 5. Three-tier calculation: cost -> markup -> xianyu discount
    mini_first = float(inp.first_cost) + first_add
    mini_extra = float(inp.extra_cost) + extra_add
    xianyu_first = max(0.0, mini_first - first_discount)
    xianyu_extra = max(0.0, mini_extra - extra_discount)

    extra_fee = extra_weight * xianyu_extra

    # 6. Surcharges
    surcharges: dict[str, float] = {}
    if extra_fee > 0:
        surcharges["\u7eed\u91cd"] = round(extra_fee, 2)  # "续重"

    # 7. Oversize warning
    max_dim = float(inp.max_dimension_cm or 0.0)
    oversize_threshold = 150.0 if inp.service_type == "freight" else 120.0
    oversize_warning = max_dim > oversize_threshold if max_dim > 0 else False

    return PricingOutput(
        billing_weight=billing_weight,
        first_add=first_add,
        extra_add=extra_add,
        first_discount=first_discount,
        extra_discount=extra_discount,
        mini_first=mini_first,
        mini_extra=mini_extra,
        xianyu_first=xianyu_first,
        xianyu_extra=xianyu_extra,
        extra_fee=extra_fee,
        surcharges=surcharges,
        oversize_warning=oversize_warning,
        oversize_threshold=oversize_threshold,
        actual_weight=actual_weight,
        volume_weight=volume_weight,
        volume_divisor=divisor,
        extra_weight=extra_weight,
    )
