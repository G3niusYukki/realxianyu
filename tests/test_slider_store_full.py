"""SliderEventStore 模块测试。"""

import sqlite3
import threading
import time
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from src.core.slider_store import SliderEventStore


@pytest.fixture()
def store(tmp_path):
    SliderEventStore._instance = None
    s = SliderEventStore(tmp_path / "slider.db")
    yield s
    SliderEventStore._instance = None


class TestInit:
    def test_creates_db(self, tmp_path):
        SliderEventStore._instance = None
        s = SliderEventStore(tmp_path / "new.db")
        assert (tmp_path / "new.db").exists()

    def test_singleton(self, tmp_path):
        SliderEventStore._instance = None
        a = SliderEventStore.get_instance(tmp_path / "s.db")
        b = SliderEventStore.get_instance()
        assert a is b
        SliderEventStore._instance = None

    def test_creates_schema(self, tmp_path):
        SliderEventStore._instance = None
        SliderEventStore(tmp_path / "s.db")
        conn = sqlite3.connect(str(tmp_path / "s.db"))
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        assert "slider_events" in tables


class TestRecordEvent:
    def test_basic_record(self, store):
        rid = store.record_event(result="passed")
        assert rid > 0

    def test_sets_default_trigger_ts(self, store):
        rid = store.record_event(result="passed")
        conn = sqlite3.connect(str(store._db_path))
        row = conn.execute("SELECT trigger_ts FROM slider_events WHERE id=?", (rid,)).fetchone()
        conn.close()
        assert row is not None
        assert row[0] is not None

    def test_custom_fields(self, store):
        rid = store.record_event(
            trigger_ts="2025-01-01T00:00:00Z",
            trigger_source="test",
            result="passed",
            slider_type="nc",
            attempt_num=3,
        )
        conn = sqlite3.connect(str(store._db_path))
        row = conn.execute(
            "SELECT id, trigger_ts, trigger_source, result, slider_type, attempt_num FROM slider_events WHERE id=?",
            (rid,),
        ).fetchone()
        conn.close()
        assert row[0] == rid
        assert row[1] == "2025-01-01T00:00:00Z"
        assert row[2] == "test"
        assert row[3] == "passed"
        assert row[4] == "nc"
        assert row[5] == 3


class TestGetLastCookieApplyTs:
    def test_no_events(self, store):
        assert store.get_last_cookie_apply_ts() is None

    def test_returns_last_cookie_event(self, store):
        store.record_event(trigger_ts="2025-01-01T00:00:00Z", result="passed", cookie_applied=0)
        store.record_event(trigger_ts="2025-01-02T00:00:00Z", result="passed", cookie_applied=1)
        store.record_event(trigger_ts="2025-01-03T00:00:00Z", result="failed", cookie_applied=0)
        assert store.get_last_cookie_apply_ts() == "2025-01-02T00:00:00Z"


class TestGetStats:
    def test_no_events(self, store):
        stats = store.get_stats()
        assert stats["total_triggers"] == 0
        assert stats["success_rate"] == 0.0

    def test_calculates_stats(self, store):
        store.record_event(result="passed", slider_type="nc")
        store.record_event(result="passed", slider_type="nc")
        store.record_event(result="failed", slider_type="nc")
        store.record_event(result="passed", slider_type="puzzle")
        store.record_event(result="failed", slider_type="puzzle")
        stats = store.get_stats()
        assert stats["total_triggers"] == 5
        assert stats["nc_attempts"] == 3
        assert stats["nc_passed"] == 2
        assert stats["puzzle_attempts"] == 2
        assert stats["puzzle_passed"] == 1

    def test_fail_reason_counts(self, store):
        store.record_event(result="failed", fail_reason="timeout")
        store.record_event(result="failed", fail_reason="timeout")
        store.record_event(result="failed", fail_reason="mismatch")
        stats = store.get_stats()
        assert stats["fail_reason_counts"]["timeout"] == 2
        assert stats["fail_reason_counts"]["mismatch"] == 1

    def test_trigger_source_counts(self, store):
        store.record_event(result="passed", trigger_source="ws")
        store.record_event(result="passed", trigger_source="ws")
        store.record_event(result="passed", trigger_source="manual")
        stats = store.get_stats()
        assert stats["trigger_source_counts"]["ws"] == 2
        assert stats["trigger_source_counts"]["manual"] == 1

    def test_screenshots_filtered(self, store):
        store.record_event(result="passed", screenshot_path="/path/screen.png")
        store.record_event(result="passed")
        stats = store.get_stats()
        assert len(stats["screenshots"]) == 1
        assert stats["screenshots"][0]["path"] == "/path/screen.png"

    def test_avg_cookie_ttl(self, store):
        store.record_event(result="passed", cookie_ttl_seconds=300)
        store.record_event(result="passed", cookie_ttl_seconds=500)
        store.record_event(result="passed")
        stats = store.get_stats()
        assert stats["avg_cookie_ttl_seconds"] == 400


class TestGetRecentEvents:
    def test_empty(self, store):
        assert store.get_recent_events() == []

    def test_returns_recent(self, store):
        for i in range(25):
            store.record_event(result="passed")
        events = store.get_recent_events(limit=5)
        assert len(events) == 5


class TestCleanup:
    def test_removes_old(self, store):
        conn = sqlite3.connect(str(store._db_path))
        conn.execute(
            "INSERT INTO slider_events (trigger_ts, result, created_at) VALUES (?,?,?)",
            ("2020-01-01", "passed", "2020-01-01T00:00:00"),
        )
        conn.commit()
        conn.close()
        deleted = store.cleanup_old(days=1)
        assert deleted >= 1

    def test_keeps_recent(self, store):
        store.record_event(result="passed")
        deleted = store.cleanup_old(days=30)
        assert deleted == 0
