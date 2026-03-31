import pytest

from src.modules.listing.templates.layers.base import (
    LayoutOutput,
    ModifierOutput,
    LAYOUT_REGISTRY,
    MODIFIER_REGISTRY,
    register_layout,
    register_modifier,
    list_layouts,
    list_modifiers,
    get_layout,
    get_modifier,
)


class TestLayoutOutput:
    def test_default_values(self):
        out = LayoutOutput(body_html="<div>hi</div>")
        assert out.body_html == "<div>hi</div>"
        assert out.required_css == ""

    def test_with_css(self):
        out = LayoutOutput(body_html="<div>hi</div>", required_css=".x { color: red; }")
        assert out.required_css == ".x { color: red; }"


class TestModifierOutput:
    def test_default_values(self):
        out = ModifierOutput()
        assert out.css_vars == {}
        assert out.css_rules == ""
        assert out.overlay_html == ""

    def test_with_all_fields(self):
        out = ModifierOutput(
            css_vars={"--bg": "#fff"},
            css_rules="body { color: red; }",
            overlay_html="<div>overlay</div>",
        )
        assert out.css_vars == {"--bg": "#fff"}
        assert "color: red" in out.css_rules
        assert "overlay" in out.overlay_html


class TestRegisterLayout:
    def test_register_and_retrieve(self):
        @register_layout("test_layout", name="Test Layout", desc="A test")
        def _test_fn(params, theme):
            return LayoutOutput(body_html="test")

        entry = get_layout("test_layout")
        assert entry is not None
        assert entry["id"] == "test_layout"
        assert entry["name"] == "Test Layout"
        assert entry["desc"] == "A test"
        assert callable(entry["render"])

        del LAYOUT_REGISTRY["test_layout"]


class TestRegisterModifier:
    def test_register_and_retrieve(self):
        @register_modifier("color_scheme", "test_cs", name="Test CS", desc="A test")
        def _test_fn(params, theme):
            return ModifierOutput()

        entry = get_modifier("color_scheme", "test_cs")
        assert entry is not None
        assert entry["id"] == "test_cs"
        assert entry["name"] == "Test CS"

        del MODIFIER_REGISTRY["color_scheme"]["test_cs"]

    def test_valid_kind_no_raise(self):
        register_modifier("color_scheme", "test_xyz_kind", name="TestXYZ")


class TestListLayouts:
    def test_returns_list(self):
        layouts = list_layouts()
        assert isinstance(layouts, list)

    def test_has_expected_layouts(self):
        layouts = list_layouts()
        ids = {l["id"] for l in layouts}
        assert "hero_center" in ids
        assert "split_panel" in ids
        assert "price_rows" in ids
        assert "brand_hero" in ids

    def test_layout_entries_have_required_keys(self):
        for layout in list_layouts():
            assert "id" in layout
            assert "name" in layout
            assert "desc" in layout

    def test_no_render_key_in_list(self):
        for layout in list_layouts():
            assert "render" not in layout


class TestListModifiers:
    def test_returns_dict(self):
        mods = list_modifiers()
        assert isinstance(mods, dict)

    def test_has_all_kinds(self):
        mods = list_modifiers()
        assert "color_scheme" in mods
        assert "decoration" in mods
        assert "title_style" in mods

    def test_filter_by_kind(self):
        mods = list_modifiers(kind="color_scheme")
        assert "color_scheme" in mods
        assert "decoration" not in mods

    def test_color_schemes(self):
        mods = list_modifiers(kind="color_scheme")
        ids = {m["id"] for m in mods["color_scheme"]}
        assert "red_gold" in ids
        assert "dark_neon" in ids
        assert "clean_white" in ids
        assert "warm_gradient" in ids

    def test_decorations(self):
        mods = list_modifiers(kind="decoration")
        ids = {m["id"] for m in mods["decoration"]}
        assert "coupon_edge" in ids
        assert "burst_badge" in ids
        assert "ribbon" in ids
        assert "dot_pattern" in ids
        assert "none" in ids

    def test_title_styles(self):
        mods = list_modifiers(kind="title_style")
        ids = {m["id"] for m in mods["title_style"]}
        assert "bold_impact" in ids
        assert "gradient_text" in ids
        assert "stroke_outline" in ids

    def test_modifier_entries_have_required_keys(self):
        mods = list_modifiers()
        for kind, entries in mods.items():
            for entry in entries:
                assert "id" in entry
                assert "name" in entry
                assert "desc" in entry


class TestGetLayout:
    def test_existing_layout(self):
        layout = get_layout("hero_center")
        assert layout is not None
        assert layout["id"] == "hero_center"
        assert callable(layout["render"])

    def test_missing_layout(self):
        assert get_layout("nonexistent_layout") is None


class TestGetModifier:
    def test_existing_modifier(self):
        mod = get_modifier("color_scheme", "red_gold")
        assert mod is not None
        assert mod["id"] == "red_gold"

    def test_missing_modifier(self):
        assert get_modifier("color_scheme", "nonexistent") is None

    def test_missing_kind(self):
        assert get_modifier("no_such_kind", "anything") is None


class TestColorSchemeModifiers:
    @pytest.mark.parametrize("scheme_id", ["red_gold", "dark_neon", "clean_white", "warm_gradient"])
    def test_returns_modifier_output(self, scheme_id):
        mod = get_modifier("color_scheme", scheme_id)
        result = mod["render"]({}, {})
        assert isinstance(result, ModifierOutput)
        assert "--bg-primary" in result.css_vars
        assert "--text-primary" in result.css_vars
        assert "--text-accent" in result.css_vars

    def test_red_gold_colors(self):
        mod = get_modifier("color_scheme", "red_gold")
        result = mod["render"]({}, {})
        assert result.css_vars["--bg-primary"] == "#dc2626"
        assert result.css_vars["--text-accent"] == "#fbbf24"

    def test_dark_neon_colors(self):
        mod = get_modifier("color_scheme", "dark_neon")
        result = mod["render"]({}, {})
        assert result.css_vars["--bg-primary"] == "#0f172a"
        assert result.css_vars["--text-accent"] == "#22d3ee"

    def test_clean_white_colors(self):
        mod = get_modifier("color_scheme", "clean_white")
        result = mod["render"]({}, {})
        assert result.css_vars["--bg-primary"] == "#ffffff"

    def test_warm_gradient_has_css_rules(self):
        mod = get_modifier("color_scheme", "warm_gradient")
        result = mod["render"]({}, {})
        assert "linear-gradient" in result.css_rules


class TestDecorationModifiers:
    @pytest.mark.parametrize("deco_id", ["coupon_edge", "burst_badge", "ribbon", "dot_pattern", "none"])
    def test_returns_modifier_output(self, deco_id):
        mod = get_modifier("decoration", deco_id)
        result = mod["render"]({}, {})
        assert isinstance(result, ModifierOutput)

    def test_coupon_edge_has_css_rules(self):
        mod = get_modifier("decoration", "coupon_edge")
        result = mod["render"]({}, {})
        assert "mask-image" in result.css_rules

    def test_burst_badge_has_overlay(self):
        mod = get_modifier("decoration", "burst_badge")
        result = mod["render"]({}, {})
        assert "HOT" in result.overlay_html
        assert "position:absolute" in result.overlay_html

    def test_ribbon_has_overlay(self):
        mod = get_modifier("decoration", "ribbon")
        result = mod["render"]({}, {})
        assert "限时特惠" in result.overlay_html

    def test_dot_pattern_has_css_rules(self):
        mod = get_modifier("decoration", "dot_pattern")
        result = mod["render"]({}, {})
        assert "radial-gradient" in result.css_rules

    def test_none_decoration_empty(self):
        mod = get_modifier("decoration", "none")
        result = mod["render"]({}, {})
        assert result.css_vars == {}
        assert result.css_rules == ""
        assert result.overlay_html == ""


class TestTitleStyleModifiers:
    @pytest.mark.parametrize("style_id", ["bold_impact", "gradient_text", "stroke_outline"])
    def test_returns_modifier_output(self, style_id):
        mod = get_modifier("title_style", style_id)
        result = mod["render"]({}, {})
        assert isinstance(result, ModifierOutput)
        assert ".title-text" in result.css_rules

    def test_bold_impact_font_size(self):
        mod = get_modifier("title_style", "bold_impact")
        result = mod["render"]({}, {})
        assert "128px" in result.css_rules

    def test_gradient_text_has_gradient(self):
        mod = get_modifier("title_style", "gradient_text")
        result = mod["render"]({}, {})
        assert "linear-gradient" in result.css_rules
        assert "background-clip" in result.css_rules

    def test_stroke_outline_has_stroke(self):
        mod = get_modifier("title_style", "stroke_outline")
        result = mod["render"]({}, {})
        assert "text-stroke" in result.css_rules
        assert "text-shadow" in result.css_rules


class TestLayoutRenderFunctions:
    @pytest.fixture
    def params(self):
        return {
            "headline": "快递代发",
            "sub_headline": "全国3元起",
            "labels": "顺丰/圆通",
            "tagline": "当天发货",
            "brand_items": [
                {"src": "data:image/svg,logo1", "name": "顺丰"},
                {"src": "data:image/svg,logo2", "name": "圆通"},
            ],
        }

    @pytest.fixture
    def theme(self):
        return {"badge": "代发"}

    @pytest.mark.parametrize("layout_id", ["hero_center", "split_panel", "price_rows", "brand_hero"])
    def test_layout_returns_layout_output(self, layout_id, params, theme):
        layout = get_layout(layout_id)
        result = layout["render"](params, theme)
        assert isinstance(result, LayoutOutput)
        assert len(result.body_html) > 0

    @pytest.mark.parametrize("layout_id", ["hero_center", "split_panel", "price_rows", "brand_hero"])
    def test_layout_output_contains_headline(self, layout_id, params, theme):
        layout = get_layout(layout_id)
        result = layout["render"](params, theme)
        assert "快递代发" in result.body_html

    @pytest.mark.parametrize("layout_id", ["hero_center", "split_panel", "price_rows", "brand_hero"])
    def test_layout_with_empty_params(self, layout_id, theme):
        layout = get_layout(layout_id)
        result = layout["render"]({}, theme)
        assert isinstance(result, LayoutOutput)

    def test_hero_center_contains_title_text_class(self, params, theme):
        layout = get_layout("hero_center")
        result = layout["render"](params, theme)
        assert 'class="title-text"' in result.body_html

    def test_split_panel_contains_grid(self, params, theme):
        layout = get_layout("split_panel")
        result = layout["render"](params, theme)
        assert "grid-template-columns" in result.body_html

    def test_price_rows_contains_price_list(self, params, theme):
        layout = get_layout("price_rows")
        result = layout["render"](params, theme)
        assert "首重3元起" in result.body_html

    def test_brand_hero_has_compact_css(self, params, theme):
        layout = get_layout("brand_hero")
        result = layout["render"](params, theme)
        assert "title-text--compact" in result.required_css

    def test_brand_hero_with_fallback_items(self, theme):
        layout = get_layout("brand_hero")
        result = layout["render"]({}, theme)
        assert "顺丰" in result.body_html


class TestLayersInitImports:
    def test_all_exports(self):
        from src.modules.listing.templates.layers import (
            LAYOUT_REGISTRY,
            MODIFIER_REGISTRY,
            LayoutOutput,
            ModifierOutput,
            list_layouts,
            list_modifiers,
            get_layout,
            get_modifier,
        )

        assert len(LAYOUT_REGISTRY) >= 4
        assert "color_scheme" in MODIFIER_REGISTRY
        assert "decoration" in MODIFIER_REGISTRY
        assert "title_style" in MODIFIER_REGISTRY
