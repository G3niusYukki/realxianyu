"""3 种标题样式修饰器 — 纯 CSS 规则，控制 .title-text 元素。"""

from __future__ import annotations

from typing import Any

from .base import ModifierOutput, register_modifier


@register_modifier("title_style", "bold_impact", name="超大加粗", desc="128px 特粗冲击标题")
def bold_impact(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(css_rules="""
.title-text {
    font-size: 128px;
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: -2px;
}
""")


@register_modifier("title_style", "gradient_text", name="渐变文字", desc="渐变色填充标题")
def gradient_text(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(css_rules="""
.title-text {
    font-size: 108px;
    font-weight: 900;
    line-height: 1.15;
    background: linear-gradient(135deg, var(--text-accent) 0%, #fff 50%, var(--text-accent) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(3px 3px 6px rgba(0,0,0,0.3));
}
""")


@register_modifier("title_style", "stroke_outline", name="描边阴影", desc="描边+投影立体标题")
def stroke_outline(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(css_rules="""
.title-text {
    font-size: 112px;
    font-weight: 900;
    line-height: 1.15;
    -webkit-text-stroke: 3px var(--text-accent, #fbbf24);
    color: transparent;
    text-shadow:
        4px 4px 0 var(--text-accent, #fbbf24),
        6px 6px 12px rgba(0,0,0,0.4);
    paint-order: stroke fill;
}
""")
