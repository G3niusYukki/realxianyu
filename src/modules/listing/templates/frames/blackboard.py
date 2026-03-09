"""黑板粉笔风格 — 原创设计。
深绿色黑板背景、白色粉笔字效果、粉笔线条边框、木质外框。
"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "blackboard",
    "name": "黑板粉笔",
    "desc": "教室黑板风格，粉笔字与木质边框",
    "tags": ["复古", "教室", "粉笔"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    grid = brand_grid_html(
        brand_items, shape="circle", size=130, gap=14,
        border_color="rgba(255,255,255,0.3)",
    )

    body = f'''
<div style="width:1080px;height:1080px;position:relative;display:flex;
    align-items:center;justify-content:center;
    background:linear-gradient(135deg,#1e3326 0%,#2d4a3e 50%,#1e3326 100%);">

    <!-- 木质外框 -->
    <div style="position:absolute;inset:20px;border:12px solid #8B6914;
        border-radius:4px;
        box-shadow:inset 0 0 20px rgba(0,0,0,0.3),
            4px 4px 16px rgba(0,0,0,0.4),
            -2px -2px 8px rgba(0,0,0,0.2);
        background:linear-gradient(135deg,
            rgba(139,105,20,0.15) 0%,rgba(139,105,20,0.05) 100%);">

        <!-- 黑板主体 -->
        <div style="position:absolute;inset:8px;
            background:linear-gradient(160deg,#234536 0%,#2d4a3e 40%,#1e3a30 100%);
            border-radius:2px;overflow:hidden;
            box-shadow:inset 0 0 60px rgba(0,0,0,0.2);
            display:flex;flex-direction:column;align-items:center;
            padding:50px 60px 30px;">

            <!-- 细微噪点纹理 -->
            <div style="position:absolute;inset:0;opacity:0.04;
                background-image:
                    radial-gradient(circle,#fff 1px,transparent 1px);
                background-size:8px 8px;pointer-events:none;"></div>

            <!-- 主标题：白色粉笔字 -->
            <div style="position:relative;z-index:1;text-align:center;margin-top:10px;">
                <span style="font-family:'DisplayBold',sans-serif;
                    font-size:76px;font-weight:900;color:#f5f5e8;
                    text-shadow:0 0 3px rgba(255,255,255,0.5),
                        2px 2px 4px rgba(0,0,0,0.3);
                    letter-spacing:5px;">
                    {headline}
                </span>
            </div>

            <!-- 标签：粉笔方括号 -->
            <div style="position:relative;z-index:1;text-align:center;margin-top:12px;">
                <span style="font-family:'DisplayBold',sans-serif;
                    font-size:26px;color:#d4e0c8;
                    text-shadow:0 0 3px rgba(255,255,255,0.4);
                    letter-spacing:3px;">
                    [ {labels} ]
                </span>
            </div>

            <!-- 副标题：黄色粉笔字 -->
            <div style="position:relative;z-index:1;text-align:center;margin-top:14px;">
                <span style="font-family:'DisplayBold',sans-serif;
                    font-size:38px;font-weight:700;color:#fbbf24;
                    text-shadow:0 0 3px rgba(251,191,36,0.5),
                        1px 1px 2px rgba(0,0,0,0.3);
                    letter-spacing:4px;">
                    {sub_headline}
                </span>
            </div>

            <!-- 粉笔线条分隔 -->
            <div style="position:relative;z-index:1;width:60%;height:2px;margin:20px 0;
                background:linear-gradient(90deg,
                    transparent 0%,rgba(255,255,255,0.4) 15%,
                    rgba(255,255,255,0.5) 50%,
                    rgba(255,255,255,0.4) 85%,transparent 100%);"></div>

            <!-- Logo 区域：白色虚线边框 -->
            <div style="position:relative;z-index:1;flex:1;display:flex;
                align-items:center;justify-content:center;
                width:88%;
                border:2px dashed rgba(255,255,255,0.35);
                border-radius:8px;padding:20px;">
                {grid}
            </div>

            <!-- 底部粉笔线条装饰 -->
            <div style="position:relative;z-index:1;width:80%;margin-top:18px;
                display:flex;align-items:center;gap:12px;">
                <div style="flex:1;height:1px;
                    background:linear-gradient(90deg,transparent,rgba(255,255,255,0.35));"></div>
                <span style="font-size:14px;color:rgba(255,255,255,0.4);">&#9674;</span>
                <div style="flex:2;height:2px;
                    background:linear-gradient(90deg,
                        rgba(255,255,255,0.45),rgba(255,255,255,0.2),rgba(255,255,255,0.45));"></div>
                <span style="font-size:14px;color:rgba(255,255,255,0.4);">&#9674;</span>
                <div style="flex:1;height:1px;
                    background:linear-gradient(90deg,rgba(255,255,255,0.35),transparent);"></div>
            </div>

            <!-- 底部标语 -->
            <div style="position:relative;z-index:1;text-align:center;margin-top:14px;
                margin-bottom:10px;">
                <span style="font-family:'DisplayBold',sans-serif;
                    font-size:28px;color:#c8d4b8;
                    text-shadow:0 0 3px rgba(255,255,255,0.4);
                    letter-spacing:5px;">
                    {tagline}
                </span>
            </div>
        </div>
    </div>
</div>'''

    return wrap_page(body, bg="#1e3326")
