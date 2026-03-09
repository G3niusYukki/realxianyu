from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "bold_price",
    "name": "大价格标签",
    "desc": "超大价格数字居中，强烈视觉冲击",
    "tags": ["价格", "冲击", "醒目"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels_raw = str(params.get("labels") or theme.get("labels", "") or "")
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    labels_pills = (
        "".join(
            f'<span style="font-size:20px;color:#fbbf24;letter-spacing:1px;'
            f"background:rgba(251,191,36,0.12);padding:8px 22px;border-radius:999px;"
            f'border:2px solid rgba(251,191,36,0.5);margin:0 6px 8px 0;">{e(p.strip())}</span>'
            for p in labels_raw.split(",")
            if p.strip()
        )
        if labels_raw
        else ""
    )

    grid = brand_grid_html(
        brand_items,
        shape="circle",
        size=110,
        gap=16,
        show_name=True,
        name_color="#ddd",
        border_color="rgba(255,255,255,0.2)",
    )

    body = f"""
<div style="width:1080px;height:1080px;position:relative;overflow:hidden;
    background:#1a1a2e;display:flex;flex-direction:column;align-items:center;">

    <div style="position:absolute;top:0;left:0;right:0;height:48px;
        background:linear-gradient(180deg,#dc2626 0%,#b91c1c 50%,#991b1b 100%);
        opacity:0.85;box-shadow:0 4px 12px rgba(0,0,0,0.3);"></div>

    <div style="flex:1;display:flex;flex-direction:column;align-items:center;
        justify-content:center;padding:80px 60px;">

        <div style="font-family:'DisplayBold',sans-serif;font-size:140px;font-weight:900;
            color:#ffffff;letter-spacing:6px;text-align:center;line-height:1.1;
            text-shadow:0 0 20px rgba(255,255,255,0.4),0 0 40px rgba(255,255,255,0.2),
                0 0 60px rgba(255,255,255,0.1);">
            {headline}
        </div>

        <div style="margin-top:20px;font-family:'DisplayBold',sans-serif;font-size:40px;
            font-weight:700;color:#fbbf24;letter-spacing:3px;text-align:center;">
            {sub_headline}
        </div>

        <div style="margin-top:28px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px;">
            {labels_pills if labels_pills else ('<span style="font-size:20px;color:#fbbf24;letter-spacing:1px;background:rgba(251,191,36,0.12);padding:8px 22px;border-radius:999px;border:2px solid rgba(251,191,36,0.5);">' + e(labels_raw) + "</span>")}
        </div>

        <div style="margin-top:40px;">
            {grid}
        </div>

        <div style="margin-top:32px;font-size:24px;color:rgba(255,255,255,0.6);
            letter-spacing:6px;text-align:center;">
            {tagline}
        </div>
    </div>
</div>"""

    return wrap_page(body, bg="#1a1a2e")
