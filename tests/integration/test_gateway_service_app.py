from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "gateway-service"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app


def test_gateway_root_returns_service_metadata() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "gateway-service",
        "status": "healthy",
        "health": "/health",
        "docs": "/docs",
    }


def test_gateway_favicon_returns_no_content() -> None:
    client = TestClient(app)

    response = client.get("/favicon.ico")

    assert response.status_code == 204
    assert response.content == b""
