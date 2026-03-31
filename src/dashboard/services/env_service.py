"""Environment variable read/write service."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class EnvService:
    """Handles .env file and environment variable operations."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    @property
    def env_path(self) -> Path:
        return self.project_root / ".env"

    @property
    def logs_dir(self) -> Path:
        return self.project_root / "logs"

    @property
    def cookie_plugin_dir(self) -> Path:
        return self.project_root / "third_party" / "Get-cookies.txt-LOCALLY"

    def _read_env_lines(self) -> list[str]:
        if not self.env_path.exists():
            return []
        return self.env_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    def _get_env_value(self, key: str) -> str:
        key_norm = f"{key}="
        for line in self._read_env_lines():
            if line.startswith(key_norm):
                return line[len(key_norm) :]
        return os.getenv(key, "")

    def _set_env_value(self, key: str, value: str) -> None:
        key_norm = f"{key}="
        lines = self._read_env_lines()
        updated = False
        for idx, line in enumerate(lines):
            if line.startswith(key_norm):
                lines[idx] = f"{key}={value}"
                updated = True
                break
        if not updated:
            lines.append(f"{key}={value}")
        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        self.env_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
        os.environ[key] = value

    @staticmethod
    def _to_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        text = str(value or "").strip().lower()
        if not text:
            return default
        return text in {"1", "true", "yes", "on", "enabled"}

    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        raw = self._get_env_value(key)
        return self._to_bool(raw, default=default)
