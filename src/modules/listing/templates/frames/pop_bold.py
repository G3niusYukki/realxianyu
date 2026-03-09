"""波普大字风格 — 参考图5复刻。
白色背景、超大黄色描边文字、橙色副标题、无容器直铺 Logo。
"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "pop_bold",
    "name": "波普大字",
    "desc": "超大描边文字，大胆配色，无框直铺",
    "tags": ["醒目", "大胆", "年轻"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    grid = brand_grid_html(brand_items, shape="circle", size=150, gap=18)

    body = f"""
<style>
.pop-title {{
    font-family: 'DisplayBold', sans-serif;
    font-size: 120px; font-weight: 900; letter-spacing: 4px;
    color: #fbbf24;
    -webkit-text-stroke: 3px #333;
    text-shadow: 5px 5px 0 rgba(51,51,51,0.15);
    line-height: 1.1;
}}
.pop-sub {{
    font-family: 'DisplayBold', sans-serif;
    font-size: 60px; font-weight: 900;
    color: #fbbf24;
    -webkit-text-stroke: 2px #ea580c;
    text-shadow: 3px 3px 0 rgba(234,88,12,0.2);
    letter-spacing: 3px;
}}
</style>
<div style="width:1080px;height:1080px;background:#ffffff;
    display:flex;flex-direction:column;align-items:center;
    padding:30px 50px;position:relative;overflow:hidden;">

    <!-- 主标题 -->
    <div class="pop-title" style="text-align:center;margin-top:30px;">
        {headline}
    </div>

    <!-- 爆炸标签：橙色底+白字 -->
    <div style="margin-top:10px;display:inline-flex;align-items:center;">
        <span style="background:#ea580c;color:#fff;padding:8px 28px;
            border-radius:24px;font-size:28px;font-weight:800;
            font-family:'DisplayBold',sans-serif;
            box-shadow:3px 3px 8px rgba(0,0,0,0.15);
            transform:rotate(-2deg);display:inline-block;">
            {labels}
        </span>
    </div>

    <!-- 副标题：橙色描边效果 -->
    <div class="pop-sub" style="margin-top:14px;text-align:center;">
        {sub_headline}
    </div>

    <!-- Logo 网格：无修饰直铺 -->
    <div style="margin-top:24px;flex:1;display:flex;align-items:center;
        justify-content:center;width:95%;">
        {grid}
    </div>

    <!-- 长箭头线条 -->
    <div style="width:70%;height:3px;margin-top:16px;position:relative;
        background:linear-gradient(90deg,transparent 0%,#333 10%,#333 90%,transparent 100%);">
        <div style="position:absolute;right:-6px;top:-10px;
            width:0;height:0;border-left:14px solid #333;
            border-top:12px solid transparent;border-bottom:12px solid transparent;"></div>
    </div>

    <!-- 底部标语 -->
    <div style="margin-top:14px;margin-bottom:20px;text-align:center;">
        <span style="font-size:30px;font-weight:800;color:#333;letter-spacing:5px;
            font-family:'DisplayBold',sans-serif;">
            ...{tagline}...
        </span>
    </div>
</div>"""

    return wrap_page(body, bg="#ffffff")
