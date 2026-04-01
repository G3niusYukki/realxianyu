"""Shared utility helpers used across core and dashboard modules."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any


def now_iso() -> str:
    """Return local time in second precision for dashboard payloads."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def safe_int(
    value: Any,
    default: int = 0,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Coerce a value to int and optionally clamp it to a range."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default

    if min_value is not None and result < min_value:
        return min_value
    if max_value is not None and result > max_value:
        return max_value
    return result


def run_async(coro: Any) -> Any:
    """Run a coroutine synchronously on an isolated event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
