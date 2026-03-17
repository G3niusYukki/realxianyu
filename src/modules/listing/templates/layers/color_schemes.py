"""4 种配色修饰器 — 纯 CSS 变量注入。"""

from __future__ import annotations

from typing import Any

from .base import ModifierOutput, register_modifier


@register_modifier("color_scheme", "red_gold", name="红金促销", desc="红底金字经典促销风格")
def red_gold(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(
        css_vars={
            "--bg-primary": "#dc2626",
            "--bg-secondary": "#fef3c7",
            "--text-primary": "#7f1d1d",
            "--text-light": "#ffffff",
            "--text-accent": "#fbbf24",
            "--border-color": "#b91c1c",
            "--badge-bg": "#fbbf24",
            "--badge-text": "#7c2d12",
        }
    )


@register_modifier("color_scheme", "dark_neon", name="暗夜霓虹", desc="深色背景+霓虹色强调")
def dark_neon(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(
        css_vars={
            "--bg-primary": "#0f172a",
            "--bg-secondary": "#1e293b",
            "--text-primary": "#e2e8f0",
            "--text-light": "#f1f5f9",
            "--text-accent": "#22d3ee",
            "--border-color": "#334155",
            "--badge-bg": "#06b6d4",
            "--badge-text": "#ffffff",
        }
    )


@register_modifier("color_scheme", "clean_white", name="极简白底", desc="白底深色字极简风格")
def clean_white(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(
        css_vars={
            "--bg-primary": "#ffffff",
            "--bg-secondary": "#f8fafc",
            "--text-primary": "#1e293b",
            "--text-light": "#334155",
            "--text-accent": "#dc2626",
            "--border-color": "#e2e8f0",
            "--badge-bg": "#dc2626",
            "--badge-text": "#ffffff",
        }
    )


@register_modifier("color_scheme", "warm_gradient", name="暖色渐变", desc="橙黄系暖色渐变")
def warm_gradient(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(
        css_vars={
            "--bg-primary": "#f97316",
            "--bg-secondary": "#fef3c7",
            "--text-primary": "#7c2d12",
            "--text-light": "#ffffff",
            "--text-accent": "#ffffff",
            "--border-color": "#ea580c",
            "--badge-bg": "#fbbf24",
            "--badge-text": "#7c2d12",
        },
        css_rules="body { background: linear-gradient(135deg, #f97316 0%, #ef4444 50%, #dc2626 100%) !important; }",
    )
