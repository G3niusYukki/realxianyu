"""小票收据风格 — 白底热敏纸、锯齿边、等宽感文字、条形码装饰。"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "receipt",
    "name": "小票收据",
    "desc": "热敏纸小票风格，锯齿边、单色文字、条形码装饰",
    "tags": ["极简", "趣味", "文艺"],
}


def _barcode_html(width: int = 400, height: int = 60) -> str:
    """用 CSS 模拟条形码黑白竖线。"""
    bars = ""
    pattern = [2, 1, 3, 1, 1, 2, 1, 3, 2, 1, 1, 3, 1, 2, 1, 1, 3, 2, 1, 1, 2, 3, 1, 1, 2, 1, 3, 1]
    x = 0
    for i, w in enumerate(pattern):
        if i % 2 == 0:
            bars += (
                f'<div style="position:absolute;left:{x}px;top:0;width:{w * 2}px;height:100%;'
                f'background:#333;"></div>'
            )
        x += w * 2
    return (
        f'<div style="position:relative;width:{width}px;height:{height}px;'
        f'margin:0 auto;overflow:hidden;">{bars}</div>'
    )


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    grid = brand_grid_html(
        brand_items, shape="rounded_square", size=110, gap=12,
        show_name=True, name_color="#333",
    )

    barcode = _barcode_html(360, 55)
    sep_eq = "= " * 28 + "="
    sep_dash = "- " * 28 + "-"

    body = f'''
<div style="width:1080px;height:1080px;display:flex;align-items:center;justify-content:center;
    background:#e8e8e0;">

    <!-- 小票主体 -->
    <div style="position:relative;width:780px;min-height:960px;background:#fdfdf5;
        box-shadow:0 8px 32px rgba(0,0,0,0.12),0 2px 8px rgba(0,0,0,0.06);
        display:flex;flex-direction:column;align-items:center;padding:0;">

        <!-- 顶部锯齿边 -->
        <div style="width:100%;height:20px;flex-shrink:0;
            background:linear-gradient(135deg,#e8e8e0 33.33%,transparent 33.33%) 0 0,
                linear-gradient(225deg,#e8e8e0 33.33%,transparent 33.33%) 0 0;
            background-size:20px 20px;background-position:top;background-repeat:repeat-x;">
        </div>

        <!-- 内容区 -->
        <div style="width:100%;padding:30px 70px 10px;display:flex;flex-direction:column;
            align-items:center;">

            <!-- 店铺名 / 主标题 -->
            <div style="font-family:'DisplayBold',sans-serif;font-size:74px;font-weight:900;
                color:#1a1a1a;letter-spacing:8px;text-align:center;line-height:1.15;">
                {headline}
            </div>

            <!-- 分隔线 -->
            <div style="margin-top:14px;font-size:14px;color:#999;letter-spacing:0;
                font-family:'Courier New',monospace;white-space:nowrap;overflow:hidden;
                width:100%;text-align:center;">
                {sep_eq}
            </div>

            <!-- 副标题 -->
            <div style="margin-top:14px;font-size:28px;font-weight:700;color:#444;
                letter-spacing:3px;text-align:center;">
                {sub_headline}
            </div>

            <!-- 标签 -->
            <div style="margin-top:12px;">
                <span style="font-size:16px;color:#666;letter-spacing:1px;
                    font-family:'Courier New',monospace;">[{labels}]</span>
            </div>

            <!-- 虚线分隔 -->
            <div style="margin-top:16px;font-size:14px;color:#bbb;letter-spacing:0;
                font-family:'Courier New',monospace;white-space:nowrap;overflow:hidden;
                width:100%;text-align:center;">
                {sep_dash}
            </div>

            <!-- Logo 区域 -->
            <div style="margin-top:20px;width:100%;">
                {grid}
            </div>

            <!-- 虚线分隔 -->
            <div style="margin-top:20px;font-size:14px;color:#bbb;letter-spacing:0;
                font-family:'Courier New',monospace;white-space:nowrap;overflow:hidden;
                width:100%;text-align:center;">
                {sep_dash}
            </div>

            <!-- 标语 -->
            <div style="margin-top:16px;font-size:20px;color:#555;letter-spacing:2px;
                text-align:center;">
                {tagline}
            </div>

            <!-- 条形码 -->
            <div style="margin-top:22px;">
                {barcode}
                <div style="margin-top:6px;font-size:12px;color:#aaa;text-align:center;
                    font-family:'Courier New',monospace;letter-spacing:3px;">
                    8 801234 567890
                </div>
            </div>

            <!-- 感谢语 -->
            <div style="margin-top:20px;margin-bottom:20px;font-size:22px;color:#888;
                letter-spacing:4px;text-align:center;">
                谢谢惠顾 Thank You
            </div>
        </div>

        <!-- 底部锯齿边 -->
        <div style="width:100%;height:20px;flex-shrink:0;margin-top:auto;
            background:linear-gradient(315deg,#e8e8e0 33.33%,transparent 33.33%) 0 0,
                linear-gradient(45deg,#e8e8e0 33.33%,transparent 33.33%) 0 0;
            background-size:20px 20px;background-position:bottom;background-repeat:repeat-x;">
        </div>
    </div>
</div>'''

    return wrap_page(body, bg="#e8e8e0")
