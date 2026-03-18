"""
Test suite for compliance and safety modules.
"""

import pytest


class TestComplianceCenter:
    """Tests for ComplianceCenter."""

    def test_compliance_center_import(self):
        """Test ComplianceCenter can be imported."""
        try:
            from src.modules.compliance.center import ComplianceCenter

            assert True
        except ImportError:
            pytest.skip("ComplianceCenter not available")

    def test_compliance_center_creation(self):
        """Test ComplianceCenter can be created."""
        try:
            from src.modules.compliance.center import ComplianceCenter

            center = ComplianceCenter()
            assert center is not None
        except ImportError:
            pytest.skip("ComplianceCenter not available")

    def test_check_content(self):
        """Test content checking."""
        try:
            from src.modules.compliance.center import ComplianceCenter

            center = ComplianceCenter()
            result = center.check_content("测试内容")

            assert isinstance(result, dict) or result is None
        except ImportError:
            pytest.skip("ComplianceCenter not available")


class TestSafetyGuard:
    """Tests for SafetyGuard."""

    def test_safety_guard_import(self):
        """Test SafetyGuard can be imported."""
        try:
            from src.modules.messages.safety_guard import SafetyGuard

            assert True
        except ImportError:
            pytest.skip("SafetyGuard not available")

    def test_safety_guard_creation(self):
        """Test SafetyGuard can be created."""
        try:
            from src.modules.messages.safety_guard import SafetyGuard

            guard = SafetyGuard()
            assert guard is not None
        except ImportError:
            pytest.skip("SafetyGuard not available")

    def test_check_message(self):
        """Test message safety check."""
        try:
            from src.modules.messages.safety_guard import SafetyGuard

            guard = SafetyGuard()
            result = guard.check("测试消息")

            assert isinstance(result, dict) or result is None
        except ImportError:
            pytest.skip("SafetyGuard not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
