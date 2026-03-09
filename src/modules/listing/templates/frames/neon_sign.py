"""霓虹灯牌风格 — 深色背景、发光霓虹文字、圆角灯管边框。"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "neon_sign",
    "name": "霓虹灯牌",
    "desc": "深色背景配霓虹发光文字与灯管边框，夜店氛围感",
    "tags": ["酷炫", "夜场", "潮流"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    accent = theme.get("accent", "#00ff88")
    primary = theme.get("primary", "#ff6ec7")

    grid = brand_grid_html(
        brand_items,
        shape="circle",
        size=130,
        gap=16,
        bg_color="rgba(255,255,255,0.08)",
    )

    body = f"""
<div style="width:1080px;height:1080px;position:relative;overflow:hidden;
    background:#0a0a2e;">

    <!-- 砖墙纹理 -->
    <div style="position:absolute;inset:0;opacity:0.12;
        background-image:
            linear-gradient(0deg,transparent 47%,rgba(255,255,255,0.25) 47%,rgba(255,255,255,0.25) 53%,transparent 53%),
            linear-gradient(90deg,transparent 47%,rgba(255,255,255,0.18) 47%,rgba(255,255,255,0.18) 53%,transparent 53%);
        background-size:60px 30px;
        background-position:0 0,30px 15px;
        pointer-events:none;"></div>

    <!-- 环境光晕 -->
    <div style="position:absolute;top:15%;left:50%;width:700px;height:700px;
        transform:translateX(-50%);border-radius:50%;
        background:radial-gradient(circle,rgba(0,255,136,0.06) 0%,transparent 70%);
        pointer-events:none;"></div>

    <!-- 主内容 -->
    <div style="position:relative;z-index:2;width:100%;height:100%;
        display:flex;flex-direction:column;align-items:center;justify-content:center;
        padding:60px 80px;">

        <!-- 主标题：霓虹发光 -->
        <div style="font-family:'DisplayBold',sans-serif;font-size:76px;font-weight:900;
            color:{accent};letter-spacing:4px;text-align:center;line-height:1.15;
            text-shadow:0 0 7px {accent},0 0 10px {accent},0 0 21px {accent},
                0 0 42px {accent}88,0 0 82px {accent}44;">
            {headline}
        </div>

        <!-- 副标题：粉紫霓虹 -->
        <div style="margin-top:18px;font-family:'DisplayBold',sans-serif;font-size:36px;
            font-weight:700;color:{primary};letter-spacing:2px;text-align:center;
            text-shadow:0 0 5px {primary},0 0 10px {primary},0 0 20px {primary}88;">
            {sub_headline}
        </div>

        <!-- 标签 -->
        <div style="margin-top:24px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
            <span style="font-size:18px;color:{accent};letter-spacing:1px;
                background:rgba(0,255,136,0.08);padding:6px 20px;border-radius:4px;
                border:1px solid rgba(0,255,136,0.2);
                text-shadow:0 0 4px {accent};">{labels}</span>
        </div>

        <!-- Logo 区域：发光边框 -->
        <div style="margin-top:36px;padding:30px 40px;border-radius:20px;
            border:2px solid rgba(0,255,136,0.3);
            box-shadow:0 0 8px {accent}44,0 0 20px {accent}22,inset 0 0 8px {accent}11;">
            {grid}
        </div>

        <!-- 底部标语 -->
        <div style="margin-top:32px;font-size:22px;color:rgba(255,255,255,0.55);
            letter-spacing:3px;text-align:center;
            text-shadow:0 0 4px rgba(255,255,255,0.15);">
            ✦ {tagline} ✦
        </div>
    </div>
</div>"""

    return wrap_page(body, bg="#0a0a2e")
