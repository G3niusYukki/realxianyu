from __future__ import annotations
from typing import Any
from ._common import e, brand_price_list_html, wrap_page

FRAME_META = {
    "id": "price_table",
    "name": "价格对比表",
    "desc": "表格式价格对比，清晰展示各品牌价格",
    "tags": ["价格", "对比", "清晰"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])
    accent = theme.get("primary", "#dc2626")

    price_list = brand_price_list_html(
        brand_items,
        price_text=headline,
        accent_color=accent,
    )
    if not price_list:
        price_list = (
            '<div style="padding:48px 24px;text-align:center;font-size:28px;'
            'color:#9ca3af;">暂无价格数据</div>'
        )

    pills = ""
    if labels:
        parts = [p.strip() for p in labels.split(",") if p.strip()]
        for part in parts[:6]:
            pills += (
                f'<span style="display:inline-block;padding:8px 20px;'
                f'margin:4px;background:rgba(220,38,38,0.12);color:{accent};'
                f'font-size:18px;font-weight:700;border-radius:999px;">{part}</span>'
            )
        pills = f'<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:4px;">{pills}</div>'

    body = f'''
<div style="width:1080px;height:1080px;display:flex;flex-direction:column;
    background:#f9fafb;">
    <div style="width:100%;height:4px;background:{accent};flex-shrink:0;"></div>
    <div style="flex:1;display:flex;flex-direction:column;padding:36px 48px 40px;">
        <div style="border-bottom:3px solid rgba(220,38,38,0.25);padding-bottom:8px;
            margin-bottom:12px;">
            <div style="font-size:64px;font-weight:900;color:{accent};">{headline}</div>
        </div>
        <div style="font-size:28px;color:#6b7280;margin-bottom:28px;">{sub_headline}</div>
        <div style="flex:1;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.06);
            overflow:hidden;padding:8px 0;">
            {price_list}
        </div>
        {pills}
        <div style="margin-top:24px;font-size:22px;color:#374151;letter-spacing:2px;">{tagline}</div>
    </div>
</div>'''

    return wrap_page(body, bg="#f9fafb")
