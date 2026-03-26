import pytest

from src.modules.listing.templates.compositor import compose, list_all_options


class TestCompose:
    def test_returns_tuple_of_two(self):
        html, chosen = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert isinstance(html, str)
        assert isinstance(chosen, dict)

    def test_html_is_valid(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<body>" in html
        assert "</html>" in html

    def test_chosen_has_all_keys(self):
        _, chosen = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert chosen["layout"] == "hero_center"
        assert chosen["color_scheme"] == "red_gold"
        assert chosen["decoration"] == "none"
        assert chosen["title_style"] == "bold_impact"

    def test_color_scheme_css_vars_in_html(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert "--bg-primary: #dc2626" in html
        assert "--text-accent: #fbbf24" in html

    def test_title_style_css_in_html(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert "font-size: 128px" in html

    def test_params_in_html(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
            params={"headline": "MY_CUSTOM_HEADLINE"},
        )
        assert "MY_CUSTOM_HEADLINE" in html

    def test_theme_in_html(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
            params={},
            theme={"badge": "MY_BADGE"},
        )
        assert "MY_BADGE" in html

    def test_default_layout_fallback(self):
        html, chosen = compose(
            layout="nonexistent_layout",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert chosen["layout"] == "hero_center"
        assert "<!DOCTYPE html>" in html

    def test_none_params_defaults(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
            params=None,
            theme=None,
        )
        assert "<!DOCTYPE html>" in html

    def test_random_selection(self):
        html, chosen = compose()
        assert chosen["layout"] is not None
        assert chosen["color_scheme"] is not None
        assert chosen["decoration"] is not None
        assert chosen["title_style"] is not None
        assert "<!DOCTYPE html>" in html

    @pytest.mark.parametrize("layout_id", ["hero_center", "split_panel", "price_rows", "brand_hero"])
    def test_all_layouts(self, layout_id):
        html, chosen = compose(
            layout=layout_id,
            color_scheme="clean_white",
            decoration="none",
            title_style="bold_impact",
        )
        assert chosen["layout"] == layout_id
        assert "<!DOCTYPE html>" in html

    @pytest.mark.parametrize("cs_id", ["red_gold", "dark_neon", "clean_white", "warm_gradient"])
    def test_all_color_schemes(self, cs_id):
        html, chosen = compose(
            layout="hero_center",
            color_scheme=cs_id,
            decoration="none",
            title_style="bold_impact",
        )
        assert chosen["color_scheme"] == cs_id
        assert "--bg-primary" in html

    @pytest.mark.parametrize("deco_id", ["coupon_edge", "burst_badge", "ribbon", "dot_pattern", "none"])
    def test_all_decorations(self, deco_id):
        html, chosen = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration=deco_id,
            title_style="bold_impact",
        )
        assert chosen["decoration"] == deco_id

    @pytest.mark.parametrize("ts_id", ["bold_impact", "gradient_text", "stroke_outline"])
    def test_all_title_styles(self, ts_id):
        html, chosen = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style=ts_id,
        )
        assert chosen["title_style"] == ts_id
        assert ".title-text" in html

    def test_overlay_html_included(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="burst_badge",
            title_style="bold_impact",
        )
        assert "HOT" in html

    def test_ribbon_overlay_included(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="ribbon",
            title_style="bold_impact",
        )
        assert "限时特惠" in html

    def test_fallback_color_scheme_when_missing(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="nonexistent_cs_12345",
            decoration="none",
            title_style="bold_impact",
        )
        assert "--bg-primary" in html
        assert "--text-accent" in html

    def test_warm_gradient_css_rules(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="warm_gradient",
            decoration="none",
            title_style="bold_impact",
        )
        assert "linear-gradient" in html

    def test_dot_pattern_css_rules(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="dot_pattern",
            title_style="bold_impact",
        )
        assert "radial-gradient" in html

    def test_width_height_1080(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert "width: 1080px" in html
        assert "height: 1080px" in html

    def test_font_face_included(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert "@font-face" in html
        assert "DisplayBold" in html

    def test_root_css_vars_block(self):
        html, _ = compose(
            layout="hero_center",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert ":root {" in html

    def test_layout_required_css_merged(self):
        html, _ = compose(
            layout="brand_hero",
            color_scheme="red_gold",
            decoration="none",
            title_style="bold_impact",
        )
        assert "title-text--compact" in html


class TestListAllOptions:
    def test_returns_dict(self):
        options = list_all_options()
        assert isinstance(options, dict)

    def test_has_layout_key(self):
        options = list_all_options()
        assert "layout" in options
        assert isinstance(options["layout"], list)

    def test_has_modifier_keys(self):
        options = list_all_options()
        assert "color_scheme" in options
        assert "decoration" in options
        assert "title_style" in options

    def test_layout_count(self):
        options = list_all_options()
        assert len(options["layout"]) >= 4

    def test_color_scheme_count(self):
        options = list_all_options()
        assert len(options["color_scheme"]) >= 4

    def test_decoration_count(self):
        options = list_all_options()
        assert len(options["decoration"]) >= 5

    def test_title_style_count(self):
        options = list_all_options()
        assert len(options["title_style"]) >= 3

    def test_entries_have_id_and_name(self):
        options = list_all_options()
        for key, entries in options.items():
            for entry in entries:
                assert "id" in entry
                assert "name" in entry
