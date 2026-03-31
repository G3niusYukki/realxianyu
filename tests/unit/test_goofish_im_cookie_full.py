"""goofish_im_cookie 模块测试。"""

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.goofish_im_cookie import (
    _TARGET_DOMAINS,
    _KEY_SESSION_COOKIE,
    _MIN_TTL_SECONDS,
    _get_data_dir,
    _is_goofish_im_running,
    _find_best_partition,
    _parse_m_h5_tk_ttl,
    read_goofish_im_cookies,
    merge_cookies,
)


class TestGetDataDir:
    def test_darwin_path(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        monkeypatch.setattr("pathlib.Path.home", lambda: Path("/Users/test"))
        result = _get_data_dir()
        assert result == Path("/Users/test/Library/Application Support/goofish-im")

    def test_windows_path(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setenv("APPDATA", "C:\\Users\\test\\AppData\\Roaming")
        result = _get_data_dir()
        assert "goofish-im" in str(result)

    def test_linux_returns_none(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Linux")
        result = _get_data_dir()
        assert result is None


class TestIsGoofishImRunning:
    def test_darwin_running(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: MagicMock(returncode=0))
        assert _is_goofish_im_running() is True

    def test_darwin_not_running(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Darwin")
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: MagicMock(returncode=1))
        assert _is_goofish_im_running() is False

    def test_windows_running(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: MagicMock(stdout=b"goofish-im.exe\n"),
        )
        assert _is_goofish_im_running() is True

    def test_windows_not_running(self, monkeypatch):
        monkeypatch.setattr("platform.system", lambda: "Windows")
        monkeypatch.setattr(
            "subprocess.run",
            lambda *a, **kw: MagicMock(stdout=b"other.exe\n"),
        )
        assert _is_goofish_im_running() is False

    def test_subprocess_error(self, monkeypatch):
        from unittest.mock import Mock

        monkeypatch.setattr("platform.system", lambda: "Darwin")
        monkeypatch.setattr("subprocess.run", Mock(side_effect=Exception("bad")))
        assert _is_goofish_im_running() is False


class TestFindBestPartition:
    def test_no_dir_returns_none(self, tmp_path):
        assert _find_best_partition(tmp_path) is None

    def test_with_user_id_exact_match(self, tmp_path):
        user_dir = tmp_path / "user123"
        user_dir.mkdir()
        (user_dir / "Cookies").write_text("x", encoding="utf-8")
        result = _find_best_partition(tmp_path, user_id="user123")
        assert result == user_dir / "Cookies"

    def test_with_user_id_no_match(self, tmp_path):
        user_dir = tmp_path / "user123"
        user_dir.mkdir()
        (user_dir / "Cookies").write_text("x", encoding="utf-8")
        result = _find_best_partition(tmp_path, user_id="nonexistent")
        assert result is None

    def test_picks_newest_by_mtime(self, tmp_path):
        old = tmp_path / "111111"
        old.mkdir()
        old_cookies = old / "Cookies"
        old_cookies.write_text("old", encoding="utf-8")
        import time

        time.sleep(0.01)
        new = tmp_path / "222222"
        new.mkdir()
        new_cookies = new / "Cookies"
        new_cookies.write_text("new", encoding="utf-8")
        result = _find_best_partition(tmp_path)
        assert result == new_cookies

    def test_skips_non_numeric_dirs(self, tmp_path):
        numeric = tmp_path / "123456"
        numeric.mkdir()
        (numeric / "Cookies").write_text("x", encoding="utf-8")
        alpha = tmp_path / "abcdef"
        alpha.mkdir()
        (alpha / "Cookies").write_text("x", encoding="utf-8")
        result = _find_best_partition(tmp_path)
        assert result == numeric / "Cookies"


class TestParseMH5TkTtl:
    def test_valid_token(self):
        import time

        future_ts = int((time.time() + 3600) * 1000)
        result = _parse_m_h5_tk_ttl(f"abc_{future_ts}")
        assert result is not None
        assert result > 0

    def test_single_part_returns_none(self):
        assert _parse_m_h5_tk_ttl("just_a_token") is None

    def test_invalid_ts_returns_none(self):
        assert _parse_m_h5_tk_ttl("abc_notanumber") is None

    def test_overflow_produces_valid_float(self):
        import sys

        result = _parse_m_h5_tk_ttl("abc_99999999999999999999999999999")
        assert isinstance(result, float)
        assert result > 0


class TestReadGoofishImCookies:
    def test_no_data_dir(self, monkeypatch):
        monkeypatch.setattr("src.core.goofish_im_cookie._get_data_dir", lambda: None)
        assert read_goofish_im_cookies() is None

    def test_no_partition_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.core.goofish_im_cookie._get_data_dir", lambda: tmp_path)
        assert read_goofish_im_cookies() is None

    def test_reads_valid_cookies(self, tmp_path, monkeypatch):
        import time

        future_ts = int((time.time() + 86400) * 1000)
        partition = tmp_path / "123456"
        partition.mkdir()
        db_path = partition / "Cookies"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE cookies (name TEXT, value TEXT, host_key TEXT)")
        conn.execute("INSERT INTO cookies VALUES ('unb', 'unb_val', '.goofish.com')")
        conn.execute("INSERT INTO cookies VALUES ('sgcookie', 'sg_val', '.goofish.com')")
        conn.execute(f"INSERT INTO cookies VALUES ('_m_h5_tk', 'sig_{future_ts}', '.goofish.com')")
        conn.commit()
        conn.close()

        monkeypatch.setattr("src.core.goofish_im_cookie._get_data_dir", lambda: tmp_path)
        monkeypatch.setattr("src.core.goofish_im_cookie._is_goofish_im_running", lambda: False)
        monkeypatch.setattr("src.core.goofish_im_cookie._find_best_partition", lambda *a, **kw: db_path)
        result = read_goofish_im_cookies(min_ttl=0)
        assert result is not None
        assert "unb_val" in result["cookie_str"]
        assert "sg_val" in result["cookie_str"]
        assert result["source"] == "goofish_im"
        assert result["m_h5_tk_ttl"] is not None

    def test_missing_unb(self, tmp_path, monkeypatch):
        partition = tmp_path / "123456"
        partition.mkdir()
        db_path = partition / "Cookies"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE cookies (name TEXT, value TEXT, host_key TEXT)")
        conn.execute("INSERT INTO cookies VALUES ('sgcookie', 'sg_val', '.goofish.com')")
        conn.commit()
        conn.close()
        monkeypatch.setattr("src.core.goofish_im_cookie._get_data_dir", lambda: tmp_path)
        monkeypatch.setattr("src.core.goofish_im_cookie._find_best_partition", lambda *a, **kw: db_path)
        assert read_goofish_im_cookies() is None

    def test_low_ttl_returns_none(self, tmp_path, monkeypatch):
        import time

        old_ts = int((time.time() - 7200) * 1000)
        partition = tmp_path / "123456"
        partition.mkdir()
        db_path = partition / "Cookies"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE cookies (name TEXT, value TEXT, host_key TEXT)")
        conn.execute("INSERT INTO cookies VALUES ('unb', 'unb_val', '.goofish.com')")
        conn.execute("INSERT INTO cookies VALUES ('sgcookie', 'sg_val', '.goofish.com')")
        conn.execute(f"INSERT INTO cookies VALUES ('_m_h5_tk', 'sig_{old_ts}', '.goofish.com')")
        conn.commit()
        conn.close()
        monkeypatch.setattr("src.core.goofish_im_cookie._get_data_dir", lambda: tmp_path)
        monkeypatch.setattr("src.core.goofish_im_cookie._find_best_partition", lambda *a, **kw: db_path)
        monkeypatch.setattr("src.core.goofish_im_cookie._is_goofish_im_running", lambda: False)
        result = read_goofish_im_cookies(min_ttl=300)
        assert result is None

    def test_filters_non_target_domains(self, tmp_path, monkeypatch):
        partition = tmp_path / "123456"
        partition.mkdir()
        db_path = partition / "Cookies"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE cookies (name TEXT, value TEXT, host_key TEXT)")
        conn.execute("INSERT INTO cookies VALUES ('unb', 'unb_val', '.goofish.com')")
        conn.execute("INSERT INTO cookies VALUES ('sgcookie', 'sg_val', '.goofish.com')")
        conn.execute("INSERT INTO cookies VALUES ('other', 'other_val', '.example.com')")
        conn.commit()
        conn.close()
        monkeypatch.setattr("src.core.goofish_im_cookie._get_data_dir", lambda: tmp_path)
        monkeypatch.setattr("src.core.goofish_im_cookie._find_best_partition", lambda *a, **kw: db_path)
        monkeypatch.setattr("src.core.goofish_im_cookie._is_goofish_im_running", lambda: False)
        result = read_goofish_im_cookies()
        assert result is not None
        assert "other_val" not in result["cookie_str"]
        assert result["cookies"].get("other") is None


class TestMergeCookies:
    def test_im_takes_priority(self):
        existing = "a=1;b=2;c=3"
        im_cookies = {"a": "new_a", "d": "4"}
        result = merge_cookies(im_cookies, existing)
        assert "a=new_a" in result
        assert "b=2" in result
        assert "d=4" in result

    def test_empty_existing(self):
        result = merge_cookies({"x": "1"}, "")
        assert result == "x=1"

    def test_sorted_output(self):
        result = merge_cookies({"z": "1", "a": "2"}, "")
        assert result.startswith("a=2")

    def test_skips_invalid_pairs(self):
        result = merge_cookies({"z": "1"}, "no-equals;key=val")
        assert "no-equals" not in result
        assert "key=val" in result
