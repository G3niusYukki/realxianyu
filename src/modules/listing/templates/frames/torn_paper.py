"""撕纸拼贴风格 — 参考图6复刻。
深蓝色纹理背景、白色撕纸拼贴、右上角胶带、金色标签。
"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "torn_paper",
    "name": "撕纸拼贴",
    "desc": "深蓝纹理背景配撕边白纸，胶带装饰，金色标签",
    "tags": ["潮流", "拼贴", "个性"],
}

_TORN_CLIP = (
    "polygon("
    "0 3%, 5% 0, 10% 2%, 15% 0, 20% 3%, 25% 0, 30% 2%, 35% 0, "
    "40% 3%, 45% 0, 50% 2%, 55% 0, 60% 3%, 65% 0, 70% 2%, 75% 0, "
    "80% 3%, 85% 0, 90% 2%, 95% 0, 100% 3%, "
    "100% 97%, 95% 100%, 90% 98%, 85% 100%, 80% 97%, 75% 100%, "
    "70% 98%, 65% 100%, 60% 97%, 55% 100%, 50% 98%, 45% 100%, "
    "40% 97%, 35% 100%, 30% 98%, 25% 100%, 20% 97%, 15% 100%, "
    "10% 98%, 5% 100%, 0 97%)"
)


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])
    accent = theme.get("accent", "#d4a017")

    grid = brand_grid_html(brand_items, shape="circle", size=140, gap=16)

    body = f'''
<div style="width:1080px;height:1080px;position:relative;overflow:hidden;
    background:linear-gradient(160deg,#0c2340 0%,#1a3a5c 40%,#0f2d4a 100%);">

    <!-- 深蓝纸质纹理叠层 -->
    <div style="position:absolute;inset:0;opacity:0.06;
        background-image:repeating-linear-gradient(
            0deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px
        );"></div>

    <!-- 右上角胶带（45度斜贴） -->
    <div style="position:absolute;top:60px;right:80px;width:120px;height:36px;
        background:linear-gradient(135deg,rgba(255,245,200,0.75),rgba(240,230,180,0.55));
        transform:rotate(45deg);z-index:20;
        box-shadow:0 1px 4px rgba(0,0,0,0.15);"></div>

    <!-- 主标题区（背景上方） -->
    <div style="position:relative;z-index:2;text-align:center;padding-top:50px;">
        <div style="display:inline-flex;align-items:center;gap:16px;flex-wrap:wrap;
            justify-content:center;">
            <span style="font-family:'DisplayBold',sans-serif;font-size:100px;
                font-weight:900;color:#c0392b;line-height:1.1;
                text-shadow:3px 3px 6px rgba(0,0,0,0.3);">
                {headline}
            </span>
            <span style="background:{accent};color:#333;font-size:24px;
                font-weight:800;padding:8px 22px;border-radius:6px;
                font-family:'DisplayBold',sans-serif;
                box-shadow:2px 2px 8px rgba(0,0,0,0.25);
                transform:rotate(-3deg);display:inline-block;">
                {labels}
            </span>
        </div>
    </div>

    <!-- 蓝色副标题 -->
    <div style="position:relative;z-index:2;text-align:center;margin-top:10px;">
        <span style="font-family:'DisplayBold',sans-serif;font-size:34px;
            font-weight:700;color:#7ec8e3;letter-spacing:4px;">
            {sub_headline}
        </span>
    </div>

    <!-- 撕纸白纸区域 -->
    <div style="position:relative;z-index:2;margin:24px 60px 0;
        background:#ffffff;clip-path:{_TORN_CLIP};
        padding:40px 50px 45px;
        box-shadow:0 8px 30px rgba(0,0,0,0.3);">

        <!-- Logo 网格 -->
        <div style="display:flex;align-items:center;justify-content:center;
            min-height:320px;">
            {grid}
        </div>
    </div>

    <!-- 底部标语 -->
    <div style="position:relative;z-index:2;text-align:center;margin-top:24px;">
        <span style="font-size:28px;font-weight:700;color:rgba(255,255,255,0.85);
            letter-spacing:5px;font-family:'DisplayBold',sans-serif;">
            ···{tagline}···
        </span>
    </div>
</div>'''

    return wrap_page(body, bg="#0c2340")
