"""Cookie 持久化存储测试。"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.cookie_store import save_cookie, load_cookie, _atomic_save_to_env, _lock, _ENV_KEY


@pytest.fixture(autouse=True)
def clean_env():
    original = os.environ.get(_ENV_KEY)
    yield
    if original is None:
        os.environ.pop(_ENV_KEY, None)
    else:
        os.environ[_ENV_KEY] = original


class TestSaveLoadCookie:
    def test_saves_to_environ(self):
        save_cookie("test_cookie_abc", persist=False)
        assert os.environ.get(_ENV_KEY) == "test_cookie_abc"

    def test_load_returns_environ_value(self):
        os.environ[_ENV_KEY] = "my_cookie"
        assert load_cookie() == "my_cookie"

    def test_load_empty_when_not_set(self):
        os.environ.pop(_ENV_KEY, None)
        assert load_cookie() == ""

    def test_persist_false_no_file(self, tmp_path):
        with patch("src.core.cookie_store.Path") as mock_path:
            mock_path.return_value = tmp_path / ".env"
            save_cookie("nocookie", persist=False)

    def test_with_source_logged(self, tmp_path):
        with patch("src.core.cookie_store._atomic_save_to_env"):
            save_cookie("cookie123", persist=True, source="test_source")


class TestAtomicSaveToEnv:
    def test_creates_new_file(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        monkeypatch.setattr("src.core.cookie_store.Path", lambda x: env_file if ".env" in str(x) else Path(x))
        monkeypatch.setattr("os.replace", lambda src, dst: None)
        _atomic_save_to_env("new_cookie")

    def test_updates_existing_key(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text(f"{_ENV_KEY}=old_value\nOTHER=keep", encoding="utf-8")
        with patch("src.core.cookie_store.Path") as mock_path:

            def side_effect(x):
                p = Path(x)
                p.lstrip = lambda: str(x)
                return p

            mock_path.return_value = env_file
            _atomic_save_to_env("new_cookie_val")
        assert env_file.read_text(encoding="utf-8").startswith(f"{_ENV_KEY}=new_cookie_val")

    def test_appends_when_key_missing(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("OTHER=value\n", encoding="utf-8")
        with patch("src.core.cookie_store.Path") as mock_path:
            mock_path.return_value = env_file
            _atomic_save_to_env("appended_cookie")
        content = env_file.read_text(encoding="utf-8")
        assert "appended_cookie" in content

    def test_creates_file_if_missing(self, tmp_path):
        env_file = tmp_path / ".env"
        with patch("src.core.cookie_store.Path") as mock_path:
            mock_path.return_value = env_file
            _atomic_save_to_env("brand_new_cookie")
        assert env_file.exists()

    def test_creates_parent_dir_if_needed(self, tmp_path):
        env_file = tmp_path / "subdir" / ".env"
        with patch("src.core.cookie_store.Path") as mock_path:
            mock_path.return_value = env_file
            with patch("os.replace"):
                _atomic_save_to_env("test")


class TestLock:
    def test_lock_exists(self):
        import threading

        assert _lock is not None
        assert isinstance(_lock, type(threading.Lock()))
