# Brand Asset Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 允许用户对素材库中每张品牌图片单独改名（改名后自动归入对应品牌分组）。

**Architecture:** 后端在 `BrandAssetManager` 新增 `rename_asset()`，通过 `PUT /api/brand-assets/<asset_id>` 暴露；前端每个缩略图 hover 时左上角出现铅笔图标，点击后在缩略图下方出现 inline 输入框，Enter/✓ 确认，Escape/✗ 取消。

**Tech Stack:** Python threading.RLock (manifest 写入), React useState, lucide-react icons

---

### Task 1: BrandAssetManager.rename_asset — 写失败测试

**Files:**
- Create: `tests/test_brand_assets_rename_cov100.py`

- [x] **Step 1: 新建测试文件，写失败测试**

```python
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
    (tmp_path / "dummy.png").write_bytes(b"\x89PNG")
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
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/test_brand_assets_rename_cov100.py -v 2>&1 | tail -15
```
Expected: FAIL — `AttributeError: 'BrandAssetManager' object has no attribute 'rename_asset'`

- [x] **Step 3: Commit red step**

```bash
cd /Users/peterzhang/realxianyu && git add tests/test_brand_assets_rename_cov100.py && git commit -m "test: add failing tests for BrandAssetManager.rename_asset"
```

---

### Task 2: 实现 BrandAssetManager.rename_asset

**Files:**
- Modify: `src/modules/listing/brand_assets.py` (在 `delete_asset` 方法之后，约第 183 行)

- [x] **Step 1: 在 `delete_asset` 末尾之后插入新方法**

在第 183 行（`return True` 之后的空行）处，在 `get_brands_grouped` 方法之前插入：

```python
    def rename_asset(self, asset_id: str, new_name: str) -> dict | None:
        """
        修改资产品牌名称，返回更新后的条目，若不存在则返回 None。

        Args:
            asset_id: 资产 UUID。
            new_name: 新品牌名称。

        Returns:
            更新后的资产字典，若资产不存在则 None。
        """
        safe_name = re.sub(r"[^\w\u4e00-\u9fff\- ]", "", (new_name or "").strip()) or "unnamed"
        with self._lock:
            entries = self._load_manifest()
            idx = next((i for i, e in enumerate(entries) if e.get("id") == asset_id), None)
            if idx is None:
                return None
            entries[idx]["name"] = safe_name
            self._save_manifest(entries)
            return dict(entries[idx])
```

- [x] **Step 2: 运行测试确认通过**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/test_brand_assets_rename_cov100.py -v 2>&1 | tail -15
```
Expected: 5 passed

- [x] **Step 3: Commit green step**

```bash
cd /Users/peterzhang/realxianyu && git add src/modules/listing/brand_assets.py tests/test_brand_assets_rename_cov100.py && git commit -m "feat: add BrandAssetManager.rename_asset"
```

---

### Task 3: 后端路由 PUT /api/brand-assets/<asset_id> — 写失败测试

**Files:**
- Create: `tests/test_brand_assets_rename_route_cov100.py`

- [x] **Step 1: 新建路由测试文件**

```python
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
```

- [x] **Step 2: 运行测试确认失败**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/test_brand_assets_rename_route_cov100.py -v 2>&1 | tail -10
```
Expected: FAIL — `ImportError: cannot import name 'handle_brand_assets_rename'`

- [x] **Step 3: Commit red step**

```bash
cd /Users/peterzhang/realxianyu && git add tests/test_brand_assets_rename_route_cov100.py && git commit -m "test: add failing tests for PUT /api/brand-assets rename route"
```

---

### Task 4: 实现后端路由

**Files:**
- Modify: `src/dashboard/routes/products.py` (在 `handle_brand_assets_delete` 函数块之前，约第 392 行)

- [x] **Step 1: 确认 `put_prefix` 已在 import 行中**

查看 `products.py` 第 10 行：
```python
from src.dashboard.router import RouteContext, get, post, get_prefix, post_prefix, put_prefix, delete_prefix
```
`put_prefix` 已存在，无需修改 import。

- [x] **Step 2: 在第 392 行（`# DELETE /api/brand-assets/` 注释块之前）插入新路由**

注：`@put_prefix("/api/brand-assets/", "asset_id")` 与现有 `GET /api/brand-assets/file/` 前缀路由不冲突，因为它们分属不同 HTTP 方法的路由表（`_PUT_PREFIX_ROUTES` vs `_GET_PREFIX_ROUTES`）。

```python
# ---------------------------------------------------------------------------
# PUT /api/brand-assets/<asset_id>  — rename
# ---------------------------------------------------------------------------


@put_prefix("/api/brand-assets/", "asset_id")
def handle_brand_assets_rename(ctx: RouteContext) -> None:
    from src.dashboard_server import _error_payload
    from src.modules.listing.brand_assets import BrandAssetManager

    asset_id = ctx.path_params.get("asset_id", "").strip("/")
    if not asset_id:
        ctx.send_json(_error_payload("Missing asset id"), status=400)
        return

    body = ctx.json_body()
    new_name = body.get("name", "").strip()
    if not new_name:
        ctx.send_json(_error_payload("Missing name field"), status=400)
        return

    mgr = BrandAssetManager()
    updated = mgr.rename_asset(asset_id, new_name)
    if updated is None:
        ctx.send_json(_error_payload("Asset not found", code="NOT_FOUND"), status=404)
        return
    ctx.send_json({"ok": True, "asset": updated})
```

- [x] **Step 3: 运行路由测试确认通过**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/test_brand_assets_rename_route_cov100.py -v 2>&1 | tail -10
```
Expected: 5 passed

- [x] **Step 4: 确认全量测试不受影响**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```
Expected: no new failures

- [x] **Step 5: Commit**

```bash
cd /Users/peterzhang/realxianyu && git add src/dashboard/routes/products.py tests/test_brand_assets_rename_route_cov100.py && git commit -m "feat: add PUT /api/brand-assets/<id> rename route"
```

---

### Task 5: 前端 API 函数

**Files:**
- Modify: `client/src/api/listing.ts` (在 `uploadBrandAssetsZip` 之后，约第 44 行)

- [x] **Step 1: 在 `deleteBrandAsset` 之前插入新函数**

```typescript
export const renameBrandAsset = (
  id: string,
  name: string,
): Promise<AxiosResponse<{ ok: boolean; asset: BrandAsset }>> =>
  api.put(`/brand-assets/${id}`, { name });
```

- [x] **Step 2: 确认 TypeScript 编译无新错误**

```bash
cd /Users/peterzhang/realxianyu/client && npx tsc --noEmit 2>&1 | grep listing
```
Expected: no output (no errors in listing.ts)

- [x] **Step 3: Commit**

```bash
cd /Users/peterzhang/realxianyu && git add client/src/api/listing.ts && git commit -m "feat: add renameBrandAsset API function"
```

---

### Task 6: 前端改名 UI

**Files:**
- Modify: `client/src/pages/products/AutoPublish.tsx`

- [x] **Step 1: 在 import 中加入 Pencil、Check、X 图标，并引入 renameBrandAsset**

将第 5 行的 API import 改为：
```typescript
  getBrandAssets, getBrandAssetsGrouped, uploadBrandAsset, uploadBrandAssetsZip,
  deleteBrandAsset, renameBrandAsset,
```

将第 12 行的 lucide import 改为（新增 `Pencil, Check, X`）：
```typescript
import {
  Calendar, RefreshCw, Upload, Trash2, Image as ImageIcon,
  ChevronUp, Edit3, Clock,
  CheckCircle2, XCircle, AlertTriangle, Package, Send,
  Pencil, Check, X,
} from 'lucide-react';
```

- [x] **Step 2: 在 BrandAssetsTab 的 state 区块新增改名 state**

在 `fileRef` 声明（约第 82 行）之后，`zipUploading` 声明之前插入：
```typescript
const [renamingId, setRenamingId] = useState<string | null>(null);
const [renameValue, setRenameValue] = useState('');
```

- [x] **Step 3: 新增 handleRename 函数**

在 `handleUpload` 函数之后（`fetchData` 已在约第 107 行定义，此处可直接引用）：
```typescript
const handleRename = async (id: string) => {
  if (!renameValue.trim()) { toast.error('品牌名称不能为空'); return; }
  try {
    const res = await renameBrandAsset(id, renameValue.trim());
    if (res.data?.ok) {
      toast.success(`已改名为「${res.data.asset.name}」`);
      setRenamingId(null);
      fetchData();
    }
  } catch (err: any) {
    toast.error('改名失败: ' + (err?.response?.data?.error || err.message));
  }
};
```

- [x] **Step 4: 替换素材库中每个缩略图的 JSX**

找到约第 226 行（品牌内每张图的容器），将：
```tsx
                  {brands[brandName].map(asset => (
                    <div key={asset.id} className="group relative w-20 h-20 rounded-xl overflow-hidden border border-xy-border bg-white">
                      <img src={`/api/brand-assets/file/${asset.filename}`} alt={asset.name} className="w-full h-full object-contain p-1" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                      <button onClick={() => handleDelete(asset.id, asset.name)} className="absolute top-0.5 right-0.5 p-0.5 bg-white/80 rounded opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50">
                        <Trash2 className="w-3 h-3 text-red-500" />
                      </button>
                    </div>
                  ))}
```

替换为：
```tsx
                  {brands[brandName].map(asset => (
                    <div key={asset.id} className="flex flex-col gap-1">
                      <div className="group relative w-20 h-20 rounded-xl overflow-hidden border border-xy-border bg-white">
                        <img src={`/api/brand-assets/file/${asset.filename}`} alt={asset.name} className="w-full h-full object-contain p-1" onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                        <button onClick={() => handleDelete(asset.id, asset.name)} className="absolute top-0.5 right-0.5 p-0.5 bg-white/80 rounded opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50">
                          <Trash2 className="w-3 h-3 text-red-500" />
                        </button>
                        <button onClick={() => { setRenamingId(asset.id); setRenameValue(asset.name); }} className="absolute top-0.5 left-0.5 p-0.5 bg-white/80 rounded opacity-0 group-hover:opacity-100 transition-opacity hover:bg-violet-50">
                          <Pencil className="w-3 h-3 text-violet-500" />
                        </button>
                      </div>
                      {renamingId === asset.id && (
                        <div className="flex gap-0.5 items-center w-20">
                          <input
                            className="xy-input px-1 py-0.5 text-xs flex-1 min-w-0"
                            value={renameValue}
                            onChange={e => setRenameValue(e.target.value)}
                            onKeyDown={e => {
                              if (e.key === 'Enter') handleRename(asset.id);
                              if (e.key === 'Escape') setRenamingId(null);
                            }}
                            autoFocus
                          />
                          <button onClick={() => handleRename(asset.id)} className="p-0.5 text-green-600 hover:text-green-700 shrink-0">
                            <Check className="w-3 h-3" />
                          </button>
                          <button onClick={() => setRenamingId(null)} className="p-0.5 text-xy-text-muted hover:text-red-500 shrink-0">
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
```

- [x] **Step 5: 确认 TypeScript 编译无新错误**

```bash
cd /Users/peterzhang/realxianyu/client && npx tsc --noEmit 2>&1 | grep -i "autopublish\|listing"
```
Expected: no output

- [x] **Step 6: 构建前端**

```bash
cd /Users/peterzhang/realxianyu/client && npm run build 2>&1 | tail -5
```
Expected: `✓ built in ...`

- [x] **Step 7: Commit**

```bash
cd /Users/peterzhang/realxianyu && git add client/src/pages/products/AutoPublish.tsx && git commit -m "feat: add inline rename UI for brand assets"
```

---

### Task 7: 全量测试 + Push

- [x] **Step 1: 全量测试**

```bash
cd /Users/peterzhang/realxianyu && ./venv/bin/python -m pytest tests/ -q 2>&1 | tail -5
```
Expected: no new failures

- [x] **Step 2: Push**

```bash
cd /Users/peterzhang/realxianyu && git push origin main
```
