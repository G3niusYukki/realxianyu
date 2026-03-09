"""5 种装饰修饰器 — CSS + position:absolute 浮动 HTML。"""

from __future__ import annotations

from typing import Any

from .base import ModifierOutput, register_modifier


@register_modifier("decoration", "coupon_edge", name="优惠券锯齿", desc="四边锯齿切割效果")
def coupon_edge(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(
        css_rules="""
body > div:first-child {
    mask-image: radial-gradient(circle 8px at 0px 50%, transparent 8px, #000 8.5px),
                radial-gradient(circle 8px at 100% 50%, transparent 8px, #000 8.5px),
                radial-gradient(circle 8px at 50% 0px, transparent 8px, #000 8.5px),
                radial-gradient(circle 8px at 50% 100%, transparent 8px, #000 8.5px);
    mask-size: 51% 20px, 51% 20px, 20px 51%, 20px 51%;
    mask-position: left, right, top, bottom;
    mask-repeat: repeat-y, repeat-y, repeat-x, repeat-x;
    mask-composite: intersect;
    -webkit-mask-composite: source-in;
}
""",
    )


@register_modifier("decoration", "burst_badge", name="爆炸贴", desc="右上角星形角标")
def burst_badge(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    svg_star = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">'
        '<polygon points="100,0 120,70 195,70 135,115 155,190 100,145 45,190 65,115 5,70 80,70" '
        'fill="var(--badge-bg,#fbbf24)"/>'
        '<text x="100" y="110" text-anchor="middle" font-size="28" font-weight="900" '
        'fill="var(--badge-text,#7c2d12)" font-family="sans-serif">HOT</text></svg>'
    )
    overlay = (
        f'<div style="position:absolute;top:20px;right:20px;width:140px;height:140px;'
        f'z-index:10;transform:rotate(12deg);filter:drop-shadow(2px 4px 6px rgba(0,0,0,0.3));">'
        f'{svg_star}</div>'
    )
    return ModifierOutput(overlay_html=overlay)


@register_modifier("decoration", "ribbon", name="飘带横幅", desc="左上角对角飘带")
def ribbon(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    overlay = '''
<div style="position:absolute;top:0;left:0;width:200px;height:200px;overflow:hidden;z-index:10;">
  <div style="position:absolute;top:28px;left:-40px;width:240px;text-align:center;
      transform:rotate(-45deg);background:var(--badge-bg,#dc2626);
      color:var(--badge-text,#fff);font-size:18px;font-weight:800;
      padding:8px 0;box-shadow:0 4px 12px rgba(0,0,0,0.3);
      letter-spacing:2px;">限时特惠</div>
</div>'''
    return ModifierOutput(overlay_html=overlay)


@register_modifier("decoration", "dot_pattern", name="波点纹理", desc="半透明波点背景纹理")
def dot_pattern(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput(
        css_rules="""
body > div:first-child::before {
    content: '';
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    background: radial-gradient(circle 3px, rgba(255,255,255,0.15) 2px, transparent 2.5px);
    background-size: 30px 30px;
}
body > div:first-child > * { position: relative; z-index: 2; }
""",
    )


@register_modifier("decoration", "none", name="无装饰", desc="不添加任何装饰元素")
def no_decoration(_params: dict[str, Any], _theme: dict[str, Any]) -> ModifierOutput:
    return ModifierOutput()
