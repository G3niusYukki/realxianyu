"""Tests for app.main FastAPI application."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestRootEndpoint:
    """Tests for the root endpoint `/`."""

    @pytest.mark.asyncio
    async def test_root_returns_service_info(self) -> None:
        """Root endpoint should return service metadata."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "gateway-service"
        assert data["status"] == "healthy"
        assert data["health"] == "/health"
        assert data["docs"] == "/docs"

    @pytest.mark.asyncio
    async def test_root_uses_json_response(self) -> None:
        """Root endpoint should return JSON Content-Type."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy_status(self) -> None:
        """Health endpoint should return healthy status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "gateway-service"

    @pytest.mark.asyncio
    async def test_health_uses_json_response(self) -> None:
        """Health endpoint should return JSON Content-Type."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestFaviconEndpoint:
    """Tests for the /favicon.ico endpoint."""

    @pytest.mark.asyncio
    async def test_favicon_returns_no_content(self) -> None:
        """Favicon endpoint should return 204 No Content."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/favicon.ico")

        assert response.status_code == 204
