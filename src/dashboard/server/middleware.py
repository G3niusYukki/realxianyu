"""Dashboard server middleware: CORS, auth helpers."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse


def _normalize_origin(origin: str) -> str:
    parsed = urlparse(str(origin or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    host = parsed.hostname.lower()
    scheme = parsed.scheme.lower()
    port = parsed.port
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if port is None:
        return f"{scheme}://{host}"
    default_port = 80 if scheme == "http" else 443
    if port == default_port:
        return f"{scheme}://{host}"
    return f"{scheme}://{host}:{port}"


def _iter_dashboard_allowed_origins() -> set[str]:
    raw = os.environ.get("DASHBOARD_ALLOWED_ORIGINS", "")
    allowed: set[str] = set()
    for item in raw.split(","):
        normalized = _normalize_origin(item)
        if normalized:
            allowed.add(normalized)
    return allowed


def _is_allowed_dashboard_origin(origin: str) -> bool:
    normalized = _normalize_origin(origin)
    if not normalized:
        return False
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").strip().lower()
    if host in {"127.0.0.1", "localhost", "::1"}:
        return True
    return normalized in _iter_dashboard_allowed_origins()


def _headers_to_dict(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    try:
        items = headers.items()
    except Exception:
        if isinstance(headers, dict):
            items = headers.items()
        else:
            return {}
    result: dict[str, str] = {}
    for key, value in items:
        result[str(key).strip().lower()] = str(value).strip()
    return result


def _extract_dashboard_token(headers: Any) -> str:
    mapped = _headers_to_dict(headers)
    direct = mapped.get("x-dashboard-token", "").strip()
    if direct:
        return direct
    auth = mapped.get("authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


def _check_api_request_access(
    *,
    method: str,
    path: str,
    origin: str,
    headers: Any,
) -> tuple[bool, int, str | None]:
    if not str(path).startswith("/api/"):
        return True, 200, None

    method_upper = str(method or "").upper()
    origin_text = str(origin or "").strip()
    if origin_text and not _is_allowed_dashboard_origin(origin_text):
        return False, 403, "FORBIDDEN_ORIGIN"

    if method_upper in {"POST", "PUT", "DELETE"}:
        expected_token = os.environ.get("DASHBOARD_API_TOKEN", "").strip()
        if expected_token:
            provided_token = _extract_dashboard_token(headers)
            if not provided_token or provided_token != expected_token:
                return False, 401, "UNAUTHORIZED"

    return True, 200, None
