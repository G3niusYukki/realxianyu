"""网格纸风格 — 米色网格纸背景，蓝绿色条纹标题栏，方形 Logo 容器（蓝色虚线边框），箭头+点阵装饰。"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "grid_paper",
    "name": "网格纸",
    "desc": "米色网格纸背景，蓝绿条纹标题与方形 Logo",
    "tags": ["复古", "文艺", "简约"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])
    primary = theme.get("primary", "#0284c7")
    accent = theme.get("accent", "#fbbf24")

    grid = brand_grid_html(
        brand_items, shape="rounded_square", size=120, gap=14,
        show_name=False, border_color="#c8d6e5", bg_color="#ffffff",
    )

    dots_top = "".join(
        '<div style="width:6px;height:6px;border-radius:50%;'
        f'background:{primary};opacity:0.35;"></div>'
        for _ in range(22)
    )

    body = f'''
<div style="width:1080px;height:1080px;background:#f5f0e8;
    background-image:
        linear-gradient(rgba(180,170,155,0.25) 1px,transparent 1px),
        linear-gradient(90deg,rgba(180,170,155,0.25) 1px,transparent 1px);
    background-size:30px 30px;
    display:flex;flex-direction:column;align-items:center;
    padding:40px 50px;position:relative;overflow:hidden;">

    <!-- 装饰：顶部圆点行 -->
    <div style="position:absolute;top:22px;left:60px;display:flex;gap:8px;">
        {dots_top}
    </div>
    <!-- 装饰：右上角竖线 -->
    <div style="position:absolute;top:18px;right:55px;width:3px;height:90px;
        background:{primary};opacity:0.35;border-radius:2px;"></div>
    <!-- 装饰：右上角星星 -->
    <div style="position:absolute;top:28px;right:80px;font-size:18px;color:{primary};opacity:0.45;">
        ✦ ✦ ✦
    </div>
    <!-- 装饰：左上角星星 -->
    <div style="position:absolute;top:55px;left:35px;font-size:26px;color:{primary};opacity:0.4;">✦</div>

    <!-- ===== 标题区 (上方 ~38%) ===== -->
    <div style="width:100%;flex:0 0 auto;display:flex;flex-direction:column;
        align-items:center;justify-content:center;padding-top:50px;padding-bottom:16px;">

        <!-- 主标题：黑色粗体 + 浅蓝条状高亮背景 -->
        <div style="position:relative;display:inline-block;margin-bottom:14px;">
            <div style="position:absolute;left:-12px;right:-12px;top:50%;
                height:48px;transform:translateY(-50%);
                background:linear-gradient(90deg,{primary}18,{primary}28,{primary}18);
                border-radius:4px;z-index:0;"></div>
            <span style="position:relative;z-index:1;font-family:'DisplayBold',sans-serif;
                font-size:76px;font-weight:900;color:#1a1a1a;letter-spacing:3px;">
                {headline}
            </span>
        </div>

        <!-- 副标题：蓝绿色条状背景 + 白字 + 箭头 -->
        <div style="display:inline-flex;align-items:center;gap:14px;
            background:linear-gradient(90deg,{primary}cc,{primary}ee,{primary}cc);
            padding:10px 32px;border-radius:4px;">
            <span style="font-family:'DisplayBold',sans-serif;
                font-size:38px;font-weight:800;color:#ffffff;letter-spacing:4px;
                text-shadow:1px 1px 2px rgba(0,0,0,0.15);">
                {sub_headline}
            </span>
            <span style="font-size:30px;color:#ffffff;opacity:0.85;letter-spacing:2px;">
                &gt;&gt;&gt;
            </span>
        </div>

        <!-- 标签 -->
        <div style="margin-top:14px;font-size:20px;font-weight:600;color:#555;
            letter-spacing:2px;">
            {labels}
        </div>
    </div>

    <!-- ===== Logo 网格区 (中间 ~48%) ===== -->
    <div style="width:92%;flex:1;background:#ffffff;border:2px dashed {primary}55;
        border-radius:10px;padding:22px 28px;position:relative;
        display:flex;align-items:center;justify-content:center;">
        <!-- 容器顶部装饰点 -->
        <div style="position:absolute;top:-7px;left:30px;right:30px;
            display:flex;justify-content:center;gap:7px;">
            {"".join(
                '<div style="width:4px;height:4px;border-radius:50%;'
                f'background:{primary};opacity:0.45;"></div>'
                for _ in range(28)
            )}
        </div>
        {grid}
    </div>

    <!-- ===== 底部标语 (~12%) ===== -->
    <div style="flex:0 0 auto;padding-top:20px;padding-bottom:10px;
        display:flex;align-items:center;gap:10px;">
        <span style="font-size:24px;color:#999;letter-spacing:3px;">——</span>
        <span style="font-family:'DisplayBold',sans-serif;
            font-size:32px;font-weight:800;color:#1a1a1a;letter-spacing:5px;">
            {tagline}
        </span>
        <span style="font-size:24px;color:#999;letter-spacing:3px;">——</span>
    </div>

    <!-- 底部装饰箭头 -->
    <div style="position:absolute;bottom:22px;left:50px;
        font-size:14px;color:{primary};opacity:0.35;">◂◂◂◂ ◂◂◂◂</div>
    <div style="position:absolute;bottom:22px;right:50px;
        font-size:14px;color:{primary};opacity:0.35;">▸▸▸▸ ▸▸▸▸</div>
</div>'''

    return wrap_page(body, bg="#f5f0e8")
