"""QuoteLedger 模块测试。"""

import json
import sqlite3
import time
from pathlib import Path

import pytest

from src.modules.quote.ledger import QuoteLedger, get_quote_ledger


@pytest.fixture()
def ledger(tmp_path):
    db = tmp_path / "test_ledger.db"
    l = QuoteLedger(db)
    # Reset singleton so other tests get fresh instances
    QuoteLedger._instance = None
    yield l


class TestQuoteLedgerInit:
    def test_creates_db_and_schema(self, tmp_path):
        db = tmp_path / "new.db"
        l = QuoteLedger(db)
        assert db.exists()
        conn = sqlite3.connect(str(db))
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        assert "quote_records" in tables

    def test_singleton(self, tmp_path):
        db = tmp_path / "single.db"
        QuoteLedger._instance = None
        a = QuoteLedger.get_instance(db)
        b = QuoteLedger.get_instance()
        assert a is b
        QuoteLedger._instance = None


class TestRecordQuote:
    def test_basic_record(self, ledger):
        rid = ledger.record_quote(
            session_id="s1",
            peer_name="买家A",
            item_id="item1",
            quote_rows=[{"courier": "圆通", "total_fee": 12.5}],
        )
        assert rid > 0

    def test_empty_quote_rows(self, ledger):
        rid = ledger.record_quote(session_id="s2", peer_name="买家B")
        assert rid > 0

    def test_all_fields(self, ledger):
        rid = ledger.record_quote(
            session_id="s3",
            peer_name="买家C",
            sender_user_id="eid123",
            item_id="item99",
            origin="上海",
            destination="北京",
            weight=3.5,
            courier_choice="顺丰",
            quote_rows=[{"courier": "顺丰", "total_fee": 25.0}],
        )
        assert rid > 0


class TestFindByBuyer:
    def test_find_by_peer_name(self, ledger):
        ledger.record_quote(session_id="s1", peer_name="张三", item_id="i1")
        result = ledger.find_by_buyer("张三")
        assert result is not None
        assert result["peer_name"] == "张三"

    def test_find_with_item_id(self, ledger):
        ledger.record_quote(session_id="s1", peer_name="李四", item_id="i1")
        ledger.record_quote(session_id="s2", peer_name="李四", item_id="i2")
        result = ledger.find_by_buyer("李四", item_id="i2")
        assert result["item_id"] == "i2"

    def test_find_by_sender_user_id_fallback(self, ledger):
        ledger.record_quote(session_id="s1", peer_name="王五", sender_user_id="eid999")
        result = ledger.find_by_buyer("不存在的买家", sender_user_id="eid999")
        assert result is not None
        assert result["sender_user_id"] == "eid999"

    def test_not_found(self, ledger):
        result = ledger.find_by_buyer("无人知晓")
        assert result is None

    def test_max_age_filters_old(self, ledger):
        ledger.record_quote(session_id="s1", peer_name="过期用户")
        result = ledger.find_by_buyer("过期用户", max_age_seconds=-1)
        assert result is None

    def test_returns_most_recent(self, ledger):
        ledger.record_quote(session_id="s1", peer_name="赵六", courier_choice="韵达")
        time.sleep(0.01)
        ledger.record_quote(session_id="s2", peer_name="赵六", courier_choice="圆通")
        result = ledger.find_by_buyer("赵六")
        assert result["courier_choice"] == "圆通"

    def test_quote_rows_deserialized(self, ledger):
        rows = [{"courier": "中通", "total_fee": 10.0}]
        ledger.record_quote(session_id="s1", peer_name="孙七", quote_rows=rows)
        result = ledger.find_by_buyer("孙七")
        assert result["quote_rows"] == rows


class TestFindBySession:
    def test_found(self, ledger):
        ledger.record_quote(session_id="sess_abc", peer_name="测试")
        result = ledger.find_by_session("sess_abc")
        assert result is not None
        assert result["session_id"] == "sess_abc"

    def test_not_found(self, ledger):
        result = ledger.find_by_session("nonexistent")
        assert result is None


class TestCleanup:
    def test_removes_old_records(self, ledger):
        ledger.record_quote(session_id="s1", peer_name="旧")
        deleted = ledger.cleanup(max_age_seconds=-1)
        assert deleted >= 1
        assert ledger.find_by_session("s1") is None

    def test_keeps_recent(self, ledger):
        ledger.record_quote(session_id="s1", peer_name="新")
        deleted = ledger.cleanup(max_age_seconds=3600)
        assert deleted == 0
        assert ledger.find_by_session("s1") is not None


class TestRowToDict:
    def test_valid_json(self):
        row = {"id": 1, "session_id": "s", "quote_rows_json": '[{"a":1}]'}
        result = QuoteLedger._row_to_dict(row)
        assert result["quote_rows"] == [{"a": 1}]

    def test_invalid_json(self):
        row = {"id": 1, "session_id": "s", "quote_rows_json": "not json"}
        result = QuoteLedger._row_to_dict(row)
        assert result["quote_rows"] == []

    def test_missing_key(self):
        row = {"id": 1, "session_id": "s"}
        result = QuoteLedger._row_to_dict(row)
        assert result["quote_rows"] == []


class TestGetQuoteLedger:
    def test_returns_singleton(self, tmp_path):
        QuoteLedger._instance = None
        db = tmp_path / "singleton.db"
        a = get_quote_ledger(db)
        b = get_quote_ledger()
        assert a is b
        QuoteLedger._instance = None
