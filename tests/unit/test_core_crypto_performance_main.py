import asyncio

import pytest

import src.core.crypto as crypto


def test_crypto_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(crypto, "_KEY_FILE", str(tmp_path / ".k"))

    # derive and env-key path
    monkeypatch.setenv("ENCRYPTION_KEY", "pass")
    key = crypto._get_or_create_key()
    assert isinstance(key, bytes)

    # no cryptography fallback via fake import
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "cryptography.fernet":
            raise ImportError("nope")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    assert crypto.encrypt_value("abc") == "abc"
    assert crypto.decrypt_value("abc") == "abc"

    monkeypatch.setattr("builtins.__import__", real_import)

    # ensure helpers
    assert crypto.is_encrypted("gAAAAA123")
    assert not crypto.is_encrypted("plain")
    assert crypto.ensure_encrypted("") == ""
    assert crypto.ensure_decrypted("") == ""


def test_main_and_module_entry(monkeypatch):
    import src.main as m

    class L:
        def __init__(self):
            self.errors = []
            self.ok = False

        def info(self, *_):
            return None

        def success(self, *_):
            self.ok = True

        def error(self, x):
            self.errors.append(x)

    logger = L()

    class C:
        app = {"name": "n", "version": "v"}

    monkeypatch.setattr("src.main.get_config", lambda: C())
    monkeypatch.setattr("src.main.get_logger", lambda: logger)

    # force one import failure
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name.endswith("accounts.service"):
            raise ImportError("bad")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    asyncio.run(m.main())
    assert logger.errors

    monkeypatch.setattr("builtins.__import__", real_import)
    asyncio.run(m.main())

    hit = {"n": 0}

    def _fake_run(coro):
        hit["n"] += 1
        coro.close()

    monkeypatch.setattr("asyncio.run", _fake_run)
    m.run()
    assert hit["n"] == 1

