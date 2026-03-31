"""消息去重模块测试。"""

import sqlite3
import time
from pathlib import Path

import pytest

from src.modules.messages.dedup import MessageDedup


@pytest.fixture()
def dedup(tmp_path):
    db = tmp_path / "test_dedup.db"
    return MessageDedup(db)


class TestNormalize:
    def test_strips_whitespace(self):
        assert MessageDedup._normalize("  hello  world  ") == "hello world"

    def test_collapses_spaces(self):
        assert MessageDedup._normalize("a   b\t\nc") == "a b c"

    def test_empty(self):
        assert MessageDedup._normalize("") == ""


class TestHash:
    def test_deterministic(self):
        a = MessageDedup._hash("test")
        b = MessageDedup._hash("test")
        assert a == b
        assert len(a) == 32

    def test_different_inputs(self):
        a = MessageDedup._hash("hello")
        b = MessageDedup._hash("world")
        assert a != b


class TestIsDuplicate:
    def test_not_duplicate_initially(self, dedup):
        assert not dedup.is_duplicate("chat1", 1000, "你好")

    def test_duplicate_after_mark(self, dedup):
        dedup.mark_replied("chat1", 1000, "你好", reply="在的")
        assert dedup.is_duplicate("chat1", 1000, "你好")

    def test_different_time_not_duplicate(self, dedup):
        dedup.mark_replied("chat1", 1000, "你好", reply="在的")
        assert not dedup.is_duplicate("chat1", 2000, "你好")

    def test_different_chat_not_duplicate(self, dedup):
        dedup.mark_replied("chat1", 1000, "你好", reply="在的")
        assert not dedup.is_duplicate("chat2", 1000, "你好")


class TestIsContentDuplicate:
    def test_not_duplicate_initially(self, dedup):
        assert not dedup.is_content_duplicate("chat1", "多少钱")

    def test_duplicate_after_mark(self, dedup):
        dedup.mark_replied("chat1", 1000, "多少钱", reply="10元")
        assert dedup.is_content_duplicate("chat1", "多少钱")

    def test_window_expired(self, dedup):
        dedup.mark_replied("chat1", 1000, "多少钱", reply="10元")
        # Negative window = everything is expired
        assert not dedup.is_content_duplicate("chat1", "多少钱", window_seconds=-1)

    def test_normalized_content_match(self, dedup):
        dedup.mark_replied("chat1", 1000, "多少钱", reply="10元")
        # Same normalized content matches
        assert dedup.is_content_duplicate("chat1", "多少钱")


class TestIsReplied:
    def test_layer1_hit(self, dedup):
        dedup.mark_replied("chat1", 1000, "hi", reply="hello")
        assert dedup.is_replied("chat1", 1000, "hi")

    def test_layer2_hit(self, dedup):
        dedup.mark_replied("chat1", 1000, "价格", reply="10元")
        # Different create_time but same content
        assert dedup.is_replied("chat1", 2000, "价格")

    def test_no_hit(self, dedup):
        assert not dedup.is_replied("chat1", 1000, "新消息")


class TestMarkReplied:
    def test_writes_both_tables(self, dedup):
        dedup.mark_replied("chat1", 1000, "测试", reply="回复")
        conn = sqlite3.connect(str(dedup.db_path))
        mr = conn.execute("SELECT * FROM message_replies").fetchone()
        cr = conn.execute("SELECT * FROM content_replies").fetchone()
        conn.close()
        assert mr is not None
        assert cr is not None

    def test_idempotent_insert(self, dedup):
        dedup.mark_replied("chat1", 1000, "测试", reply="回复1")
        dedup.mark_replied("chat1", 1000, "测试", reply="回复2")
        conn = sqlite3.connect(str(dedup.db_path))
        count = conn.execute("SELECT COUNT(*) FROM message_replies").fetchone()[0]
        conn.close()
        assert count == 1

    def test_content_count_increments(self, dedup):
        dedup.mark_replied("chat1", 1000, "测试", reply="r1")
        dedup.mark_replied("chat1", 2000, "测试", reply="r2")
        conn = sqlite3.connect(str(dedup.db_path))
        row = conn.execute("SELECT count FROM content_replies").fetchone()
        conn.close()
        assert row[0] == 2


class TestReplyDedup:
    def test_not_duplicate_initially(self, dedup):
        assert not dedup.is_reply_duplicate("chat1", "好的亲")

    def test_duplicate_after_mark(self, dedup):
        dedup.mark_reply_sent("chat1", "好的亲")
        assert dedup.is_reply_duplicate("chat1", "好的亲")

    def test_window_expired(self, dedup):
        dedup.mark_reply_sent("chat1", "好的亲")
        assert not dedup.is_reply_duplicate("chat1", "好的亲", window_seconds=-1)

    def test_different_reply_not_duplicate(self, dedup):
        dedup.mark_reply_sent("chat1", "好的亲")
        assert not dedup.is_reply_duplicate("chat1", "收到")


class TestCleanup:
    def test_removes_old_records(self, dedup):
        # Insert with a very old replied_at
        conn = sqlite3.connect(str(dedup.db_path))
        conn.execute(
            "INSERT OR REPLACE INTO message_replies (message_hash, chat_id, content, create_time, reply, replied_at) VALUES (?,?,?,?,?,?)",
            ("old_hash", "chat1", "旧消息", 1000, "回复", "2020-01-01T00:00:00"),
        )
        conn.execute(
            "INSERT OR REPLACE INTO content_replies (content_hash, chat_id, content, reply, first_at, last_at, count) VALUES (?,?,?,?,?,?,?)",
            ("old_ch", "chat1", "旧消息", "回复", "2020-01-01T00:00:00", "2020-01-01T00:00:00", 1),
        )
        conn.commit()
        conn.close()
        total = dedup.cleanup(days=30)
        assert total >= 1

    def test_no_records_to_clean(self, dedup):
        total = dedup.cleanup(days=30)
        assert total == 0


class TestInitDb:
    def test_creates_tables(self, tmp_path):
        db = tmp_path / "init_test.db"
        MessageDedup(db)
        conn = sqlite3.connect(str(db))
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        assert "message_replies" in tables
        assert "content_replies" in tables
        assert "reply_dedup" in tables
