"""tests/test_brand_assets_rename_route_cov100.py — 改名路由测试"""
from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_ctx(asset_id: str, body: dict):
    ctx = MagicMock()
    ctx.path_params = {"asset_id": asset_id}
    ctx.json_body.return_value = body
    return ctx


class TestBrandAssetsRenameRoute:
    def test_rename_success(self):
        """PUT /api/brand-assets/<id> with valid name → 200 ok + asset."""
        ctx = _make_ctx("abc-123", {"name": "顺丰速运"})
        updated = {"id": "abc-123", "name": "顺丰速运", "category": "express",
                   "filename": "abc-123.png", "uploaded_at": "2026-01-01"}
        with patch("src.modules.listing.brand_assets.BrandAssetManager.rename_asset",
                   return_value=updated):
            from src.dashboard.routes.products import handle_brand_assets_rename
            handle_brand_assets_rename(ctx)
        resp = ctx.send_json.call_args[0][0]
        assert resp["ok"] is True
        assert resp["asset"]["name"] == "顺丰速运"

    def test_rename_missing_id_returns_400(self):
        """PUT with empty asset_id → 400."""
        ctx = _make_ctx("", {"name": "顺丰速运"})
        from src.dashboard.routes.products import handle_brand_assets_rename
        handle_brand_assets_rename(ctx)
        assert ctx.send_json.call_args[1].get("status") == 400

    def test_rename_missing_name_returns_400(self):
        """PUT with missing name field → 400."""
        ctx = _make_ctx("abc-123", {})
        from src.dashboard.routes.products import handle_brand_assets_rename
        handle_brand_assets_rename(ctx)
        assert ctx.send_json.call_args[1].get("status") == 400

    def test_rename_blank_name_returns_400(self):
        """PUT with whitespace-only name → 400."""
        ctx = _make_ctx("abc-123", {"name": "   "})
        from src.dashboard.routes.products import handle_brand_assets_rename
        handle_brand_assets_rename(ctx)
        assert ctx.send_json.call_args[1].get("status") == 400

    def test_rename_not_found_returns_404(self):
        """PUT for unknown asset_id → 404."""
        ctx = _make_ctx("unknown", {"name": "顺丰"})
        with patch("src.modules.listing.brand_assets.BrandAssetManager.rename_asset",
                   return_value=None):
            from src.dashboard.routes.products import handle_brand_assets_rename
            handle_brand_assets_rename(ctx)
        assert ctx.send_json.call_args[1].get("status") == 404
