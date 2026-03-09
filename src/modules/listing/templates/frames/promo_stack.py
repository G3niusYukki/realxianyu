from __future__ import annotations
from typing import Any
from ._common import e, brand_grid_html, wrap_page

FRAME_META = {
    "id": "promo_stack",
    "name": "促销信息堆叠",
    "desc": "多层信息堆叠排布，信息密集型促销",
    "tags": ["信息量", "促销", "堆叠"],
}


def render(params: dict[str, Any], theme: dict[str, str]) -> str:
    headline = e(params.get("headline") or theme.get("headline", ""))
    sub_headline = e(params.get("sub_headline") or theme.get("sub_headline", ""))
    labels = e(params.get("labels") or theme.get("labels", ""))
    tagline = e(params.get("tagline") or theme.get("tagline", ""))
    brand_items = params.get("brand_items", [])

    label_pills = "".join(
        f'<span style="display:inline-block;font-size:22px;font-weight:700;color:#92400e;'
        f'background:rgba(255,255,255,0.7);padding:8px 18px;border-radius:999px;'
        f'margin:4px;">{e(l.strip())}</span>'
        for l in (labels or "").split("/") if l.strip()
    ) or '<span style="font-size:22px;color:#92400e;">—</span>'

    grid = brand_grid_html(
        brand_items,
        shape="rounded_square",
        size=120,
        gap=14,
        show_name=True,
        name_color="#fff",
        bg_color="rgba(255,255,255,0.15)",
    )

    body = f'''
<div style="width:1080px;height:1080px;display:flex;flex-direction:column;
    align-items:center;padding:50px 0 60px;
    background:linear-gradient(180deg,#f97316 0%,#ea580c 100%);">

    <div style="width:90%;max-width:972px;display:flex;flex-direction:column;
        gap:28px;align-items:center;">

        <div style="width:100%;height:180px;background:#fff;border-radius:20px;
            box-shadow:0 8px 24px rgba(0,0,0,0.12),0 2px 8px rgba(0,0,0,0.06);
            display:flex;flex-direction:column;justify-content:center;padding:28px 36px;">
            <div style="font-size:56px;font-weight:900;color:#dc2626;line-height:1.2;">
                {headline}
            </div>
            <div style="font-size:28px;font-weight:700;color:#374151;margin-top:10px;">
                {sub_headline}
            </div>
        </div>

        <div style="width:100%;transform:rotate(-1deg);
            background:#fef3c7;border-radius:20px;padding:24px 36px;
            box-shadow:0 8px 24px rgba(0,0,0,0.1),0 2px 8px rgba(0,0,0,0.05);
            display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
            {label_pills}
        </div>

        <div style="width:100%;padding:28px 36px;border-radius:20px;
            background:rgba(255,255,255,0.15);box-shadow:0 6px 20px rgba(0,0,0,0.08);
            display:flex;justify-content:center;align-items:center;">
            {grid}
        </div>

        <div style="width:100%;min-height:100px;background:#1e1e2e;border-radius:20px;
            box-shadow:0 8px 24px rgba(0,0,0,0.2),0 2px 8px rgba(0,0,0,0.1);
            display:flex;align-items:center;justify-content:space-between;
            padding:24px 36px;">
            <span style="font-size:26px;font-weight:700;color:#fff;">{tagline}</span>
            <span style="display:inline-block;font-size:24px;font-weight:900;
                color:#1e1e2e;background:#f97316;padding:14px 32px;border-radius:12px;
                box-shadow:0 4px 12px rgba(249,115,22,0.4);">
                立即购买
            </span>
        </div>
    </div>
</div>'''

    return wrap_page(body, bg="linear-gradient(180deg,#f97316 0%,#ea580c 100%)")
