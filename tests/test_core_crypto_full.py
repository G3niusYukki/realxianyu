"""
Test suite for core crypto module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.core.crypto import encrypt_value, decrypt_value, is_encrypted, ensure_encrypted, ensure_decrypted


class TestCryptoEncryptDecrypt:
    """Tests for encryption and decryption functions."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt/decrypt roundtrip works correctly."""
        original = "test_secret_data"
        encrypted = encrypt_value(original)
        assert encrypted != original
        assert isinstance(encrypted, str)

        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        encrypted = encrypt_value("")
        decrypted = decrypt_value(encrypted)
        assert decrypted == ""

    def test_encrypt_unicode(self):
        """Test encryption of unicode characters."""
        original = "中文测试 🎉 émojis"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_long_string(self):
        """Test encryption of long string."""
        original = "A" * 10000
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_different_inputs_produce_different_outputs(self):
        """Test that different inputs produce different encrypted outputs."""
        encrypted1 = encrypt_value("data1")
        encrypted2 = encrypt_value("data2")
        assert encrypted1 != encrypted2

    def test_same_input_produces_different_outputs(self):
        """Test that same input produces different encrypted outputs (with different IV)."""
        encrypted1 = encrypt_value("same_data")
        encrypted2 = encrypt_value("same_data")
        assert encrypted1 != encrypted2


class TestCryptoHelpers:
    """Tests for crypto helper functions."""

    def test_is_encrypted(self):
        """Test checking if value is encrypted."""
        encrypted = encrypt_value("test")
        assert is_encrypted(encrypted) is True
        assert is_encrypted("plain_text") is False

    def test_ensure_encrypted(self):
        """Test ensuring value is encrypted."""
        plain = "test_data"
        encrypted = ensure_encrypted(plain)
        assert is_encrypted(encrypted) is True

    def test_ensure_decrypted(self):
        """Test ensuring value is decrypted."""
        encrypted = encrypt_value("test_data")
        decrypted = ensure_decrypted(encrypted)
        assert decrypted == "test_data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
