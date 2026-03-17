"""装饰框架模板自动发现与注册。"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

_FRAMES: dict[str, dict[str, Any]] = {}


def _discover() -> None:
    """扫描本包下所有模块，注册含 FRAME_META + render 的模块。"""
    if _FRAMES:
        return
    package = importlib.import_module(__package__)
    for info in pkgutil.iter_modules(package.__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__package__}.{info.name}")
        meta = getattr(mod, "FRAME_META", None)
        render_fn = getattr(mod, "render", None)
        if meta and render_fn:
            _FRAMES[meta["id"]] = {**meta, "render": render_fn}


def list_frames() -> list[dict[str, Any]]:
    _discover()
    return [{k: v for k, v in f.items() if k != "render"} for f in _FRAMES.values()]


def get_frame(frame_id: str) -> dict[str, Any] | None:
    _discover()
    return _FRAMES.get(frame_id)


def render_frame(frame_id: str, params: dict, theme: dict) -> str | None:
    _discover()
    frame = _FRAMES.get(frame_id)
    if not frame:
        return None
    return frame["render"](params, theme)
