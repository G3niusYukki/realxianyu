"""
Test suite for core error handler module.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.core.error_handler import (
    XianyuError,
    ConfigError,
    BrowserError,
    AIError,
    MediaError,
    AccountError,
    DatabaseError,
    handle_controller_errors,
    handle_operation_errors,
    safe_execute,
)


class TestXianyuError:
    """Tests for XianyuError exceptions."""

    def test_xianyu_error_creation(self):
        """Test XianyuError can be created."""
        error = XianyuError("Test error message")
        assert str(error) == "Test error message"

    def test_config_error_creation(self):
        """Test ConfigError can be created."""
        error = ConfigError("Config error")
        assert isinstance(error, XianyuError)

    def test_browser_error_creation(self):
        """Test BrowserError can be created."""
        error = BrowserError("Browser error")
        assert isinstance(error, XianyuError)

    def test_ai_error_creation(self):
        """Test AIError can be created."""
        error = AIError("AI error")
        assert isinstance(error, XianyuError)

    def test_media_error_creation(self):
        """Test MediaError can be created."""
        error = MediaError("Media error")
        assert isinstance(error, XianyuError)

    def test_account_error_creation(self):
        """Test AccountError can be created."""
        error = AccountError("Account error")
        assert isinstance(error, XianyuError)

    def test_database_error_creation(self):
        """Test DatabaseError can be created."""
        error = DatabaseError("Database error")
        assert isinstance(error, XianyuError)


class TestErrorDecorators:
    """Tests for error handling decorators."""

    def test_handle_controller_errors_decorator(self):
        """Test handle_controller_errors decorator exists."""
        assert callable(handle_controller_errors)

    def test_handle_operation_errors_decorator(self):
        """Test handle_operation_errors decorator exists."""
        assert callable(handle_operation_errors)

    def test_safe_execute_decorator(self):
        """Test safe_execute decorator exists."""
        assert callable(safe_execute)

    def test_controller_error_handler_with_function(self):
        """Test handle_controller_errors with a function."""

        @handle_controller_errors(default_return="fallback")
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result == "fallback"

    def test_operation_error_handler_with_function(self):
        """Test handle_operation_errors with a function."""

        @handle_operation_errors(default_return=False)
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result is False

    def test_safe_execute_with_function(self):
        """Test safe_execute with a function."""

        @safe_execute(default_return="safe")
        def test_func():
            raise ValueError("Test error")

        result = test_func()
        assert result == "safe"

    def test_handle_error_with_context(self):
        """Test handling error with context."""
        handler = ErrorHandler()

        context = {"user_id": "123", "action": "test"}
        result = handler.handle(Exception("Test"), severity=ErrorSeverity.WARNING, context=context)
        assert result is not None


class TestHandleErrorFunction:
    """Tests for standalone handle_error function."""

    def test_handle_error_basic(self):
        """Test basic error handling."""
        try:
            raise RuntimeError("Test runtime error")
        except Exception as e:
            result = handle_error(e)
            assert result is not None

    def test_handle_error_with_severity(self):
        """Test error handling with severity."""
        try:
            raise ValueError("Test value error")
        except Exception as e:
            result = handle_error(e, severity="critical")
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
