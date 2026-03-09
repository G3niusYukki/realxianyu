"""剪贴板风格 — 浅绿格子底纹，纸质剪贴板容器，顶部金属夹子，右上角+底部胶带装饰，圆形 Logo。"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "clipboard",
    "name": "剪贴板",
    "desc": "浅绿格子背景剪贴板，金属夹子与胶带装饰",
    "tags": ["复古", "手工", "温暖"],
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
        brand_items, shape="circle", size=130, gap=14, show_name=False,
    )

    body = f'''
<div style="width:1080px;height:1080px;
    background:#d6e8d0;
    background-image:
        linear-gradient(rgba(255,255,255,0.4) 1px,transparent 1px),
        linear-gradient(90deg,rgba(255,255,255,0.4) 1px,transparent 1px);
    background-size:24px 24px;
    display:flex;align-items:center;justify-content:center;
    position:relative;overflow:hidden;">

    <!-- ===== 剪贴板主体 ===== -->
    <div style="width:86%;height:88%;background:#faf6ed;
        border:3px solid #c5b898;border-radius:20px;position:relative;
        display:flex;flex-direction:column;align-items:center;
        padding:55px 40px 35px;
        box-shadow:3px 5px 18px rgba(0,0,0,0.1);">

        <!-- 金属夹子（凸出顶部） -->
        <div style="position:absolute;top:-28px;left:50%;transform:translateX(-50%);z-index:10;">
            <div style="width:110px;height:55px;
                background:linear-gradient(180deg,#c8a84e,#9a7d2e);
                border-radius:14px 14px 6px 6px;border:2px solid #8b6914;
                display:flex;align-items:center;justify-content:center;">
                <div style="width:24px;height:24px;background:#faf6ed;border-radius:50%;
                    border:3px solid #8b6914;"></div>
            </div>
        </div>

        <!-- 右上角胶带（斜45度半透明） -->
        <div style="position:absolute;top:15px;right:-18px;width:100px;height:30px;
            background:rgba(200,180,120,0.55);transform:rotate(-45deg);
            border:1px solid rgba(180,160,100,0.2);z-index:5;"></div>

        <!-- 底部左侧胶带（斜45度半透明） -->
        <div style="position:absolute;bottom:30px;left:-15px;width:90px;height:28px;
            background:rgba(200,180,120,0.45);transform:rotate(45deg);
            border:1px solid rgba(180,160,100,0.2);z-index:5;"></div>

        <!-- ===== 标题区 (上方 ~36%) ===== -->
        <div style="width:100%;flex:0 0 auto;display:flex;flex-direction:column;
            align-items:center;padding-bottom:12px;">

            <!-- 主标题：深色手写感粗体 -->
            <div style="margin-bottom:10px;">
                <span style="font-family:'DisplayBold',sans-serif;
                    font-size:74px;font-weight:900;color:#2d2d2d;
                    letter-spacing:4px;">
                    {headline}
                </span>
            </div>

            <!-- 标签：金色底色 -->
            <div style="display:inline-flex;align-items:center;gap:6px;
                background:{accent}35;padding:7px 24px;border-radius:22px;
                border:2px solid {accent}60;margin-bottom:10px;">
                <span style="font-size:22px;font-weight:600;color:#5a4a2a;
                    letter-spacing:1px;">
                    {labels}
                </span>
            </div>

            <!-- 副标题小标签 -->
            <div style="display:inline-flex;align-items:center;gap:4px;
                border:2px dashed {primary}50;padding:5px 18px;border-radius:8px;">
                <span style="font-size:20px;font-weight:600;color:{primary};
                    letter-spacing:2px;">
                    · {sub_headline} ·
                </span>
            </div>
        </div>

        <!-- ===== Logo 网格区 (中间 ~50%) ===== -->
        <div style="width:100%;flex:1;display:flex;align-items:center;
            justify-content:center;padding:8px 0;">
            {grid}
        </div>

        <!-- ===== 底部标语 (~12%) ===== -->
        <div style="flex:0 0 auto;padding-top:10px;text-align:center;">
            <span style="font-family:'DisplayBold',sans-serif;
                font-size:32px;font-weight:800;color:#2d2d2d;letter-spacing:4px;">
                ··· {tagline} ···
            </span>
        </div>
    </div>
</div>'''

    return wrap_page(body, bg="#d6e8d0")
