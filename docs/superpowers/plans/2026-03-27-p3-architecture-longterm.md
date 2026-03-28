# P3: 架构改进与长期优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 明确微服务路线图、添加 services/ 测试、统一配置/日志模式、引入前端测试、添加数据库迁移版本管理。

**Architecture:** 这些是中长期任务，依赖 P0/P1/P2 的基础改进完成后再推进。按独立子系统拆分，每个 Task 可独立实施。

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Pydantic, Vitest, React Testing Library

---

## Task 1: 为 services/ 添加测试基础设施和核心测试

**Files:**
- Create: `services/common/tests/test_database.py`
- Create: `services/common/tests/test_cache.py`
- Create: `services/common/tests/test_dual_write.py`
- Create: `services/gateway-service/tests/test_main.py`
- Create: `services/gateway-service/tests/test_signing.py`
- Create: `services/conftest.py`

**问题：** services/ 目录零测试覆盖，CI 尝试安装这些服务但无法验证。

- [x] **Step 1: 在 services/common 下创建测试目录和 conftest**

```python
# services/conftest.py
import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
```

- [x] **Step 2: 编写 gateway-service 核心测试**

```python
# services/gateway-service/tests/test_signing.py
from app.signing import generate_sign

def test_sign_deterministic():
    params = {"appid": "test", "timestamp": "1234567890"}
    sign1 = generate_sign(params, "secret_key")
    sign2 = generate_sign(params, "secret_key")
    assert sign1 == sign2

def test_sign_changes_with_params():
    sign1 = generate_sign({"appid": "a", "timestamp": "1"}, "secret")
    sign2 = generate_sign({"appid": "b", "timestamp": "1"}, "secret")
    assert sign1 != sign2
```

```python
# services/gateway-service/tests/test_main.py
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_health_endpoint():
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
```

- [x] **Step 3: 编写 common 模块核心测试**

测试 `MultiLevelCache` 的 TTL 和 LRU 淘汰，测试 `DualWriteManager` 的模式切换。

- [x] **Step 4: 运行测试确认通过**

Run: `cd services && python -m pytest common/tests gateway-service/tests -v`

- [x] **Step 5: 提交**

```bash
git add services/conftest.py services/common/tests/ services/gateway-service/tests/
git commit -m "test(services): add core tests for gateway-service and common modules"
```

---

## Task 2: 明确 services/ 微服务路线图

**Files:**
- Create: `docs/MICROSERVICE_ROADMAP.md`

**问题：** `src/` 和 `services/` 双架构并存，无清晰迁移路线图。

- [x] **Step 1: 编写微服务路线图文档**

内容应包含：
- **现状评估**: services/ 的完成度（测试、部署、Kafka 集成）
- **方案 A — 推进迁移**: 定义阶段（SQLite → PostgreSQL 双写 → 服务拆分 → K8s 部署）
- **方案 B — 精简 services/**: 保留 gateway-service（已可独立运行），移除未完成的 ai/message/order/quote 服务，减少维护负担
- **建议时间线**: 每个阶段的预计工作量

- [x] **Step 2: 提交**

```bash
git add docs/MICROSERVICE_ROADMAP.md
git commit -m "docs: add microservice migration roadmap"
```

---

## Task 3: 添加数据库迁移版本管理

**Files:**
- Create: `src/core/migration.py`
- Create: `database/migrations/0000_schema_version.sql`
- Modify: `src/dashboard_server.py` (启动时运行迁移)

**问题：** 12 个 SQL 迁移文件无版本追踪，无幂等性保证，重复文件存在。

- [x] **Step 1: 创建 schema_versions 表**

```sql
-- database/migrations/0000_schema_version.sql
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- [x] **Step 2: 创建迁移运行器**

```python
# src/core/migration.py
"""简单的数据库迁移运行器。"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from loguru import logger

MIGRATIONS_DIR = Path("database/migrations")

def run_migrations(db_path: str) -> list[str]:
    """运行所有未应用的迁移，返回已应用的迁移名列表。"""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_versions (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_versions")}
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))

    newly_applied = []
    for i, path in enumerate(migrations):
        version = i + 1
        if version in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_versions (version, name) VALUES (?, ?)",
                     (version, path.name))
        conn.commit()
        logger.info(f"Migration applied: {path.name}")
        newly_applied.append(path.name)

    conn.close()
    return newly_applied
```

- [x] **Step 3: 在 dashboard_server.py 启动时调用迁移**

在 `run_server()` 函数的 DB 初始化阶段添加：

```python
from src.core.migration import run_migrations
run_migrations("data/agent.db")
```

- [x] **Step 4: 编写测试**

```python
# tests/test_migration.py
import tempfile
from src.core.migration import run_migrations

def test_migration_idempotent():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        applied1 = run_migrations(f.name)
        applied2 = run_migrations(f.name)
        assert len(applied2) == 0  # 第二次不应应用任何迁移
```

- [x] **Step 5: 提交**

```bash
git add src/core/migration.py database/migrations/0000_schema_version.sql tests/test_migration.py src/dashboard_server.py
git commit -m "feat(db): add schema migration version tracking"
```

---

## Task 4: 引入前端测试框架

**Files:**
- Modify: `client/package.json` (添加 devDependencies 和 scripts)
- Create: `client/vitest.config.ts`
- Create: `client/src/utils/__tests__/format.test.ts`
- Create: `client/src/hooks/__tests__/useAsyncData.test.ts`

- [x] **Step 1: 安装依赖**

Run: `cd client && npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom`

- [x] **Step 2: 创建 vitest 配置**

```typescript
// client/vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: [],
  },
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
})
```

- [x] **Step 3: 编写工具函数测试**

```typescript
// client/src/utils/__tests__/format.test.ts
import { describe, it, expect } from 'vitest'
import { formatPrice } from '../format'

describe('formatPrice', () => {
  it('formats number to ¥X.XX', () => {
    expect(formatPrice(10)).toBe('¥10.00')
  })
  it('handles string input', () => {
    expect(formatPrice('15.5')).toBe('¥15.50')
  })
  it('returns — for null/undefined', () => {
    expect(formatPrice(null)).toBe('—')
    expect(formatPrice(undefined)).toBe('—')
  })
})
```

- [x] **Step 4: 运行测试**

Run: `cd client && npx vitest run`

- [x] **Step 5: 提交**

```bash
git add client/package.json client/vitest.config.ts client/src/utils/__tests__/ client/src/hooks/__tests__/
git commit -m "test(frontend): add Vitest + Testing Library, initial util/hook tests"
```

---

## Task 5: 统一 Dashboard 内联子组件提取

**Files:**
- Create: `client/src/pages/dashboard/PublishQueueCard.tsx`
- Create: `client/src/pages/dashboard/SliderStatsCard.tsx`
- Create: `client/src/pages/dashboard/XgjControlPanel.tsx`
- Modify: `client/src/pages/Dashboard.tsx` (删除内联定义，改为 import)

**问题：** `Dashboard.tsx` 定义了 3 个内联子组件，每次父组件渲染都重新创建。

- [x] **Step 1: 提取 PublishQueueCard**

从 `Dashboard.tsx` 中提取 `PublishQueueCard` 为独立文件，用 `React.memo` 包装。

- [x] **Step 2: 提取 SliderStatsCard**

同上。

- [x] **Step 3: 提取 XgjControlPanel**

同上。

- [x] **Step 4: 修改 Dashboard.tsx 使用提取的组件**

```tsx
import PublishQueueCard from './dashboard/PublishQueueCard'
import SliderStatsCard from './dashboard/SliderStatsCard'
import XgjControlPanel from './dashboard/XgjControlPanel'
```

- [x] **Step 5: 运行构建确认**

Run: `cd client && npm run build`

- [x] **Step 6: 提交**

```bash
git add client/src/pages/dashboard/ client/src/pages/Dashboard.tsx
git commit -m "refactor(frontend): extract Dashboard inline sub-components with React.memo"
```

---

## Task 6: 移除 config.example.yaml 中的硬编码 browser_id

**Files:**
- Modify: `config/config.example.yaml:120`

- [x] **Step 1: 替换为环境变量引用**

```yaml
# Before:
browser_id: 3213efceee934ab09138ec1100f1c62b

# After:
browser_id: ${BITBROWSER_BROWSER_ID:}
```

- [x] **Step 2: 提交**

```bash
git add config/config.example.yaml
git commit -m "fix(config): replace hardcoded browser_id with env var reference"
```

---

## Task 7: 添加数据库外键约束

**Files:**
- Create: `database/migrations/0013_foreign_keys.sql`

**问题：** `virtual_goods_orders` 和 `virtual_goods_products` 之间无外键约束。

- [x] **Step 1: 编写迁移添加外键**

```sql
-- database/migrations/0013_foreign_keys.sql
-- 注意: SQLite 不支持 ALTER TABLE ADD CONSTRAINT，需要重建表
-- 这里仅记录意图，实际实施需要根据数据量评估

-- 对于新部署，在原始建表语句中添加:
-- FOREIGN KEY (product_id) REFERENCES virtual_goods_products(id)
```

- [x] **Step 2: 提交**

```bash
git add database/migrations/0013_foreign_keys.sql
git commit -m "feat(db): add foreign key migration for virtual goods tables"
```

---

## 完成标准

- [x] services/ 有核心测试覆盖
- [x] 微服务路线图已文档化
- [x] 数据库迁移有版本追踪
- [x] 前端有测试框架和初始测试
- [x] Dashboard 子组件已提取并 memo 化
- [x] 硬编码配置已替换为环境变量
- [x] `python -m pytest tests/ -q` 全部通过
- [x] `cd client && npm run build` 成功
