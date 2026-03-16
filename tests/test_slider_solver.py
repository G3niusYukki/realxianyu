"""Tests for slider_solver module."""

import platform
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.core.slider_solver import (
    _AUTH_COOKIES,
    _GOOFISH_DOMAINS,
    _GOOFISH_IM_URL,
    _SLIDER_GONE_SELECTORS,
    NC_SLIDER_SELECTORS,
    NC_SUCCESS_MARKERS,
    NC_TRACK_SELECTORS,
    PUZZLE_SELECTORS,
    _get_slider_config,
    _has_display,
    generate_human_trajectory,
)


class TestConstants:
    """Test module constants are properly defined."""

    def test_nc_slider_selectors_defined(self):
        """NC slider selectors should be a non-empty list."""
        assert isinstance(NC_SLIDER_SELECTORS, list)
        assert len(NC_SLIDER_SELECTORS) > 0
        assert all(isinstance(s, str) for s in NC_SLIDER_SELECTORS)
        assert "#nc_1_n1z" in NC_SLIDER_SELECTORS

    def test_nc_track_selectors_defined(self):
        """NC track selectors should be a non-empty list."""
        assert isinstance(NC_TRACK_SELECTORS, list)
        assert len(NC_TRACK_SELECTORS) > 0
        assert all(isinstance(s, str) for s in NC_TRACK_SELECTORS)

    def test_puzzle_selectors_defined(self):
        """Puzzle selectors should be a non-empty list."""
        assert isinstance(PUZZLE_SELECTORS, list)
        assert len(PUZZLE_SELECTORS) > 0
        assert all(isinstance(s, str) for s in PUZZLE_SELECTORS)

    def test_nc_success_markers_defined(self):
        """NC success markers should be a non-empty list."""
        assert isinstance(NC_SUCCESS_MARKERS, list)
        assert len(NC_SUCCESS_MARKERS) > 0
        assert "验证通过" in NC_SUCCESS_MARKERS
        assert "success" in NC_SUCCESS_MARKERS

    def test_slider_gone_selectors_defined(self):
        """Slider gone selectors should be a non-empty list."""
        assert isinstance(_SLIDER_GONE_SELECTORS, list)
        assert len(_SLIDER_GONE_SELECTORS) > 0

    def test_auth_cookies_defined(self):
        """Auth cookies should be a non-empty set."""
        assert isinstance(_AUTH_COOKIES, set)
        assert len(_AUTH_COOKIES) > 0
        assert "unb" in _AUTH_COOKIES
        assert "cookie2" in _AUTH_COOKIES

    def test_goofish_urls_defined(self):
        """Goofish URLs should be properly defined."""
        assert _GOOFISH_IM_URL == "https://www.goofish.com/im"
        assert isinstance(_GOOFISH_DOMAINS, list)
        assert ".goofish.com" in _GOOFISH_DOMAINS
        assert ".taobao.com" in _GOOFISH_DOMAINS


class TestHasDisplay:
    """Test _has_display function."""

    def test_darwin_returns_true(self):
        """macOS should always return True."""
        with patch("platform.system", return_value="Darwin"):
            assert _has_display() is True

    def test_windows_returns_true(self):
        """Windows should always return True."""
        with patch("platform.system", return_value="Windows"):
            assert _has_display() is True

    def test_linux_with_display(self):
        """Linux with DISPLAY env should return True."""
        with patch("platform.system", return_value="Linux"):
            with patch.dict("os.environ", {"DISPLAY": ":0"}, clear=True):
                assert _has_display() is True

    def test_linux_with_wayland(self):
        """Linux with WAYLAND_DISPLAY env should return True."""
        with patch("platform.system", return_value="Linux"):
            with patch.dict("os.environ", {"WAYLAND_DISPLAY": "wayland-1"}, clear=True):
                assert _has_display() is True

    def test_linux_no_display(self):
        """Linux without display env should return False."""
        with patch("platform.system", return_value="Linux"):
            with patch.dict("os.environ", {}, clear=True):
                assert _has_display() is False


class TestGetSliderConfig:
    """Test _get_slider_config function."""

    def test_default_config(self):
        """Default config should have expected values."""
        config = _get_slider_config(None)
        assert config["enabled"] is False
        assert config["max_attempts"] == 2
        assert config["cooldown_seconds"] == 300
        assert config["headless"] is False

    def test_custom_config(self):
        """Custom config should override defaults."""
        config = _get_slider_config(
            {
                "slider_auto_solve": {
                    "enabled": True,
                    "max_attempts": 5,
                    "cooldown_seconds": 600,
                    "headless": True,
                }
            }
        )
        assert config["enabled"] is True
        assert config["max_attempts"] == 5
        assert config["cooldown_seconds"] == 600
        assert config["headless"] is True

    def test_partial_config(self):
        """Partial config should use defaults for missing values."""
        config = _get_slider_config(
            {
                "slider_auto_solve": {
                    "enabled": True,
                }
            }
        )
        assert config["enabled"] is True
        assert config["max_attempts"] == 2  # default
        assert config["cooldown_seconds"] == 300  # default

    def test_invalid_slider_config_type(self):
        """Invalid slider config type should return defaults."""
        config = _get_slider_config({"slider_auto_solve": "invalid"})
        assert config["enabled"] is False
        assert config["max_attempts"] == 2


class TestGenerateHumanTrajectory:
    """Test generate_human_trajectory function."""

    def test_returns_list_of_tuples(self):
        """Should return a list of (dx, dy, dt) tuples."""
        trajectory = generate_human_trajectory(100)
        assert isinstance(trajectory, list)
        assert len(trajectory) > 0
        for point in trajectory:
            assert isinstance(point, tuple)
            assert len(point) == 3
            dx, dy, dt = point
            assert isinstance(dx, int)
            assert isinstance(dy, int)
            assert isinstance(dt, int)

    def test_total_distance_approximate(self):
        """Total horizontal distance should approximate target."""
        distance = 100
        trajectory = generate_human_trajectory(distance)
        total_dx = sum(point[0] for point in trajectory)
        # Allow some variance due to randomness
        assert abs(total_dx - distance) <= 5

    def test_duration_in_reasonable_range(self):
        """Total duration should be in reasonable range (800-3000ms)."""
        trajectory = generate_human_trajectory(100)
        total_time = sum(point[2] for point in trajectory)
        assert 800 <= total_time <= 3000

    def test_vertical_jitter_present(self):
        """Should have some vertical jitter."""
        trajectory = generate_human_trajectory(100)
        dys = [point[1] for point in trajectory]
        # At least some points should have non-zero dy
        assert any(dy != 0 for dy in dys)

    def test_small_distance(self):
        """Should handle small distances."""
        trajectory = generate_human_trajectory(10)
        assert len(trajectory) > 0
        total_dx = sum(point[0] for point in trajectory)
        assert abs(total_dx - 10) <= 2

    def test_large_distance(self):
        """Should handle large distances."""
        trajectory = generate_human_trajectory(300)
        assert len(trajectory) > 0
        total_dx = sum(point[0] for point in trajectory)
        assert abs(total_dx - 300) <= 10


class TestHelperFunctions:
    """Test helper functions."""

    def test_generate_human_trajectory_edge_cases(self):
        """Test edge cases for trajectory generation."""
        # Zero distance
        result = generate_human_trajectory(0)
        assert isinstance(result, list)

        # Negative distance (should handle gracefully)
        result = generate_human_trajectory(-10)
        assert isinstance(result, list)

    def test_get_slider_config_with_empty_dict(self):
        """Empty dict should return defaults."""
        config = _get_slider_config({})
        assert config["enabled"] is False
        assert config["max_attempts"] == 2

    def test_get_slider_config_with_nested_empty_dict(self):
        """Nested empty dict should return defaults."""
        config = _get_slider_config({"slider_auto_solve": {}})
        assert config["enabled"] is False
        assert config["max_attempts"] == 2


class TestCookieExtraction:
    """Test cookie extraction functions."""

    def test_extract_goofish_cookies_with_valid_cookies(self):
        """Should extract goofish cookies."""
        from src.core.slider_solver import _extract_goofish_cookies

        cookies = [
            {"name": "unb", "value": "12345" + "x" * 50, "domain": ".goofish.com"},
            {"name": "cookie2", "value": "abcde" + "y" * 50, "domain": ".taobao.com"},
        ]
        result = _extract_goofish_cookies(cookies)
        assert result is not None
        assert "unb=" in result
        assert "cookie2=" in result

    def test_extract_goofish_cookies_with_no_goofish_cookies(self):
        """Should return None if no goofish cookies."""
        from src.core.slider_solver import _extract_goofish_cookies

        cookies = [
            {"name": "session", "value": "xyz", "domain": ".example.com"},
        ]
        result = _extract_goofish_cookies(cookies)
        assert result is None

    def test_extract_goofish_cookies_too_short(self):
        """Should return None if cookie string too short."""
        from src.core.slider_solver import _extract_goofish_cookies

        cookies = [{"name": "x", "value": "y", "domain": ".goofish.com"}]
        result = _extract_goofish_cookies(cookies)
        assert result is None

    def test_has_login_cookies_with_auth_cookie(self):
        """Should detect login cookies."""
        from src.core.slider_solver import _has_login_cookies

        cookies = [{"name": "unb", "value": "12345"}]
        assert _has_login_cookies(cookies) is True

    def test_has_login_cookies_with_cookie2(self):
        """Should detect cookie2."""
        from src.core.slider_solver import _has_login_cookies

        cookies = [{"name": "cookie2", "value": "abcde"}]
        assert _has_login_cookies(cookies) is True

    def test_has_login_cookies_no_auth(self):
        """Should return False if no auth cookies."""
        from src.core.slider_solver import _has_login_cookies

        cookies = [{"name": "random", "value": "value"}]
        assert _has_login_cookies(cookies) is False

    def test_has_login_cookies_empty(self):
        """Should handle empty cookies."""
        from src.core.slider_solver import _has_login_cookies

        assert _has_login_cookies([]) is False
