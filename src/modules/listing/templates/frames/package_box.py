"""快递纸箱风格 — 牛皮纸底色、虚线裁切框、橡皮章装饰、条形码。"""

from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "package_box",
    "name": "快递纸箱",
    "desc": "牛皮纸底色配虚线裁切框与橡皮章，拆箱感",
    "tags": ["快递", "实用", "趣味"],
}


def _barcode_html(width: int = 500, height: int = 50) -> str:
    """用 CSS 模拟条形码黑白竖线。"""
    bars = ""
    pattern = [3, 1, 2, 1, 1, 3, 1, 2, 3, 1, 1, 2, 1, 3, 1, 1, 2, 1, 3, 2, 1, 1, 3, 1, 2, 1, 1, 2, 3, 1]
    x = 0
    for i, w in enumerate(pattern):
        if i % 2 == 0:
            bars += (
                f'<div style="position:absolute;left:{x}px;top:0;width:{w * 2}px;height:100%;'
                f'background:#1a1a1a;"></div>'
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
        brand_items, shape="rounded_square", size=120, gap=14,
        border_color="#a0845e", bg_color="#fff9f0",
    )

    barcode = _barcode_html(420, 44)

    body = f'''
<div style="width:1080px;height:1080px;position:relative;overflow:hidden;
    background:#c8a86e;">

    <!-- 牛皮纸纹理 -->
    <div style="position:absolute;inset:0;opacity:0.35;
        background-image:
            repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(160,132,94,0.15) 2px,rgba(160,132,94,0.15) 4px),
            repeating-linear-gradient(90deg,transparent,transparent 3px,rgba(120,100,70,0.08) 3px,rgba(120,100,70,0.08) 5px);
        pointer-events:none;"></div>

    <!-- 虚线裁切框 -->
    <div style="position:absolute;top:40px;left:40px;right:40px;bottom:40px;
        border:4px dashed #7a6240;border-radius:6px;pointer-events:none;"></div>

    <!-- 十字裁切标记（四角） -->
    <div style="position:absolute;top:32px;left:50%;width:24px;height:4px;background:#7a6240;transform:translateX(-50%);"></div>
    <div style="position:absolute;bottom:32px;left:50%;width:24px;height:4px;background:#7a6240;transform:translateX(-50%);"></div>
    <div style="position:absolute;left:32px;top:50%;width:4px;height:24px;background:#7a6240;transform:translateY(-50%);"></div>
    <div style="position:absolute;right:32px;top:50%;width:4px;height:24px;background:#7a6240;transform:translateY(-50%);"></div>

    <!-- 橡皮章 -->
    <div style="position:absolute;top:70px;right:90px;width:140px;height:140px;
        border:5px solid #c0392b;border-radius:50%;transform:rotate(-15deg);
        display:flex;align-items:center;justify-content:center;
        box-shadow:inset 0 0 0 3px #c0392b;opacity:0.85;">
        <div style="text-align:center;color:#c0392b;font-family:'DisplayBold',sans-serif;
            font-weight:900;line-height:1.2;">
            <div style="font-size:16px;letter-spacing:2px;">快递代发</div>
            <div style="font-size:11px;margin-top:2px;letter-spacing:1px;">VERIFIED</div>
        </div>
    </div>

    <!-- 易碎品标志 -->
    <div style="position:absolute;bottom:90px;left:80px;font-size:42px;opacity:0.5;
        transform:rotate(-5deg);color:#7a6240;">
        ⚠
    </div>
    <div style="position:absolute;bottom:85px;left:130px;font-size:14px;color:#7a6240;
        transform:rotate(-5deg);letter-spacing:2px;opacity:0.6;">
        轻拿轻放
    </div>

    <!-- 主内容 -->
    <div style="position:relative;z-index:2;width:100%;height:100%;
        display:flex;flex-direction:column;align-items:center;justify-content:center;
        padding:80px 100px;">

        <!-- 主标题 -->
        <div style="font-family:'DisplayBold',sans-serif;font-size:72px;font-weight:900;
            color:#3e2c1a;letter-spacing:3px;text-align:center;line-height:1.15;">
            {headline}
        </div>

        <!-- 副标题 -->
        <div style="margin-top:14px;font-size:30px;font-weight:700;color:#6b5234;
            letter-spacing:2px;text-align:center;">
            {sub_headline}
        </div>

        <!-- 标签 -->
        <div style="margin-top:18px;">
            <span style="font-size:16px;color:#5a4a32;letter-spacing:1px;
                background:rgba(255,255,255,0.5);padding:5px 16px;border-radius:4px;
                border:1px solid #a0845e;">{labels}</span>
        </div>

        <!-- Logo 区域：白底标签贴纸 -->
        <div style="margin-top:30px;background:#fff9f0;padding:24px 32px;
            border:2px solid #a0845e;border-radius:8px;
            box-shadow:2px 3px 8px rgba(0,0,0,0.12);">
            {grid}
        </div>

        <!-- 条形码 + 标语 -->
        <div style="margin-top:28px;text-align:center;">
            {barcode}
            <div style="margin-top:10px;font-size:18px;color:#6b5234;letter-spacing:3px;">
                {tagline}
            </div>
        </div>
    </div>
</div>'''

    return wrap_page(body, bg="#c8a86e")
