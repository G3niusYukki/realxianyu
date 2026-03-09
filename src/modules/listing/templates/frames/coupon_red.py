"""红色折扣横幅 — 淘宝/拼多多风格促销主图。"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "coupon_red",
    "name": "红色折扣横幅",
    "desc": "红色背景大折扣数字，醒目促销风格",
    "tags": ["促销", "折扣", "红色"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    grid = brand_grid_html(brand_items, shape="circle", size=130, gap=16, show_name=True, name_color="#fff")

    label_pills = ""
    if labels:
        parts = [p.strip() for p in labels.split(",") if p.strip()]
        for part in parts:
            label_pills += f'<span style="background:rgba(255,255,255,0.35);color:#fff;padding:8px 20px;border-radius:999px;font-size:24px;font-weight:700;margin:0 6px;">{part}</span>'

    body = f"""
<style>
.coupon-headline {{
    font-family: 'DisplayBold', sans-serif;
    font-size: 108px; font-weight: 900; letter-spacing: 6px;
    color: #fef08a;
    -webkit-text-stroke: 3px #b91c1c;
    text-shadow: 4px 4px 0 rgba(0,0,0,0.15);
    line-height: 1.1;
}}
</style>
<div style="width:1080px;height:1080px;background:linear-gradient(180deg,#dc2626 0%,#b91c1c 100%);
    display:flex;flex-direction:column;align-items:center;
    padding:36px 50px;position:relative;overflow:hidden;">

    <div style="background:linear-gradient(180deg,#fef9c3 0%,#fef08a 100%);border-radius:20px;
        padding:28px 56px;margin-top:16px;box-shadow:0 8px 24px rgba(0,0,0,0.25);
        border:3px solid rgba(255,255,255,0.8);">
        <div class="coupon-headline" style="text-align:center;">
            {headline}
        </div>
    </div>

    <div style="margin-top:24px;font-size:40px;font-weight:800;color:#fff;
        font-family:'DisplayBold',sans-serif;text-align:center;letter-spacing:3px;">
        {sub_headline}
    </div>

    <div style="margin-top:16px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px;">
        {label_pills}
    </div>

    <div style="margin-top:28px;flex:1;display:flex;align-items:center;
        justify-content:center;width:95%;">
        {grid}
    </div>

    <div style="margin-top:20px;margin-bottom:24px;text-align:center;">
        <span style="font-size:28px;font-weight:700;color:rgba(255,255,255,0.95);
            letter-spacing:8px;font-family:'DisplayBold',sans-serif;">
            {tagline}
        </span>
    </div>
</div>"""

    return wrap_page(body, bg="#dc2626")
