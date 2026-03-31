"""tests/test_bargain_tracker_cov100.py — 议价追踪模块测试"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.modules.messages.bargain_tracker import BargainTracker, get_bargain_tracker


@pytest.fixture
def tracker(tmp_path: Path) -> BargainTracker:
    return BargainTracker(db_path=str(tmp_path / "bargain.db"))


class TestIsBargainMessage:
    @pytest.mark.parametrize("msg,expected", [
        ("能不能便宜点", True),
        ("便宜一点行不行", True),
        ("打折吗", True),
        ("最低多少钱", True),
        ("能少点吗", True),
        ("hello", False),
        ("寄快递", False),
        ("", False),
        (None, False),
    ])
    def test_is_bargain_message(self, msg, expected):
        assert BargainTracker.is_bargain_message(msg) == expected


class TestGetDynamicReply:
    def test_first_bargain_returns_first_reply(self, tracker):
        reply = tracker.get_dynamic_reply("session-1")
        assert "比自寄省一半" in reply
        assert tracker.get_count("session-1") == 1

    def test_second_bargain_returns_second_reply(self, tracker):
        tracker.get_dynamic_reply("session-1")
        reply = tracker.get_dynamic_reply("session-1")
        assert "首单价已经是最低了" in reply
        assert tracker.get_count("session-1") == 2

    def test_third_bargain_returns_third_reply(self, tracker):
        for _ in range(2):
            tracker.get_dynamic_reply("session-1")
        reply = tracker.get_dynamic_reply("session-1")
        assert "别的快递" in reply
        assert tracker.get_count("session-1") == 3

    def test_fourth_plus_bargain_returns_fourth_reply(self, tracker):
        for _ in range(3):
            tracker.get_dynamic_reply("session-1")
        reply = tracker.get_dynamic_reply("session-1")
        assert "先拍下不付款" in reply
        assert tracker.get_count("session-1") == 4

    def test_different_sessions_independent(self, tracker):
        r1 = tracker.get_dynamic_reply("s1")
        r2 = tracker.get_dynamic_reply("s2")
        assert r1 == r2  # both first reply
        assert tracker.get_count("s1") == 1
        assert tracker.get_count("s2") == 1


class TestReset:
    def test_reset_clears_count(self, tracker):
        tracker.get_dynamic_reply("session-x")
        assert tracker.get_count("session-x") == 1
        tracker.reset("session-x")
        assert tracker.get_count("session-x") == 0

    def test_after_reset_starts_from_first(self, tracker):
        tracker.get_dynamic_reply("session-x")
        tracker.get_dynamic_reply("session-x")
        tracker.reset("session-x")
        reply = tracker.get_dynamic_reply("session-x")
        assert "比自寄省一半" in reply
        assert tracker.get_count("session-x") == 1


class TestGetBargainTrackerSingleton:
    def test_returns_same_instance(self, monkeypatch, tmp_path: Path):
        # Reset singleton
        import src.modules.messages.bargain_tracker as bt
        bt._tracker = None
        t1 = get_bargain_tracker()
        t2 = get_bargain_tracker()
        assert t1 is t2
        # Restore
        bt._tracker = None
