"""线圈笔记本风格 — 浅蓝背景，白色笔记本纸，左侧线圈装饰，右上角回形针，横线纸纹理，蓝色虚线 Logo 区。"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "spiral_notebook",
    "name": "线圈笔记本",
    "desc": "左侧螺旋线圈，横线纸纹理，回形针装饰",
    "tags": ["学生", "文艺", "清新"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])
    primary = theme.get("primary", "#0284c7")
    primary_light = theme.get("primary_light", "#38bdf8")

    grid = brand_grid_html(
        brand_items,
        shape="circle",
        size=130,
        gap=14,
        show_name=False,
        border_color="#bfdbfe",
    )

    spirals = ""
    for i in range(8):
        y = 80 + i * 115
        spirals += (
            f'<div style="position:absolute;left:20px;top:{y}px;'
            "width:30px;height:30px;border:3px solid #b0b0b0;border-radius:50%;"
            'background:linear-gradient(135deg,#e0e0e0,#f8f8f8);z-index:5;"></div>\n'
        )

    body = f"""
<div style="width:1080px;height:1080px;background:{primary_light}30;
    display:flex;align-items:center;justify-content:center;padding:24px;">

    <!-- ===== 笔记本主体 ===== -->
    <div style="width:94%;height:94%;background:#ffffff;position:relative;
        border-radius:4px 18px 18px 4px;
        box-shadow:5px 5px 24px rgba(0,0,0,0.1);
        background-image:repeating-linear-gradient(
            transparent, transparent 35px,
            {primary}12 35px, {primary}12 36px
        );
        background-position:0 42px;
        display:flex;flex-direction:column;
        padding:44px 55px 36px 70px;">

        <!-- 螺旋线圈（左侧 8 个） -->
        {spirals}

        <!-- 右上角回形针 -->
        <div style="position:absolute;top:-8px;right:55px;z-index:10;">
            <svg width="44" height="78" viewBox="0 0 44 78">
                <path d="M22,0 L22,12 Q22,20 14,20 L14,60 Q14,72 22,72
                    Q30,72 30,60 L30,28 Q30,20 22,20 L22,12"
                    fill="none" stroke="#bbb" stroke-width="3.5"/>
            </svg>
        </div>

        <!-- ===== 标题区 (上方 ~37%) ===== -->
        <div style="flex:0 0 auto;display:flex;flex-direction:column;
            padding-bottom:14px;">

            <!-- 主标题：浅蓝色超大粗体 -->
            <div style="margin-bottom:10px;">
                <span style="font-family:'DisplayBold',sans-serif;
                    font-size:76px;font-weight:900;color:{primary};
                    letter-spacing:4px;">
                    {headline}
                </span>
            </div>

            <!-- 标签 -->
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:12px;">
                <span style="font-size:20px;color:{primary};">✓</span>
                <span style="font-size:24px;font-weight:700;color:{primary};
                    letter-spacing:1px;">
                    {labels}
                </span>
            </div>

            <!-- 副标题：蓝色粗体 -->
            <div>
                <span style="font-family:'DisplayBold',sans-serif;
                    font-size:38px;font-weight:800;color:{primary_light};
                    letter-spacing:3px;">
                    {sub_headline}
                </span>
            </div>
        </div>

        <!-- ===== Logo 网格区 (中间 ~48%) ===== -->
        <div style="flex:1;border:2px dashed {primary}35;border-radius:14px;
            padding:18px;display:flex;align-items:center;justify-content:center;">
            {grid}
        </div>

        <!-- ===== 底部标语 (~13%) ===== -->
        <div style="flex:0 0 auto;padding-top:18px;text-align:center;
            display:flex;align-items:center;justify-content:center;gap:16px;">
            <span style="font-size:24px;font-weight:700;color:#555;letter-spacing:2px;">
                {tagline}
            </span>
        </div>
    </div>
</div>"""

    return wrap_page(body, bg=f"{primary_light}30")
