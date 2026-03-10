import base64
import json
import threading

from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from src.core.cookie_grabber import CookieGrabber
from src.dashboard import config_service


def _encrypt_cookiecloud(payload: dict, key: str, salt: bytes) -> str:
    from hashlib import md5

    key_bytes = key.encode("utf-8")
    prev = b""
    derived = b""
    while len(derived) < 48:
        prev = md5(prev + key_bytes + salt).digest()
        derived += prev
    aes_key = derived[:32]
    iv = derived[32:48]

    plaintext = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(b"Salted__" + salt + encrypted).decode("utf-8")


def test_cookiecloud_decrypt_returns_promptly_and_restores_payload() -> None:
    payload = {".goofish.com": [{"name": "_m_h5_tk", "value": "abc_123"}]}
    encrypted = _encrypt_cookiecloud(payload, "unit-test-key", b"12345678")

    result: dict[str, object] = {}

    def run() -> None:
        result["value"] = CookieGrabber._decrypt_cookiecloud(encrypted, "unit-test-key")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(1.0)

    assert thread.is_alive() is False
    assert result["value"] == payload


def test_cookie_cloud_password_is_masked() -> None:
    assert "cookie_cloud_password" in config_service._SENSITIVE_CONFIG_KEYS
