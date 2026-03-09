from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "brand_spotlight",
    "name": "品牌聚焦",
    "desc": "大尺寸单品牌展示，适合突出核心品牌",
    "tags": ["品牌", "聚焦", "简洁"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    first_logo = ""
    first_name = ""
    if brand_items:
        first_logo = e(brand_items[0].get("src", ""))
        first_name = e(brand_items[0].get("name", ""))

    remaining_grid = brand_grid_html(
        brand_items[1:], shape="circle", size=80, gap=12,
        show_name=True, name_color="#666",
    )

    labels_html = ""
    if labels:
        labels_html = f'''<div style="margin-top:20px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px;">
            <span style="font-size:22px;color:#999;background:#f0f0f0;padding:6px 18px;
                border-radius:999px;letter-spacing:1px;">{labels}</span>
        </div>'''

    body = f'''
<div style="width:1080px;height:1080px;position:relative;display:flex;
    flex-direction:column;align-items:center;padding:60px 80px;
    background:#f8f8f8;">
    {f'<img src="{first_logo}" alt="{first_name}" style="width:300px;height:300px;object-fit:contain;margin-top:20px;">' if first_logo else ''}
    {f'<div style="font-size:48px;font-weight:900;color:#222;margin-top:24px;text-align:center;">{first_name}</div>' if first_name else ''}
    <div style="font-size:72px;font-weight:900;color:#e85c2b;margin-top:28px;text-align:center;letter-spacing:2px;">{headline}</div>
    <div style="font-size:36px;font-weight:700;color:#999;margin-top:16px;text-align:center;">{sub_headline}</div>
    {labels_html}
    {f'<div style="margin-top:36px;">{remaining_grid}</div>' if remaining_grid else ''}
    <div style="margin-top:auto;padding-bottom:40px;font-size:24px;color:#bbb;text-align:center;">{tagline}</div>
</div>'''

    return wrap_page(body, bg="#f8f8f8")
