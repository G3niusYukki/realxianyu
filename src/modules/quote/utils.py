"""报价模块共享工具函数。"""
from __future__ import annotations


def format_eta_days(minutes: int | float | None) -> str:
    """将分钟数转换为友好的天数显示（如 "1天"、"2.5天"）。"""
    try:
        raw = float(minutes or 0)
    except (TypeError, ValueError):
        raw = 0.0
    if raw <= 0:
        return "1天"
    days = max(1.0, raw / 1440.0)
    rounded = round(days, 1)
    if abs(rounded - round(rounded)) < 1e-9:
        return f"{round(rounded)}天"
    return f"{rounded:.1f}天"
