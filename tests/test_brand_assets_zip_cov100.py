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
