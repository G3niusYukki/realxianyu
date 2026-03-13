"""Tests for cookie_grabber module."""

import pytest
from unittest.mock import Mock

from src.core.cookie_grabber import (
    GrabStage,
    GrabProgress,
    GrabResult,
    _GOOFISH_DOMAINS,
    _MY_PAGE_URL,
    _LOGIN_TIMEOUT_MS,
    _AUTH_COOKIES,
    _WEAK_LOGIN_COOKIES,
    _SESSION_COOKIES,
)


class TestConstants:
    def test_grab_stage_enum_values(self):
        from src.core.cookie_grabber import GrabStage

        assert GrabStage.IDLE == "idle"
        assert GrabStage.READING_DB == "reading_db"
        assert GrabStage.SUCCESS == "success"
        assert GrabStage.FAILED == "failed"

    def test_goofish_domains_defined(self):
        assert isinstance(_GOOFISH_DOMAINS, list)
        assert ".goofish.com" in _GOOFISH_DOMAINS

    def test_auth_cookies_defined(self):
        assert isinstance(_AUTH_COOKIES, set)
        assert "unb" in _AUTH_COOKIES

    def test_my_page_url(self):
        assert _MY_PAGE_URL == "https://www.goofish.com/personal"

    def test_login_timeout(self):
        assert _LOGIN_TIMEOUT_MS == 300_000


class TestGrabProgress:
    def test_default_values(self):
        progress = GrabProgress()
        assert progress.stage == GrabStage.IDLE
        assert progress.progress == 0

    def test_custom_values(self):
        progress = GrabProgress(stage=GrabStage.SUCCESS, progress=100)
        assert progress.stage == GrabStage.SUCCESS
        assert progress.progress == 100


class TestGrabResult:
    def test_default_values(self):
        result = GrabResult()
        assert result.ok is False
        assert result.cookie_str == ""

    def test_success_result(self):
        result = GrabResult(ok=True, cookie_str="test")
        assert result.ok is True
        assert result.cookie_str == "test"


class TestCookieGrabber:
    def test_initialization(self):
        from src.core.cookie_grabber import CookieGrabber

        grabber = CookieGrabber()
        assert grabber is not None
        assert grabber.progress.stage == GrabStage.IDLE

    def test_add_listener(self):
        from src.core.cookie_grabber import CookieGrabber

        grabber = CookieGrabber()
        callback = Mock()
        grabber.add_listener(callback)
        assert callback in grabber._listeners

    def test_progress_listener_invoked(self):
        from src.core.cookie_grabber import CookieGrabber, GrabProgress

        progress_received = []

        def listener(progress: GrabProgress):
            progress_received.append(progress)

        grabber = CookieGrabber()
        grabber.add_listener(listener)
        grabber._update(GrabStage.READING_DB, "Testing")
        assert len(progress_received) == 1
        assert progress_received[0].stage == GrabStage.READING_DB

    def test_cancel(self):
        from src.core.cookie_grabber import CookieGrabber, GrabStage

        grabber = CookieGrabber()
        grabber.cancel()
        assert grabber._cancel is True
        assert grabber.progress.stage == GrabStage.CANCELLED


class TestCookieAutoRefresher:
    def test_class_exists(self):
        from src.core.cookie_grabber import CookieAutoRefresher, AutoRefreshStatus

        assert CookieAutoRefresher is not None
        assert AutoRefreshStatus is not None

    def test_initialization(self):
        from src.core.cookie_grabber import CookieAutoRefresher

        refresher = CookieAutoRefresher(interval_minutes=30)
        assert refresher is not None
        assert refresher._interval_minutes == 30

    def test_default_interval(self):
        from src.core.cookie_grabber import CookieAutoRefresher

        refresher = CookieAutoRefresher()
        assert refresher._interval_minutes == 30
