from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "coupon_ticket",
    "name": "优惠券卡片",
    "desc": "仿真优惠券撕票样式，趣味促销风格",
    "tags": ["优惠券", "卡片", "趣味"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    grid = brand_grid_html(
        brand_items,
        shape="rounded_square",
        size=100,
        gap=14,
        show_name=True,
        name_color="#92400e",
    )

    body = f"""
<div style="width:1080px;height:1080px;display:flex;flex-direction:column;align-items:center;justify-content:center;
    background:#fff7ed;padding:40px 0;">

    <div style="margin-bottom:28px;">
        {grid}
    </div>

    <div style="position:relative;width:900px;height:500px;background:#fff;
        border:3px dashed #e0d5c7;border-radius:12px;overflow:visible;
        display:flex;flex-direction:row;box-shadow:0 8px 32px rgba(0,0,0,0.08);">

        <div style="position:absolute;left:-45px;top:50%;transform:translateY(-50%);
            width:90px;height:90px;border-radius:50%;background:#fff7ed;"></div>

        <div style="width:30%;display:flex;align-items:center;justify-content:center;
            padding:20px;">
            <div style="writing-mode:vertical-rl;letter-spacing:12px;font-size:36px;
                font-weight:900;color:#ea580c;">
                优惠券
            </div>
        </div>

        <div style="border-left:2px dashed #ccc;width:70%;display:flex;flex-direction:column;
            justify-content:center;padding:40px 50px;">
            <div style="font-family:'DisplayBold',sans-serif;font-size:72px;font-weight:900;
                color:#dc2626;line-height:1.2;">
                {headline}
            </div>
            <div style="margin-top:12px;font-size:32px;font-weight:700;color:#374151;">
                {sub_headline}
            </div>
            <div style="margin-top:14px;font-size:22px;color:#6b7280;">
                {labels}
            </div>
        </div>
    </div>

    <div style="margin-top:28px;font-size:28px;font-weight:700;color:#92400e;
        text-align:center;">
        {tagline}
    </div>
</div>"""

    return wrap_page(body, bg="#fff7ed")
