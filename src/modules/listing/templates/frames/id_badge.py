"""工牌吊牌风格 — 浅蓝背景，白色工牌卡片（圆角24px），顶部金属夹子+绳带，黄色超粗标题，圆形 Logo 网格。"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "id_badge",
    "name": "工牌吊牌",
    "desc": "工牌风格白色卡片，金属夹子与绳带，黄色大标题",
    "tags": ["可爱", "卡通", "蓝色"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])
    primary = theme.get("primary", "#0284c7")
    primary_light = theme.get("primary_light", "#38bdf8")
    accent = theme.get("accent", "#fbbf24")

    grid = brand_grid_html(
        brand_items,
        shape="circle",
        size=130,
        gap=16,
        show_name=False,
    )

    body = f"""
<div style="width:1080px;height:1080px;
    background:linear-gradient(180deg,{primary_light}50 0%,{primary}20 100%);
    display:flex;flex-direction:column;align-items:center;
    padding:28px 40px;position:relative;overflow:hidden;">

    <!-- ===== 标题区 (工牌外上方 ~37%) ===== -->
    <div style="width:100%;flex:0 0 auto;display:flex;flex-direction:column;
        align-items:center;justify-content:center;padding-top:20px;padding-bottom:8px;">

        <!-- 主标题：黄色超大字 -->
        <div style="margin-bottom:6px;">
            <span style="font-family:'DisplayBold',sans-serif;
                font-size:72px;font-weight:900;color:{accent};
                text-shadow:3px 3px 0 rgba(0,0,0,0.12);letter-spacing:3px;">
                {headline}
            </span>
        </div>

        <!-- 副标题：黄色大字 -->
        <div style="margin-bottom:10px;">
            <span style="font-family:'DisplayBold',sans-serif;
                font-size:44px;font-weight:800;color:{accent};
                text-shadow:2px 2px 0 rgba(0,0,0,0.08);">
                {sub_headline}
            </span>
        </div>

        <!-- 标签：半透明白底 -->
        <div style="display:inline-flex;align-items:center;gap:8px;
            background:rgba(255,255,255,0.35);padding:6px 22px;border-radius:24px;">
            <span style="font-size:18px;">⭐</span>
            <span style="font-size:21px;font-weight:600;color:#ffffff;letter-spacing:1px;">
                {labels}
            </span>
        </div>
    </div>

    <!-- 绳带 -->
    <div style="width:3px;height:20px;
        background:linear-gradient(180deg,#aaa,#ccc);z-index:10;"></div>

    <!-- ===== 工牌主体 (~50% Logo 区) ===== -->
    <div style="width:88%;flex:1;background:#ffffff;border-radius:24px;
        position:relative;display:flex;flex-direction:column;align-items:center;
        padding:40px 32px 28px;
        box-shadow:0 8px 32px rgba(0,0,0,0.12),0 2px 8px rgba(0,0,0,0.06);">

        <!-- 金属夹子 -->
        <div style="position:absolute;top:-22px;left:50%;transform:translateX(-50%);z-index:10;">
            <div style="width:90px;height:40px;
                background:linear-gradient(180deg,#d4d4d4,#a8a8a8);
                border-radius:10px 10px 4px 4px;border:2px solid #999;
                display:flex;align-items:center;justify-content:center;">
                <div style="width:34px;height:10px;background:#eee;border-radius:5px;"></div>
            </div>
        </div>

        <!-- 工牌内标题 -->
        <div style="text-align:center;margin-bottom:12px;">
            <span style="font-size:22px;font-weight:700;color:{primary};letter-spacing:2px;">
                {sub_headline}
            </span>
        </div>

        <!-- Logo 网格（占据工牌大部分空间） -->
        <div style="flex:1;width:100%;display:flex;align-items:center;justify-content:center;
            padding:8px 0;">
            {grid}
        </div>

        <!-- 工牌底部装饰线 -->
        <div style="width:60%;height:2px;background:linear-gradient(90deg,
            transparent,{primary}30,transparent);margin-top:8px;"></div>
    </div>

    <!-- ===== 底部标语 (~12%) ===== -->
    <div style="flex:0 0 auto;padding-top:16px;padding-bottom:8px;
        display:flex;align-items:center;gap:10px;">
        <span style="font-family:'DisplayBold',sans-serif;
            font-size:26px;font-weight:700;color:#ffffff;letter-spacing:2px;
            text-shadow:1px 1px 2px rgba(0,0,0,0.1);">
            {tagline}
        </span>
        <span style="font-size:22px;color:#ffffff;opacity:0.8;">▸▸▸</span>
    </div>
</div>"""

    return wrap_page(body, bg=f"linear-gradient(180deg,{primary_light}50 0%,{primary}20 100%)")
