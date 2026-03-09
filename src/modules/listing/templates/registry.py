"""Template registry for frame and composition-based image generation."""

from typing import Any


def render_by_frame(
    frame_id: str,
    category: str,
    params: dict[str, Any] | None = None,
) -> str | None:
    return None


def render_by_composition(
    category: str,
    params: dict[str, Any] | None = None,
    layers: dict[str, str] | None = None,
) -> tuple[str | None, dict[str, str]]:
    return None, {}


def list_frames_metadata() -> list[dict[str, Any]]:
    return []
