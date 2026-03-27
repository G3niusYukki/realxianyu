# P0: 安全漏洞修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消除代码中所有硬编码密钥、密码和注入漏洞，确保凭据通过环境变量管理。

**Architecture:** 将硬编码的敏感值替换为环境变量引用，修复 SQL 注入和并发 Bug，所有变更向后兼容（提供合理默认值或启动时校验）。

**Tech Stack:** Python 3.12, asyncio, SQLite, environment variables

---

## Task 1: 移除 ws_live.py 中的硬编码 MTOP App Secret

**Files:**
- Modify: `src/modules/messages/ws_live.py:26`
- Test: `tests/test_messages_ws_live.py`

`ws_live.py` 第 26 行硬编码了 `_MTOP_APP_SECRET = "444e9908a51d1cb236a27862abc769c9"`。这个值应该从环境变量读取。

- [ ] **Step 1: 编写测试验证 secret 来源**

在 `tests/test_messages_ws_live.py` 中添加：

```python
def test_mtop_app_secret_from_env(monkeypatch):
    """MTOP secret 应从环境变量读取，不应硬编码。"""
    from src.modules.messages import ws_live

    monkeypatch.setenv("MTOP_APP_SECRET", "test_secret_value")
    # 重新加载模块级常量
    assert ws_live._MTOP_APP_SECRET != "444e9908a51d1cb236a27862abc769c9"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_messages_ws_live.py::test_mtop_app_secret_from_env -v`
Expected: FAIL (当前硬编码值)

- [ ] **Step 3: 修改 ws_live.py，secret 从环境变量读取**

```python
# Before (line 26):
_MTOP_APP_SECRET = "444e9908a51d1cb236a27862abc769c9"

# After:
import os
_MTOP_APP_SECRET = os.getenv("MTOP_APP_SECRET", "")
```

同时在 `.env.example` 中添加：

```
# MTOP 签名密钥（从闲鱼平台获取）
MTOP_APP_SECRET=
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_messages_ws_live.py -v`

- [ ] **Step 5: 提交**

```bash
git add src/modules/messages/ws_live.py .env.example
git commit -m "fix(security): move MTOP app secret from hardcoded value to env var"
```

---

## Task 2: 移除 infra/scripts/setup-local.sh 中的硬编码密码

**Files:**
- Modify: `infra/scripts/setup-local.sh:49`

- [ ] **Step 1: 修改 setup-local.sh**

将硬编码的 Grafana 凭据替换为环境变量：

```bash
# Before:
--set admin.password=xianyu2024

# After:
--set admin.password="${GRAFANA_ADMIN_PASSWORD:-admin}"
```

同时在脚本顶部添加环境变量提示：

```bash
: "${GRAFANA_ADMIN_PASSWORD:=admin}"
echo "Grafana admin password: $GRAFANA_ADMIN_PASSWORD (override with GRAFANA_ADMIN_PASSWORD)"
```

- [ ] **Step 2: 提交**

```bash
git add infra/scripts/setup-local.sh
git commit -m "fix(security): remove hardcoded Grafana password, use env var"
```

---

## Task 3: 移除 order-service 中的硬编码默认密码

**Files:**
- Modify: `services/order-service/app/main.py:150`

- [ ] **Step 1: 修改默认密码为启动时校验**

```python
# Before:
db_password = os.getenv("DB_PASSWORD", "password")

# After:
db_password = os.getenv("DB_PASSWORD", "")
if not db_password:
    logger.warning("DB_PASSWORD not set — using local SQLite fallback")
```

- [ ] **Step 2: 提交**

```bash
git add services/order-service/app/main.py
git commit -m "fix(security): remove default DB password from order-service"
```

---

## Task 4: 修复 dual_write.py 的 asyncio.Lock 并发 Bug

**Files:**
- Modify: `services/common/xianyuflow_common/dual_write.py:257-262`
- Test: `tests/test_dual_write.py`（新增）

Bug 描述：`_sqlite_lock()` 每次调用都创建新的 `asyncio.Lock()`，导致锁永远不被持有。

- [ ] **Step 1: 编写并发测试**

```python
import asyncio
import pytest
from xianyuflow_common.dual_write import DualWriteManager


@pytest.mark.asyncio
async def test_sqlite_lock_prevents_concurrent_access():
    """验证 SQLite 锁确实序列化并发操作。"""
    mgr = DualWriteManager.__new__(DualWriteManager)
    mgr._lock = asyncio.Lock()  # 将在 Task 4 Step 3 中改为实例属性

    call_order = []

    async def slow_op(label, delay=0.05):
        async with mgr._sqlite_lock():
            call_order.append(f"{label}-start")
            await asyncio.sleep(delay)
            call_order.append(f"{label}-end")

    await asyncio.gather(slow_op("A"), slow_op("B"))
    # 如果锁生效，操作不会交错
    assert call_order in [
        ["A-start", "A-end", "B-start", "B-end"],
        ["B-start", "B-end", "A-start", "A-end"],
    ]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_dual_write.py::test_sqlite_lock_prevents_concurrent_access -v`
Expected: FAIL (当前锁无效，操作交错)

- [ ] **Step 3: 修复 `_sqlite_lock`**

```python
# Before (line 257-262):
@asynccontextmanager
async def _sqlite_lock(self):
    """SQLite 操作锁（防止并发问题）"""
    async with asyncio.Lock():
        yield

# After:
# 在 __init__ 中添加:
#     self._lock = asyncio.Lock()

@asynccontextmanager
async def _sqlite_lock(self):
    """SQLite 操作锁（防止并发问题）"""
    async with self._lock:
        yield
```

确保 `__init__` 中初始化 `self._lock = asyncio.Lock()`。

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_dual_write.py -v`

- [ ] **Step 5: 提交**

```bash
git add services/common/xianyuflow_common/dual_write.py
git commit -m "fix(concurrency): fix asyncio.Lock bug in dual_write._sqlite_lock"
```

---

## Task 5: 修复 dual_write.py 的 SQL 注入风险

**Files:**
- Modify: `services/common/xianyuflow_common/dual_write.py:210-212,218`

Bug 描述：`table` 和 `limit` 通过 f-string 直接拼接到 SQL 中。

- [ ] **Step 1: 修改 compare_data 方法，添加输入校验**

```python
import re

# 在 compare_data 方法开头添加校验:
_VALID_TABLE_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

async def compare_data(self, table: str, limit: int = 100) -> dict:
    if not _VALID_TABLE_RE.match(table):
        raise ValueError(f"Invalid table name: {table!r}")
    limit = max(1, min(int(limit), 10000))

    # SQLite — 使用参数化 limit
    cursor = await self._sqlite_pool.execute(
        f"SELECT * FROM {table} ORDER BY id LIMIT ?",
        (limit,),
    )

    # PostgreSQL — 使用 $1 参数化
    rows = await conn.fetch(
        f"SELECT * FROM {table} ORDER BY id LIMIT $1",
        limit,
    )
```

- [ ] **Step 2: 提交**

```bash
git add services/common/xianyuflow_common/dual_write.py
git commit -m "fix(security): parameterize SQL in dual_write.compare_data, validate table name"
```

---

## Task 6: 修复 ai-service SSE JSON 手动拼接

**Files:**
- Modify: `services/ai-service/app/main.py:142`

- [ ] **Step 1: 用 json.dumps 替换手动字符串拼接**

```python
# Before (line 142 附近):
f"data: {json.dumps({'content': chunk, ...})}\n\n"

# After: 确保 SSE 数据通过 json.dumps 序列化
import json
sse_data = json.dumps({"content": chunk, "type": "delta"}, ensure_ascii=False)
yield f"data: {sse_data}\n\n"
```

- [ ] **Step 2: 提交**

```bash
git add services/ai-service/app/main.py
git commit -m "fix(security): use json.dumps for SSE data to prevent injection"
```

---

## Task 7: 修复 deprecated datetime.utcnow

**Files:**
- Modify: `services/common/xianyuflow_common/models/base.py`

- [ ] **Step 1: 替换为 datetime.now(UTC)**

```python
# Before:
from datetime import datetime
datetime.utcnow()

# After:
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

- [ ] **Step 2: 提交**

```bash
git add services/common/xianyuflow_common/models/base.py
git commit -m "fix: replace deprecated datetime.utcnow with datetime.now(UTC)"
```

---

## 完成标准

- [ ] 所有硬编码密钥/密码已移除或改为环境变量
- [ ] SQL 注入已修复（参数化查询 + 输入校验）
- [ ] asyncio.Lock 并发 Bug 已修复
- [ ] `.env.example` 已更新包含所有新的环境变量
- [ ] `python -m pytest tests/ -q` 全部通过
