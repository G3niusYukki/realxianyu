# Brand Assets Zip Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 允许用户一次性上传包含多张品牌图片的 zip 压缩包，替代逐张上传的操作方式。

**Architecture:** 新增后端接口 `POST /api/brand-assets/upload-zip` 解压 zip 并批量调用现有 `BrandAssetManager.add_asset()`；前端在品牌图片上传卡片中新增批量上传区块，调用新接口并展示导入结果（成功数/跳过数/错误列表）。

**Tech Stack:** Python `zipfile` (stdlib), React + TypeScript (Vite), `cgi.FieldStorage` (multipart), `FormData` (fetch)

---

### Task 1: 后端接口 — 写失败测试

**Files:**
- Create: `tests/test_brand_assets_zip_cov100.py`

- [ ] **Step 1: 新建测试文件，写第一个失败测试**

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/test_brand_assets_zip_cov100.py::TestUploadZipSuccess::test_imports_two_png_images -v
```
Expected: FAIL with `AttributeError` or `ImportError` — `handle_brand_assets_upload_zip` 不存在

- [ ] **Step 3: Commit red step**

```bash
cd /Users/peterzhang/realxianyu && git add tests/test_brand_assets_zip_cov100.py && git commit -m "test: add failing test for upload-zip endpoint"
```

---

### Task 2: 后端接口实现

**Files:**
- Modify: `src/dashboard/routes/products.py` (在 `handle_brand_assets_upload` 定义之后插入，约第 461 行)

- [ ] **Step 1: 在 `products.py` 中添加新路由**

在第 461 行（`handle_brand_assets_upload` 函数块结束后）插入：

```python
# ---------------------------------------------------------------------------
# POST /api/brand-assets/upload-zip
# ---------------------------------------------------------------------------


@post("/api/brand-assets/upload-zip")
def handle_brand_assets_upload_zip(ctx: RouteContext) -> None:
    import cgi
    import io
    import zipfile
    from pathlib import Path as _Path

    from src.dashboard_server import _error_payload
    from src.modules.listing.brand_assets import ALLOWED_EXTENSIONS, BrandAssetManager

    content_type_header = ctx.headers.get("Content-Type", "")
    if "multipart/form-data" not in content_type_header:
        ctx.send_json(_error_payload("Expected multipart/form-data"), status=400)
        return

    form = cgi.FieldStorage(
        fp=ctx._handler.rfile,
        headers=ctx.headers,
        environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type_header},
    )
    file_item = form["file"] if "file" in form else None
    cat = form.getvalue("category", "default")

    if file_item is None or not getattr(file_item, "file", None):
        ctx.send_json(_error_payload("Missing file field"), status=400)
        return

    zip_data = file_item.file.read()
    if not zipfile.is_zipfile(io.BytesIO(zip_data)):
        ctx.send_json(_error_payload("File is not a valid ZIP archive"), status=400)
        return

    mgr = BrandAssetManager()
    imported = 0
    skipped = 0
    errors: list[str] = []

    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        for member in zf.infolist():
            member_name = member.filename
            base_name = _Path(member_name).name
            # Skip directories, macOS metadata, hidden files
            if member.is_dir() or "__MACOSX" in member_name or base_name.startswith("."):
                skipped += 1
                continue
            stem = _Path(base_name).stem
            ext = _Path(base_name).suffix.lstrip(".").lower()
            if not stem or ext not in ALLOWED_EXTENSIONS:
                skipped += 1
                if ext and ext not in ALLOWED_EXTENSIONS:
                    errors.append(f"{base_name}: 不支持的格式 (.{ext})")
                continue
            try:
                file_data = zf.read(member_name)
                mgr.add_asset(stem, cat, file_data, ext)
                imported += 1
            except Exception as exc:
                errors.append(f"{base_name}: {exc}")
                skipped += 1

    ctx.send_json({"ok": True, "imported": imported, "skipped": skipped, "errors": errors})
```

- [ ] **Step 2: 运行测试确认通过**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/test_brand_assets_zip_cov100.py::TestUploadZipSuccess::test_imports_two_png_images -v
```
Expected: PASS

- [ ] **Step 3: Commit green step**

```bash
cd /Users/peterzhang/realxianyu && git add src/dashboard/routes/products.py && git commit -m "feat: implement handle_brand_assets_upload_zip"
```

---

### Task 3: 补全边界情况测试并全部通过

**Files:**
- Modify: `tests/test_brand_assets_zip_cov100.py`

- [ ] **Step 1: 添加更多测试用例**

在测试文件中追加以下测试类：

```python
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
        boundary = b"testboundary"
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
```

- [ ] **Step 2: 运行全部测试**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/test_brand_assets_zip_cov100.py -v
```
Expected: all PASS

- [ ] **Step 3: 确认现有测试不受影响**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -20
```
Expected: no new failures

- [ ] **Step 4: Commit**

```bash
cd /Users/peterzhang/realxianyu && git add tests/test_brand_assets_zip_cov100.py && git commit -m "test: add edge case coverage for POST /api/brand-assets/upload-zip"
```

---

### Task 4: 前端 API 函数

**Files:**
- Modify: `client/src/api/listing.ts` (在 `uploadBrandAsset` 之后插入)

- [ ] **Step 1: 在 `deleteBrandAsset` 之前（第 34 行前）新增函数**

```typescript
export const uploadBrandAssetsZip = (
  file: File,
  category: string,
): Promise<AxiosResponse<{ ok: boolean; imported: number; skipped: number; errors: string[] }>> => {
  const form = new FormData();
  form.append('file', file);
  form.append('category', category);
  return api.post('/brand-assets/upload-zip', form, { headers: { 'Content-Type': 'multipart/form-data' } });
};
```

- [ ] **Step 2: 确认 TypeScript 编译通过**

```bash
cd /Users/peterzhang/realxianyu/client && npx tsc --noEmit 2>&1 | head -20
```
Expected: no errors

- [ ] **Step 3: Commit**

```bash
cd /Users/peterzhang/realxianyu && git add client/src/api/listing.ts && git commit -m "feat: add uploadBrandAssetsZip API function"
```

---

### Task 5: 前端批量上传 UI

**Files:**
- Modify: `client/src/pages/products/AutoPublish.tsx`

- [ ] **Step 1: 添加所需 state 和 handler**

在 `BrandAssetsTab` 函数体内，`fileRef` 声明（第 82 行）之后插入：

```typescript
const [zipUploading, setZipUploading] = useState(false);
const zipFileRef = useRef<HTMLInputElement>(null);

const handleZipUpload = async () => {
  const file = zipFileRef.current?.files?.[0];
  if (!file) { toast.error('请选择 ZIP 压缩包'); return; }
  setZipUploading(true);
  try {
    const res = await uploadBrandAssetsZip(file, assetCat);
    if (res.data?.ok) {
      const { imported, skipped, errors } = res.data;
      toast.success(`批量导入完成：${imported} 张成功，${skipped} 张跳过`);
      if (errors.length > 0) {
        errors.forEach(e => toast.error(e, { duration: 6000 }));
      }
      if (zipFileRef.current) zipFileRef.current.value = '';
      fetchData();
    }
  } catch (err: any) {
    toast.error('上传失败: ' + (err?.response?.data?.error || err.message));
  }
  setZipUploading(false);
};
```

- [ ] **Step 2: 在 import 行引入新 API 函数**

在 `AutoPublish.tsx` 顶部找到引入 `uploadBrandAsset` 的那行，将 `uploadBrandAssetsZip` 加进去：

```typescript
import { ..., uploadBrandAsset, uploadBrandAssetsZip, ... } from '../../api/listing';
```

- [ ] **Step 3: 在上传卡片中追加批量上传区块**

在第 168 行（`</div>` — 关闭单文件上传 flex 行）之后，第 169 行（`</div>` — 关闭 `xy-card p-5`）之前插入分隔线和批量区块：

```tsx
        <hr className="my-4 border-xy-border" />
        <p className="text-xs text-xy-text-secondary mb-3 flex items-center gap-1.5">
          批量上传：将多张品牌图片打包为 <code className="bg-xy-gray-100 px-1 rounded text-[11px]">.zip</code>，文件名即品牌名
        </p>
        <div className="flex items-end gap-3">
          <div className="flex-1 max-w-xs">
            <label className="xy-label text-xs">ZIP 压缩包</label>
            <input ref={zipFileRef} type="file" accept=".zip,application/zip" className="xy-input px-3 py-1.5 text-sm file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:bg-violet-50 file:text-violet-600 file:font-medium file:text-xs" />
          </div>
          <button onClick={handleZipUpload} disabled={zipUploading} className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-violet-50 border border-violet-300 text-violet-700 hover:bg-violet-100 transition-colors disabled:opacity-50">
            {zipUploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />} 批量导入
          </button>
        </div>
```

- [ ] **Step 4: 确认 TypeScript 编译通过**

```bash
cd /Users/peterzhang/realxianyu/client && npx tsc --noEmit 2>&1 | head -20
```
Expected: no errors

- [ ] **Step 5: 构建前端**

```bash
cd /Users/peterzhang/realxianyu/client && npm run build 2>&1 | tail -10
```
Expected: build succeeds

- [ ] **Step 6: Commit**

```bash
cd /Users/peterzhang/realxianyu && git add client/src/pages/products/AutoPublish.tsx && git commit -m "feat: add batch zip upload UI for brand assets"
```

---

### Task 6: 全量测试 + Push

- [ ] **Step 1: 运行全量测试**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/ -q 2>&1 | tail -20
```
Expected: all pass (no new failures)

- [ ] **Step 2: Lint 检查**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/ruff check src/ && ./venv/bin/ruff format src/ --check
```
Expected: no errors

- [ ] **Step 3: Push**

```bash
cd /Users/peterzhang/realxianyu && git push origin main
```
