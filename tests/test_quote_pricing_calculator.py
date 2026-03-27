"""Tests for pricing_calculator shared logic."""
import pytest
from src.modules.quote.pricing_calculator import compute_three_tier_price, PricingInput


def test_basic_normal_pricing():
    inp = PricingInput(
        first_cost=10.0, extra_cost=2.0, base_weight=1.0,
        actual_weight=2.0, volume_cm3=0, volume_weight=0,
        service_type="express", courier="顺丰", category="线上快递",
        service_level="standard",
    )
    out = compute_three_tier_price(
        inp,
        category_markup={},
        xianyu_discount_rules={},
        markup_rules={"default": {"normal_first_add": 0.5, "normal_extra_add": 0.5,
                                   "member_first_add": 0.25, "member_extra_add": 0.3}},
        pricing_profile="normal",
        volume_divisors={},
        volume_divisor_default=0,
    )
    assert out.xianyu_first == 10.5
    assert out.billing_weight == 2.0
    assert "续重" in out.surcharges


def test_member_pricing():
    inp = PricingInput(
        first_cost=10.0, extra_cost=2.0, base_weight=1.0,
        actual_weight=1.0, volume_cm3=0, volume_weight=0,
        service_type="express", courier="顺丰", category="线上快递",
        service_level="standard",
    )
    out = compute_three_tier_price(
        inp,
        category_markup={},
        xianyu_discount_rules={},
        markup_rules={"default": {"normal_first_add": 0.5, "normal_extra_add": 0.5,
                                   "member_first_add": 0.25, "member_extra_add": 0.3}},
        pricing_profile="member",
        volume_divisors={},
        volume_divisor_default=0,
    )
    assert out.xianyu_first == 10.25
    assert out.extra_fee == 0.0  # no extra weight


def test_freight_oversize_warning():
    inp = PricingInput(
        first_cost=100.0, extra_cost=5.0, base_weight=30.0,
        actual_weight=50.0, volume_cm3=0, volume_weight=0,
        service_type="freight", courier="德邦", category="线上快运",
        service_level="standard", max_dimension_cm=200.0,
    )
    out = compute_three_tier_price(
        inp,
        category_markup={}, xianyu_discount_rules={},
        markup_rules={"default": {"normal_first_add": 0.5, "normal_extra_add": 0.5,
                                   "member_first_add": 0.25, "member_extra_add": 0.3}},
        pricing_profile="normal",
        volume_divisors={}, volume_divisor_default=0,
    )
    assert out.oversize_warning is True
    assert out.billing_weight == 50.0
