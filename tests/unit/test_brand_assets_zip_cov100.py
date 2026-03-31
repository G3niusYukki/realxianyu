"""tests/test_brand_assets_zip_cov100.py — ZIP 批量上传接口测试"""
from __future__ import annotations

import io
import zipfile
from unittest.mock import MagicMock, patch


def _make_zip(files: dict[str, bytes]) -> bytes:
    """Helper: build an in-memory zip from {filename: content} mapping."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def _make_ctx(zip_data: bytes, category: str = "express"):
    """Build a minimal mock RouteContext carrying multipart zip data."""
    import email.message

    # Build raw multipart body
    boundary = b"testboundary"
    body = (
        b"--testboundary\r\n"
        b'Content-Disposition: form-data; name="file"; filename="logos.zip"\r\n'
        b"Content-Type: application/zip\r\n\r\n"
        + zip_data
        + b"\r\n--testboundary\r\n"
        b'Content-Disposition: form-data; name="category"\r\n\r\n'
        + category.encode()
        + b"\r\n--testboundary--\r\n"
    )
    headers = email.message.Message()
    headers["Content-Type"] = f"multipart/form-data; boundary=testboundary"
    headers["Content-Length"] = str(len(body))

    mock_handler = MagicMock()
    mock_handler.rfile = io.BytesIO(body)

    ctx = MagicMock()
    ctx.headers = headers
    ctx._handler = mock_handler
    ctx._handler.rfile = io.BytesIO(body)
    return ctx


class TestUploadZipSuccess:
    def test_imports_two_png_images(self):
        """Two valid PNG files in zip → imported=2, skipped=0, errors=[]."""
        zip_data = _make_zip({
            "顺丰.png": b"\x89PNG fake",
            "中通.png": b"\x89PNG fake2",
        })
        ctx = _make_ctx(zip_data, category="express")

        with patch("src.modules.listing.brand_assets.BrandAssetManager.add_asset") as mock_add:
            mock_add.return_value = {"id": "abc", "name": "顺丰", "category": "express",
                                     "filename": "abc.png", "uploaded_at": "2026-01-01"}
            from src.dashboard.routes.products import handle_brand_assets_upload_zip
            handle_brand_assets_upload_zip(ctx)

        ctx.send_json.assert_called_once()
        resp = ctx.send_json.call_args[0][0]
        assert resp["ok"] is True
        assert resp["imported"] == 2
        assert resp["skipped"] == 0
        assert resp["errors"] == []


class TestUploadZipEdgeCases:
    def test_non_zip_returns_400(self):
        """Non-zip file → 400 with error message."""
        ctx = _make_ctx(b"this is not a zip", category="express")
        from src.dashboard.routes.products import handle_brand_assets_upload_zip
        handle_brand_assets_upload_zip(ctx)
        ctx.send_json.assert_called_once()
        call_args = ctx.send_json.call_args
        assert call_args[1].get("status") == 400

    def test_missing_file_field_returns_400(self):
        """Missing file field in multipart → 400."""
        import email.message
        body = (
            b"--testboundary\r\n"
            b'Content-Disposition: form-data; name="category"\r\n\r\n'
            b"express\r\n--testboundary--\r\n"
        )
        headers = email.message.Message()
        headers["Content-Type"] = "multipart/form-data; boundary=testboundary"
        headers["Content-Length"] = str(len(body))
        mock_handler = MagicMock()
        mock_handler.rfile = io.BytesIO(body)
        ctx = MagicMock()
        ctx.headers = headers
        ctx._handler = mock_handler

        from src.dashboard.routes.products import handle_brand_assets_upload_zip
        handle_brand_assets_upload_zip(ctx)
        call_args = ctx.send_json.call_args
        assert call_args[1].get("status") == 400

    def test_non_multipart_returns_400(self):
        """Non-multipart content type → 400."""
        ctx = MagicMock()
        ctx.headers = {"Content-Type": "application/json"}
        from src.dashboard.routes.products import handle_brand_assets_upload_zip
        handle_brand_assets_upload_zip(ctx)
        call_args = ctx.send_json.call_args
        assert call_args[1].get("status") == 400

    def test_skips_macosx_metadata(self):
        """__MACOSX entries are skipped and not counted as errors."""
        zip_data = _make_zip({
            "__MACOSX/._顺丰.png": b"garbage",
            "顺丰.png": b"\x89PNG fake",
        })
        ctx = _make_ctx(zip_data)
        with patch("src.modules.listing.brand_assets.BrandAssetManager.add_asset") as mock_add:
            mock_add.return_value = {"id": "x", "name": "顺丰", "category": "express",
                                     "filename": "x.png", "uploaded_at": "2026-01-01"}
            from src.dashboard.routes.products import handle_brand_assets_upload_zip
            handle_brand_assets_upload_zip(ctx)
        resp = ctx.send_json.call_args[0][0]
        assert resp["imported"] == 1
        assert resp["skipped"] == 1
        assert resp["errors"] == []

    def test_unsupported_extension_goes_to_errors(self):
        """Files with unsupported extension are listed in errors."""
        zip_data = _make_zip({
            "顺丰.txt": b"not an image",
            "中通.png": b"\x89PNG fake",
        })
        ctx = _make_ctx(zip_data)
        with patch("src.modules.listing.brand_assets.BrandAssetManager.add_asset") as mock_add:
            mock_add.return_value = {"id": "x", "name": "中通", "category": "express",
                                     "filename": "x.png", "uploaded_at": "2026-01-01"}
            from src.dashboard.routes.products import handle_brand_assets_upload_zip
            handle_brand_assets_upload_zip(ctx)
        resp = ctx.send_json.call_args[0][0]
        assert resp["imported"] == 1
        assert resp["skipped"] == 1
        assert any("txt" in e for e in resp["errors"])

    def test_add_asset_exception_goes_to_errors(self):
        """If add_asset raises, the file is counted as skipped with error message."""
        zip_data = _make_zip({"顺丰.png": b"\x89PNG fake"})
        ctx = _make_ctx(zip_data)
        with patch("src.modules.listing.brand_assets.BrandAssetManager.add_asset",
                   side_effect=ValueError("disk full")):
            from src.dashboard.routes.products import handle_brand_assets_upload_zip
            handle_brand_assets_upload_zip(ctx)
        resp = ctx.send_json.call_args[0][0]
        assert resp["imported"] == 0
        assert resp["skipped"] == 1
        assert any("disk full" in e for e in resp["errors"])

    def test_empty_stem_skipped(self):
        """'.png' (dotfile) is skipped by the startswith('.') guard before stem/ext check."""
        zip_data = _make_zip({".png": b"\x89PNG fake"})
        ctx = _make_ctx(zip_data)
        with patch("src.modules.listing.brand_assets.BrandAssetManager.add_asset") as mock_add:
            from src.dashboard.routes.products import handle_brand_assets_upload_zip
            handle_brand_assets_upload_zip(ctx)
        resp = ctx.send_json.call_args[0][0]
        assert resp["imported"] == 0
        mock_add.assert_not_called()

    def test_category_passed_to_add_asset(self):
        """category from form is forwarded to BrandAssetManager.add_asset."""
        zip_data = _make_zip({"德邦.png": b"\x89PNG fake"})
        ctx = _make_ctx(zip_data, category="freight")
        with patch("src.modules.listing.brand_assets.BrandAssetManager.add_asset") as mock_add:
            mock_add.return_value = {"id": "y", "name": "德邦", "category": "freight",
                                     "filename": "y.png", "uploaded_at": "2026-01-01"}
            from src.dashboard.routes.products import handle_brand_assets_upload_zip
            handle_brand_assets_upload_zip(ctx)
        mock_add.assert_called_once_with("德邦", "freight", b"\x89PNG fake", "png")
