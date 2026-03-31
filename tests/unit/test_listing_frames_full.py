import html

import pytest

from src.modules.listing.templates.frames._common import (
    e,
    brand_grid_html,
    brand_price_list_html,
    wrap_page,
    sample_brand_items,
    _placeholder_logo_svg,
    SQUARE_VIEWPORT,
)


class TestE:
    def test_escapes_html_special_chars(self):
        assert e("<b>bold</b>") == "&lt;b&gt;bold&lt;/b&gt;"

    def test_escapes_ampersand(self):
        assert e("a&b") == "a&amp;b"

    def test_escapes_quotes(self):
        assert e('"hi"') == "&#x27;hi&#x27;" or "&quot;hi&quot;" in e('"hi"')

    def test_none_returns_empty(self):
        assert e(None) == ""

    def test_empty_string(self):
        assert e("") == ""

    def test_normal_string_unchanged(self):
        assert e("hello") == "hello"

    def test_numeric_string(self):
        assert e("123") == "123"


class TestBrandGridHtml:
    def test_empty_items_returns_empty_string(self):
        assert brand_grid_html([]) == ""

    def test_single_item(self):
        items = [{"src": "img.png", "name": "Brand"}]
        result = brand_grid_html(items)
        assert "img.png" in result
        assert "display:grid" in result

    def test_show_name(self):
        items = [{"src": "img.png", "name": "BrandX"}]
        result = brand_grid_html(items, show_name=True)
        assert "BrandX" in result

    def test_circle_shape(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_grid_html(items, shape="circle")
        assert "border-radius:50%" in result

    def test_rounded_square_shape(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_grid_html(items, shape="rounded_square")
        assert "border-radius:16px" in result

    def test_square_shape(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_grid_html(items, shape="square")
        assert "border-radius:4px" in result

    def test_custom_size(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_grid_html(items, size=200)
        assert "width:200px" in result
        assert "height:200px" in result

    def test_custom_gap(self):
        items = [{"src": "a.png", "name": "A"}, {"src": "b.png", "name": "B"}]
        result = brand_grid_html(items, gap=50)
        assert "gap:50px" in result

    def test_max_cols(self):
        items = [{"src": f"{i}.png", "name": str(i)} for i in range(9)]
        result = brand_grid_html(items, max_cols=3)
        assert "grid-template-columns:repeat(3,1fr)" in result

    def test_border_color(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_grid_html(items, border_color="#ff0000")
        assert "border:2px solid #ff0000" in result

    def test_bg_color(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_grid_html(items, bg_color="#eee")
        assert "background:#eee" in result

    def test_limits_to_8_items(self):
        items = [{"src": f"{i}.png", "name": str(i)} for i in range(10)]
        result = brand_grid_html(items)
        count = result.count("<img")
        assert count == 8

    def test_two_items_cols(self):
        items = [{"src": "a.png", "name": "A"}, {"src": "b.png", "name": "B"}]
        result = brand_grid_html(items)
        assert "repeat(2,1fr)" in result

    def test_three_items_cols(self):
        items = [{"src": f"{i}.png", "name": str(i)} for i in range(3)]
        result = brand_grid_html(items)
        assert "repeat(2,1fr)" in result

    def test_five_items_cols(self):
        items = [{"src": f"{i}.png", "name": str(i)} for i in range(5)]
        result = brand_grid_html(items)
        assert "repeat(3,1fr)" in result

    def test_name_font_size_scales(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_grid_html(items, size=200, show_name=True)
        assert "font-size:25px" in result

    def test_name_color(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_grid_html(items, show_name=True, name_color="#123")
        assert "color:#123" in result

    def test_item_without_src(self):
        items = [{"name": "NoImg"}]
        result = brand_grid_html(items)
        assert 'src=""' in result


class TestBrandPriceListHtml:
    def test_empty_items_returns_empty(self):
        assert brand_price_list_html([]) == ""

    def test_basic_render(self):
        items = [{"src": "logo.png", "name": "顺丰", "price": "5元"}]
        result = brand_price_list_html(items)
        assert "顺丰" in result
        assert "5元" in result
        assert "logo.png" in result

    def test_default_price_text(self):
        items = [{"src": "logo.png", "name": "顺丰"}]
        result = brand_price_list_html(items)
        assert "首重3元起" in result

    def test_custom_row_height(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_price_list_html(items, row_height=80)
        assert "height:80px" in result

    def test_custom_font_size(self):
        items = [{"src": "a.png", "name": "A"}]
        result = brand_price_list_html(items, font_size=30)
        assert "font-size:30px" in result

    def test_custom_colors(self):
        items = [{"src": "a.png", "name": "A", "price": "3元"}]
        result = brand_price_list_html(items, text_color="#111", accent_color="#f00", border_color="#ddd")
        assert "color:#111" in result
        assert "color:#f00" in result
        assert "border-bottom:1px solid #ddd" in result

    def test_limits_to_8_items(self):
        items = [{"src": f"{i}.png", "name": str(i)} for i in range(10)]
        result = brand_price_list_html(items)
        assert result.count("<img") == 8


class TestWrapPage:
    def test_basic_wrap(self):
        result = wrap_page("<div>hi</div>")
        assert "<!DOCTYPE html>" in result
        assert "<div>hi</div>" in result
        assert "zh-CN" in result

    def test_custom_dimensions(self):
        result = wrap_page("body", width=800, height=600)
        assert "width: 800px" in result
        assert "height: 600px" in result

    def test_custom_bg(self):
        result = wrap_page("body", bg="#aabbcc")
        assert "background: #aabbcc" in result

    def test_default_dimensions(self):
        result = wrap_page("body")
        assert "width: 1080px" in result
        assert "height: 1080px" in result

    def test_contains_font_face(self):
        result = wrap_page("body")
        assert "@font-face" in result
        assert "DisplayBold" in result

    def test_contains_reset(self):
        result = wrap_page("body")
        assert "margin: 0" in result
        assert "padding: 0" in result


class TestSampleBrandItems:
    def test_returns_list(self):
        items = sample_brand_items()
        assert isinstance(items, list)

    def test_has_10_brands(self):
        items = sample_brand_items()
        assert len(items) == 10

    def test_items_have_name_and_src(self):
        items = sample_brand_items()
        for item in items:
            assert "name" in item
            assert "src" in item
            assert item["src"].startswith("data:image/svg+xml,")


class TestPlaceholderLogoSvg:
    def test_returns_encoded_svg(self):
        from urllib.parse import unquote

        result = _placeholder_logo_svg("SF", "顺丰")
        decoded = unquote(result)
        assert "<svg" in decoded
        assert "SF" in decoded
        assert "顺丰" in decoded

    def test_deterministic(self):
        assert _placeholder_logo_svg("A", "B") == _placeholder_logo_svg("A", "B")


class TestSquareViewport:
    def test_dimensions(self):
        assert SQUARE_VIEWPORT == {"width": 1080, "height": 1080}


FRAME_IDS = [
    "airmail",
    "chat_bubble",
    "clipboard",
    "convenience",
    "coupon_red",
    "glassmorphism",
    "grid_paper",
    "industrial",
    "neon_sign",
    "official_blue",
    "package_box",
    "polaroid",
    "pop_bold",
    "receipt",
    "spiral_notebook",
    "torn_paper",
]


@pytest.fixture(scope="module")
def frames_registry():
    from src.modules.listing.templates.frames import list_frames, get_frame, render_frame

    return list_frames, get_frame, render_frame


class TestFramesRegistry:
    def test_list_frames_returns_all(self, frames_registry):
        list_frames, _, _ = frames_registry
        frames = list_frames()
        ids = {f["id"] for f in frames}
        for fid in FRAME_IDS:
            assert fid in ids

    def test_list_frames_meta_keys(self, frames_registry):
        list_frames, _, _ = frames_registry
        for frame in list_frames():
            assert "id" in frame
            assert "name" in frame
            assert "desc" in frame

    def test_list_frames_no_render_key(self, frames_registry):
        list_frames, _, _ = frames_registry
        for frame in list_frames():
            assert "render" not in frame

    def test_get_frame_existing(self, frames_registry):
        _, get_frame, _ = frames_registry
        frame = get_frame("airmail")
        assert frame is not None
        assert frame["id"] == "airmail"
        assert callable(frame["render"])

    def test_get_frame_missing(self, frames_registry):
        _, get_frame, _ = frames_registry
        assert get_frame("nonexistent_frame") is None

    def test_render_frame_existing(self, frames_registry):
        _, _, render_frame = frames_registry
        params = {"headline": "Test", "sub_headline": "Sub", "labels": "A/B", "tagline": "Tag"}
        html = render_frame("airmail", params, {})
        assert html is not None
        assert "<!DOCTYPE html>" in html
        assert "Test" in html

    def test_render_frame_missing(self, frames_registry):
        _, _, render_frame = frames_registry
        assert render_frame("nonexistent", {}, {}) is None


def _make_params():
    return {
        "headline": "快递代发",
        "sub_headline": "全国3元起",
        "labels": "顺丰/圆通/中通",
        "tagline": "当天发货",
        "brand_items": [
            {"src": "data:image/svg,logo1", "name": "顺丰"},
            {"src": "data:image/svg,logo2", "name": "圆通"},
        ],
    }


class TestFrameModules:
    @pytest.fixture(scope="class")
    def params(self):
        return _make_params()

    @pytest.mark.parametrize("frame_id", FRAME_IDS)
    def test_frame_meta_required_keys(self, frame_id):
        mod = __import__(f"src.modules.listing.templates.frames.{frame_id}", fromlist=["FRAME_META"])
        meta = mod.FRAME_META
        assert "id" in meta
        assert "name" in meta
        assert "desc" in meta
        assert meta["id"] == frame_id

    @pytest.mark.parametrize("frame_id", FRAME_IDS)
    def test_frame_meta_has_tags(self, frame_id):
        mod = __import__(f"src.modules.listing.templates.frames.{frame_id}", fromlist=["FRAME_META"])
        assert "tags" in mod.FRAME_META
        assert isinstance(mod.FRAME_META["tags"], list)
        assert len(mod.FRAME_META["tags"]) > 0

    @pytest.mark.parametrize("frame_id", FRAME_IDS)
    def test_render_returns_valid_html(self, frame_id, params):
        mod = __import__(f"src.modules.listing.templates.frames.{frame_id}", fromlist=["render"])
        result = mod.render(params, {})
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result
        assert "<body>" in result
        assert "快递代发" in result

    @pytest.mark.parametrize("frame_id", FRAME_IDS)
    def test_render_with_empty_params(self, frame_id):
        mod = __import__(f"src.modules.listing.templates.frames.{frame_id}", fromlist=["render"])
        result = mod.render({}, {})
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result

    @pytest.mark.parametrize("frame_id", FRAME_IDS)
    def test_render_with_brand_items(self, frame_id, params):
        mod = __import__(f"src.modules.listing.templates.frames.{frame_id}", fromlist=["render"])
        result = mod.render(params, {})
        assert "data:image/svg,logo1" in result or "logo1" in result

    @pytest.mark.parametrize("frame_id", FRAME_IDS)
    def test_render_1080_dimensions(self, frame_id, params):
        mod = __import__(f"src.modules.listing.templates.frames.{frame_id}", fromlist=["render"])
        result = mod.render(params, {})
        assert "1080px" in result

    @pytest.mark.parametrize("frame_id", FRAME_IDS)
    def test_render_contains_headline(self, frame_id):
        mod = __import__(f"src.modules.listing.templates.frames.{frame_id}", fromlist=["render"])
        result = mod.render({"headline": "UNIQUE_HEADLINE_XYZ"}, {})
        assert "UNIQUE_HEADLINE_XYZ" in result

    @pytest.mark.parametrize("frame_id", FRAME_IDS)
    def test_render_escapes_html(self, frame_id):
        mod = __import__(f"src.modules.listing.templates.frames.{frame_id}", fromlist=["render"])
        result = mod.render({"headline": "<script>alert(1)</script>"}, {})
        assert "<script>" not in result
        assert "&lt;script&gt;" in result


class TestFrameSpecific:
    def test_airmail_contains_parcel_service(self):
        from src.modules.listing.templates.frames import airmail

        result = airmail.render({"headline": "Test"}, {})
        assert "PARCEL SERVICE" in result
        assert "AIRMAIL" in result

    def test_chat_bubble_contains_customer_service(self):
        from src.modules.listing.templates.frames import chat_bubble

        result = chat_bubble.render({"headline": "Test"}, {})
        assert "官方代发客服" in result

    def test_clipboard_contains_metal_clip(self):
        from src.modules.listing.templates.frames import clipboard

        result = clipboard.render({"headline": "Test"}, {})
        assert "e9f5ed" in result

    def test_convenience_contains_express_service(self):
        from src.modules.listing.templates.frames import convenience

        result = convenience.render({"headline": "Test"}, {})
        assert "EXPRESS SERVICE" in result

    def test_coupon_red_contains_limited_offer(self):
        from src.modules.listing.templates.frames import coupon_red

        result = coupon_red.render({"headline": "Test"}, {})
        assert "限时特惠" in result

    def test_glassmorphism_contains_backdrop_filter(self):
        from src.modules.listing.templates.frames import glassmorphism

        result = glassmorphism.render({"headline": "Test"}, {})
        assert "backdrop-filter" in result

    def test_grid_paper_contains_grid_background(self):
        from src.modules.listing.templates.frames import grid_paper

        result = grid_paper.render({"headline": "Test"}, {})
        assert "background-image" in result

    def test_industrial_contains_caution(self):
        from src.modules.listing.templates.frames import industrial

        result = industrial.render({"headline": "Test", "tagline": "小心轻放"}, {})
        assert "CAUTION" in result

    def test_neon_sign_contains_terminal(self):
        from src.modules.listing.templates.frames import neon_sign

        result = neon_sign.render({"headline": "Test"}, {})
        assert "root@system" in result

    def test_official_blue_contains_info_bar(self):
        from src.modules.listing.templates.frames import official_blue

        result = official_blue.render({"headline": "Test"}, {})
        assert "93c5fd" in result

    def test_package_box_contains_shipping_bill(self):
        from src.modules.listing.templates.frames import package_box

        result = package_box.render({"headline": "Test"}, {})
        assert "SHIPPING BILL" in result
        assert "特快" in result

    def test_polaroid_contains_rotation(self):
        from src.modules.listing.templates.frames import polaroid

        result = polaroid.render({"headline": "Test"}, {})
        assert "rotate(2deg)" in result

    def test_pop_bold_contains_stroke(self):
        from src.modules.listing.templates.frames import pop_bold

        result = pop_bold.render({"headline": "Test"}, {})
        assert "text-stroke" in result

    def test_receipt_contains_barcode(self):
        from src.modules.listing.templates.frames import receipt

        result = receipt.render({"headline": "Test"}, {})
        assert "192837465019283" in result

    def test_spiral_notebook_contains_spirals(self):
        from src.modules.listing.templates.frames import spiral_notebook

        result = spiral_notebook.render({"headline": "Test"}, {})
        assert "border-radius:6px" in result

    def test_torn_paper_contains_tape(self):
        from src.modules.listing.templates.frames import torn_paper

        result = torn_paper.render({"headline": "Test"}, {})
        assert "fcc419" in result

    def test_industrial_label_join(self):
        from src.modules.listing.templates.frames import industrial

        result = industrial.render({"labels": "大件/物流/专线"}, {})
        assert "大件 // 物流 // 专线" in result

    def test_polaroid_label_boxes(self):
        from src.modules.listing.templates.frames import polaroid

        result = polaroid.render({"labels": "生活/手作"}, {})
        assert "生活" in result
        assert "手作" in result

    def test_chat_bubble_label_pills(self):
        from src.modules.listing.templates.frames import chat_bubble

        result = chat_bubble.render({"labels": "顺丰/圆通"}, {})
        assert "顺丰" in result
        assert "圆通" in result

    def test_pop_bold_short_label(self):
        from src.modules.listing.templates.frames import pop_bold

        result = pop_bold.render({"sub_headline": "ABCDEFGH"}, {})
        assert "ABCDEF" in result

    def test_receipt_barcode_function(self):
        from src.modules.listing.templates.frames.receipt import _barcode_html

        result = _barcode_html()
        assert "position:relative" in result
        assert "position:absolute" in result

    def test_receipt_barcode_custom_size(self):
        from src.modules.listing.templates.frames.receipt import _barcode_html

        result = _barcode_html(width=300, height=80)
        assert "width:300px" in result
        assert "height:80px" in result
