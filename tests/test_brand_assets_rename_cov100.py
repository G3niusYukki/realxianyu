"""tests/test_brand_assets_rename_cov100.py — 品牌资产改名测试"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.modules.listing.brand_assets import BrandAssetManager


def _mgr_with_asset(tmp_path: Path) -> tuple[BrandAssetManager, str]:
    """Helper: create manager with one asset, return (mgr, asset_id)."""
    mgr = BrandAssetManager(base_dir=tmp_path)
    asset = mgr.add_asset("顺丰", "express", b"\x89PNG", "png")
    return mgr, asset["id"]


class TestRenameAsset:
    def test_rename_returns_updated_entry(self, tmp_path):
        """rename_asset returns the updated entry with new name."""
        mgr, asset_id = _mgr_with_asset(tmp_path)
        result = mgr.rename_asset(asset_id, "顺丰速运")
        assert result is not None
        assert result["name"] == "顺丰速运"
        assert result["id"] == asset_id

    def test_rename_persists_to_manifest(self, tmp_path):
        """rename_asset updates name in manifest.json on disk."""
        mgr, asset_id = _mgr_with_asset(tmp_path)
        mgr.rename_asset(asset_id, "新品牌")
        entries = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        assert entries[0]["name"] == "新品牌"

    def test_rename_nonexistent_returns_none(self, tmp_path):
        """rename_asset returns None when asset_id not found."""
        mgr = BrandAssetManager(base_dir=tmp_path)
        result = mgr.rename_asset("nonexistent-id", "名字")
        assert result is None

    def test_rename_strips_unsafe_chars(self, tmp_path):
        """rename_asset sanitises the new name (same rules as add_asset)."""
        mgr, asset_id = _mgr_with_asset(tmp_path)
        result = mgr.rename_asset(asset_id, "顺丰<script>")
        assert result is not None
        assert "<" not in result["name"]
        assert "script" not in result["name"]

    def test_rename_empty_name_falls_back_to_unnamed(self, tmp_path):
        """rename_asset with blank name falls back to 'unnamed'."""
        mgr, asset_id = _mgr_with_asset(tmp_path)
        result = mgr.rename_asset(asset_id, "   ")
        assert result is not None
        assert result["name"] == "unnamed"
