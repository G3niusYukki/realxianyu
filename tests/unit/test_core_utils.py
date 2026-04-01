"""
Tests for core crypto and utility modules.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest


class TestCrypto:
    """Tests for crypto module."""

    def test_encrypt_decrypt(self):
        try:
            from src.core.crypto import decrypt, encrypt

            test_data = "test_secret"
            encrypted = encrypt(test_data)
            assert encrypted != test_data

            decrypted = decrypt(encrypted)
            assert decrypted == test_data
        except ImportError:
            pytest.skip("Crypto functions not available")


class TestLogger:
    """Tests for logger module."""

    def test_logger_singleton(self):
        from src.core.logger import Logger

        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2

    def test_logger_instance(self):
        from src.core.logger import Logger

        logger = Logger()
        assert logger is not None


class TestNotify:
    """Tests for notify module."""

    def test_notifier_import(self):
        try:
            from src.core.notify import Notifier

            assert True
        except ImportError:
            pytest.skip("Notifier not available")


class TestCompliance:
    """Tests for compliance module."""

    def test_compliance_center_import(self):
        try:
            from src.modules.compliance.center import ComplianceCenter

            assert True
        except ImportError:
            pytest.skip("ComplianceCenter not available")


class TestPerformance:
    """Tests for performance module."""

    def test_metrics_collector(self):
        try:
            from src.core.performance import MetricsCollector

            collector = MetricsCollector()
            collector.record("test_metric", 100)
            metrics = collector.get_metrics()
            assert "test_metric" in metrics
        except ImportError:
            pytest.skip("MetricsCollector not available")


class TestCoreUtils:
    """Tests for shared core utility helpers."""

    def test_now_iso_uses_local_second_precision_format(self):
        from src.core.utils import now_iso

        value = now_iso()

        assert len(value) == 19
        assert value[4] == "-"
        assert value[7] == "-"
        assert value[10] == "T"
        assert value[13] == ":"
        assert value[16] == ":"

    def test_md5_hex_accepts_str_and_bytes(self):
        from src.core.utils import md5_hex

        assert md5_hex("abc") == "900150983cd24fb0d6963f7d28e17f72"
        assert md5_hex(b"abc") == "900150983cd24fb0d6963f7d28e17f72"

    def test_safe_int_applies_default_and_bounds(self):
        from src.core.utils import safe_int

        assert safe_int(None, default=5, min_value=1, max_value=10) == 5
        assert safe_int("0", default=5, min_value=1, max_value=10) == 1
        assert safe_int("20", default=5, min_value=1, max_value=10) == 10
        assert safe_int("3", default=5, min_value=1, max_value=10) == 3

    def test_run_async_executes_coroutine(self):
        from src.core.utils import run_async

        async def _sample():
            await asyncio.sleep(0)
            return "ok"

        assert run_async(_sample()) == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
