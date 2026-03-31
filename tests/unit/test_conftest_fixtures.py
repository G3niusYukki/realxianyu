from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def test_mock_controller_is_strict_spec(mock_controller):
    assert mock_controller.connect is not None
    with pytest.raises(AttributeError):
        mock_controller.typo_method = AsyncMock()


def test_mock_ai_client_is_strict_spec(mock_ai_client):
    assert mock_ai_client.chat.completions.create is not None
    with pytest.raises(AttributeError):
        mock_ai_client.typo_client = object()
