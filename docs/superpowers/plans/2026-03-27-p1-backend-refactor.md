# P1: 后端 Python 代码重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 消除代码重复、精简 God Class、外部化硬编码数据、引入连接池、统一错误处理，提升后端代码质量和可维护性。

**Architecture:** 以渐进式重构为主，不改变外部 API 行为。每个 Task 独立可测试，可按任意顺序执行。

**Tech Stack:** Python 3.12, asyncio, aiosqlite, Pydantic, SQLite

---

## Task 1: 提取 BaseMarkupMixin 消除 Provider 定价逻辑重复

**Files:**
- Create: `src/modules/quote/pricing_calculator.py`
- Modify: `src/modules/quote/providers.py` (CostTableMarkupQuoteProvider, ApiCostMarkupQuoteProvider)
- Modify: `src/modules/quote/__init__.py`
- Test: `tests/test_quote_engine.py`, `tests/test_quote_engine_full.py`

**问题：** `CostTableMarkupQuoteProvider.get_quote()` 和 `ApiCostMarkupQuoteProvider.get_quote()` 共享 ~80% 的三层定价逻辑（成本→加价→闲鱼折扣、体积重计算、explain dict 构建），各 ~100 行。

- [x] **Step 1: 创建 `pricing_calculator.py`，提取共享的三层定价计算函数**

```python
# src/modules/quote/pricing_calculator.py
"""三层定价共享计算逻辑。

Layer 1: 成本价 (cost)
Layer 2: 加价 (markup / add)
Layer 3: 闲鱼让利 (discount)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.modules.quote.providers import (
    _resolve_category_markup,
    _resolve_xianyu_discount_value,
    _resolve_markup,
    _profile_markup,
    _resolve_volume_divisor,
    _derive_volume_weight_kg,
    _first_positive,
    _eta_by_service_level,
)


@dataclass
class PricingInput:
    """三层定价的输入参数。"""
    first_cost: float
    extra_cost: float
    base_weight: float
    actual_weight: float
    volume_cm3: float
    volume_weight: float
    service_type: str  # "freight" | "express"
    courier: str
    category: str  # "线上快运" | "线上快递"
    service_level: str
    max_dimension_cm: float = 0.0


@dataclass
class PricingOutput:
    """三层定价的计算结果。"""
    xianyu_first: float
    xianyu_extra: float
    extra_fee: float
    surcharges: dict[str, float]
    billing_weight: float
    volume_weight_kg: float
    volume_divisor: float
    first_add: float
    extra_add: float
    first_discount: float
    extra_discount: float
    mini_first: float
    mini_extra: float
    oversize_warning: bool
    eta_minutes: int


def compute_three_tier_price(
    inp: PricingInput,
    *,
    category_markup: dict,
    xianyu_discount_rules: dict,
    markup_rules: dict,
    pricing_profile: str,
    volume_divisors: dict,
    volume_divisor_default: float,
    cost_row_throw_ratio: float | None = None,
    api_billable_weight: float | None = None,
) -> PricingOutput:
    """统一的三层定价计算。"""
    # 1. 解析加价规则
    if category_markup:
        first_add, extra_add = _resolve_category_markup(category_markup, inp.category, inp.courier)
        first_discount, extra_discount = _resolve_xianyu_discount_value(
            xianyu_discount_rules, inp.category, inp.courier
        )
    else:
        markup = _resolve_markup(markup_rules, inp.courier)
        first_add, extra_add = _profile_markup(markup, pricing_profile)
        first_discount, extra_discount = 0.0, 0.0

    # 2. 计费重量
    courier_divisor = _resolve_volume_divisor(volume_divisors, inp.category, inp.courier, volume_divisor_default)
    divisor = _first_positive(courier_divisor, cost_row_throw_ratio, volume_divisor_default)
    volume_weight = _derive_volume_weight_kg(
        volume_cm3=inp.volume_cm3,
        explicit_volume_weight=inp.volume_weight,
        divisor=divisor,
    )
    weights = [inp.actual_weight, volume_weight]
    if api_billable_weight:
        weights.append(api_billable_weight)
    billing_weight = max(weights)

    # 3. 三层计算
    extra_weight = max(0.0, billing_weight - inp.base_weight)
    mini_first = inp.first_cost + first_add
    mini_extra = inp.extra_cost + extra_add
    xianyu_first = max(0.0, mini_first - first_discount)
    xianyu_extra = max(0.0, mini_extra - extra_discount)
    extra_fee = extra_weight * xianyu_extra

    surcharges: dict[str, float] = {}
    if extra_fee > 0:
        surcharges["续重"] = round(extra_fee, 2)

    # 4. 超长警告
    oversize_threshold = 150.0 if inp.service_type == "freight" else 120.0
    oversize_warning = inp.max_dimension_cm > oversize_threshold if inp.max_dimension_cm > 0 else False

    return PricingOutput(
        xianyu_first=round(xianyu_first, 2),
        xianyu_extra=round(xianyu_extra, 2),
        extra_fee=extra_fee,
        surcharges=surcharges,
        billing_weight=billing_weight,
        volume_weight_kg=volume_weight,
        volume_divisor=divisor,
        first_add=first_add,
        extra_add=extra_add,
        first_discount=first_discount,
        extra_discount=extra_discount,
        mini_first=round(mini_first, 2),
        mini_extra=round(mini_extra, 2),
        oversize_warning=oversize_warning,
        eta_minutes=_eta_by_service_level(inp.service_level),
    )
```

- [x] **Step 2: 编写测试**

在 `tests/test_quote_pricing_calculator.py` 中：

```python
import pytest
from src.modules.quote.pricing_calculator import compute_three_tier_price, PricingInput


def test_basic_three_tier_pricing():
    inp = PricingInput(
        first_cost=10.0, extra_cost=2.0, base_weight=1.0,
        actual_weight=2.0, volume_cm3=0, volume_weight=0,
        service_type="express", courier="顺丰", category="线上快递",
        service_level="standard",
    )
    out = compute_three_tier_price(
        inp,
        category_markup={},
        xianyu_discount_rules={},
        markup_rules={"default": {"normal_first_add": 0.5, "normal_extra_add": 0.5,
                                   "member_first_add": 0.25, "member_extra_add": 0.3}},
        pricing_profile="normal",
        volume_divisors={},
        volume_divisor_default=0,
    )
    assert out.xianyu_first == 10.5
    assert out.billing_weight == 2.0
    assert out.extra_fee > 0
    assert "续重" in out.surcharges
```

- [x] **Step 3: 运行测试确认通过**

Run: `python -m pytest tests/test_quote_pricing_calculator.py -v`

- [x] **Step 4: 重构 `CostTableMarkupQuoteProvider.get_quote()` 使用新函数**

将 `providers.py` 中 `CostTableMarkupQuoteProvider.get_quote()` 的定价计算部分替换为调用 `compute_three_tier_price()`，保持 `QuoteResult` 结构不变。

- [x] **Step 5: 重构 `ApiCostMarkupQuoteProvider.get_quote()` 使用新函数**

同样替换 API provider 的定价计算部分。

- [x] **Step 6: 运行全量报价测试确认无回归**

Run: `python -m pytest tests/test_quote_engine.py tests/test_quote_engine_full.py tests/test_quote_fuzzy.py -v`

- [x] **Step 7: 提交**

```bash
git add src/modules/quote/pricing_calculator.py src/modules/quote/providers.py src/modules/quote/__init__.py tests/test_quote_pricing_calculator.py
git commit -m "refactor(quote): extract shared three-tier pricing logic into pricing_calculator"
```

---

## Task 2: 提取 format_eta_days 共享函数

**Files:**
- Modify: `src/modules/quote/models.py:98-107`
- Modify: `src/modules/messages/quote_composer.py:38-50`
- Create: `src/modules/quote/utils.py`

**问题：** `QuoteResult._format_days_from_minutes()` 和 `QuoteReplyComposer.format_eta_days()` 逻辑完全相同。

- [x] **Step 1: 创建 `src/modules/quote/utils.py`**

```python
"""报价模块共享工具函数。"""
from __future__ import annotations


def format_eta_days(minutes: int | float | None) -> str:
    """将分钟数转换为友好的天数显示。"""
    try:
        raw = float(minutes or 0)
    except (TypeError, ValueError):
        raw = 0.0
    if raw <= 0:
        return "1天"
    days = max(1.0, raw / 1440.0)
    rounded = round(days, 1)
    if abs(rounded - round(rounded)) < 1e-9:
        return f"{round(rounded)}天"
    return f"{rounded:.1f}天"
```

- [x] **Step 2: 修改 `models.py` 和 `quote_composer.py` 调用共享函数**

```python
# models.py — 替换 _format_days_from_minutes 为:
from src.modules.quote.utils import format_eta_days

# 静态方法委托
@staticmethod
def _format_days_from_minutes(minutes):
    return format_eta_days(minutes)

# quote_composer.py — 替换 format_eta_days 为:
from src.modules.quote.utils import format_eta_days
# 类方法委托
@staticmethod
def format_eta_days(minutes):
    return format_eta_days(minutes)
```

- [x] **Step 3: 运行测试**

Run: `python -m pytest tests/test_quote_models.py tests/test_quote_route.py -v`

- [x] **Step 4: 提交**

```bash
git add src/modules/quote/utils.py src/modules/quote/models.py src/modules/messages/quote_composer.py
git commit -m "refactor(quote): extract format_eta_days into shared utils"
```

---

## Task 3: 提取 CookieCloudClient 统一凭证读取

**Files:**
- Create: `src/core/cookie_cloud_client.py`
- Modify: `src/core/cookie_grabber.py` (删除重复的 UUID/password 读取)
- Modify: `src/dashboard/mimic_ops.py` (删除重复的 UUID/password 读取)
- Modify: `src/dashboard_server.py` (删除重复的 AES-CBC 解密)
- Test: `tests/test_cookie_cloud_client.py`

**问题：** CookieCloud 凭证读取和 AES-CBC 解密在 `cookie_grabber.py`、`mimic_ops.py`、`dashboard_server.py` 三处重复。

- [x] **Step 1: 创建 `src/core/cookie_cloud_client.py`**

提取以下内容为独立类：
- UUID/密码从配置读取的逻辑
- AES-CBC 解密逻辑（legacy CryptoJS 格式 + fixed mode）
- `is_configured()` 检查方法

```python
"""CookieCloud 客户端 — 统一凭证管理与解密。"""
from __future__ import annotations
import base64, hashlib, json
from typing import Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class CookieCloudClient:
    """CookieCloud 凭证读取与数据解密。"""

    def __init__(self, uuid: str = "", password: str = "", server: str = ""):
        self.uuid = uuid.strip()
        self.password = password.strip()
        self.server = server.strip()

    @classmethod
    def from_config(cls) -> "CookieCloudClient":
        """从运行时配置创建实例。"""
        from src.core.config import get_config
        cfg = get_config()
        cc = cfg.get("cookie_cloud", {})
        return cls(
            uuid=cc.get("uuid", ""),
            password=cc.get("password", ""),
            server=cc.get("server", ""),
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.uuid and self.password)

    def decrypt(self, encrypted_data: str) -> dict[str, Any]:
        """解密 CookieCloud 数据。"""
        # 将现有 AES-CBC 解密逻辑集中在此处
        ...
```

- [x] **Step 2: 编写测试**

```python
def test_cookie_cloud_client_not_configured():
    client = CookieCloudClient()
    assert not client.is_configured

def test_cookie_cloud_client_configured():
    client = CookieCloudClient(uuid="abc", password="123", server="https://cc.example.com")
    assert client.is_configured
```

- [x] **Step 3: 修改三个消费方使用 CookieCloudClient**

将 `cookie_grabber.py`、`mimic_ops.py`、`dashboard_server.py` 中的重复代码替换为 `CookieCloudClient.from_config()` 调用。

- [x] **Step 4: 运行测试**

Run: `python -m pytest tests/test_cookie_cloud_client.py tests/test_cookie_health.py tests/test_cookie_store_full.py -v`

- [x] **Step 5: 提交**

```bash
git add src/core/cookie_cloud_client.py src/core/cookie_grabber.py src/dashboard/mimic_ops.py src/dashboard_server.py tests/test_cookie_cloud_client.py
git commit -m "refactor(cookie): extract CookieCloudClient to unify credential reading and decryption"
```

---

## Task 4: 精简错误处理装饰器

**Files:**
- Modify: `src/core/error_handler.py`
- Test: `tests/test_error_handler.py`, `tests/test_core_error_handler_full.py`

**问题：** 6 个装饰器中 `handle_errors` 和 `safe_execute` 几乎相同。`handle_controller_errors` 和 `handle_operation_errors` 逻辑高度相似。

- [x] **Step 1: 合并为 3 个核心装饰器**

保留：
- `safe_execute` — 通用安全执行（合并 `handle_errors` 的功能，增加 `log_level` 参数）
- `retry` — 重试逻辑（保留不变）
- `log_execution_time` — 性能计时（保留不变）

删除：
- `handle_errors` → 合并到 `safe_execute`，添加 `log_level: str = "error"` 参数
- `handle_controller_errors` → 用 `safe_execute(log_level="warning")` 替代
- `handle_operation_errors` → 用 `safe_execute(log_level="debug")` 替代

```python
def safe_execute(
    logger=None,
    default_return: Any = None,
    raise_on_error: bool = False,
    log_level: str = "debug",
    catch: tuple = (Exception,),
):
    """统一的安全执行装饰器。

    Args:
        log_level: 日志级别 "debug" | "warning" | "error"
        catch: 需要捕获的异常类型
    """
    ...
```

- [x] **Step 2: 全局替换引用**

搜索所有 `handle_controller_errors`、`handle_operation_errors`、`handle_errors` 的使用处，替换为 `safe_execute` 的对应参数形式。

- [x] **Step 3: 运行测试确认无回归**

Run: `python -m pytest tests/test_error_handler.py tests/test_core_error_handler_full.py -v`

- [x] **Step 4: 提交**

```bash
git add src/core/error_handler.py
git commit -m "refactor(error): consolidate 6 error decorators into 3 core ones"
```

---

## Task 5: 外部化硬编码业务数据

**Files:**
- Create: `data/quote_data/item_weights.json`
- Create: `data/quote_data/courier_aliases.json`
- Create: `data/quote_data/region_aliases.json`
- Create: `data/shipping_regions.json` (省市区数据)
- Modify: `src/modules/quote/quote_parser.py` (ITEM_WEIGHT_MAP → JSON)
- Modify: `src/modules/quote/cost_table.py` (COURIER_ALIASES, REGION_ALIASES → JSON)
- Modify: `src/dashboard/config_service.py` (SHIPPING_REGIONS → JSON)
- Test: 各模块现有测试

**问题：** 65 条意图规则、73 条快递别名、70+ 条地区别名、115 条物品重量、200+ 行省市区数据硬编码在 Python 源码中。

- [x] **Step 1: 创建数据目录和 JSON 文件**

将 `quote_parser.py` 的 `ITEM_WEIGHT_MAP` 提取到 `data/quote_data/item_weights.json`：

```json
{
  "iPhone 15": 0.17,
  "iPhone 15 Pro": 0.19,
  "iPad": 0.48,
  ...
}
```

将 `cost_table.py` 的 `COURIER_ALIASES` 提取到 `data/quote_data/courier_aliases.json`。

将 `cost_table.py` 的 `REGION_ALIASES` 提取到 `data/quote_data/region_aliases.json`。

将 `config_service.py` 的 `SHIPPING_REGIONS` 提取到 `data/shipping_regions.json`。

- [x] **Step 2: 修改源码加载 JSON 数据**

```python
# quote_parser.py — 替换硬编码:
import json
from pathlib import Path

_ITEM_WEIGHT_PATH = Path("data/quote_data/item_weights.json")

def _load_item_weights() -> dict[str, float]:
    if _ITEM_WEIGHT_PATH.exists():
        with open(_ITEM_WEIGHT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}  # fallback
```

- [x] **Step 3: 运行测试**

Run: `python -m pytest tests/ -q`

- [x] **Step 4: 提交**

```bash
git add data/quote_data/ data/shipping_regions.json src/modules/quote/quote_parser.py src/modules/quote/cost_table.py src/dashboard/config_service.py
git commit -m "refactor: externalize hardcoded business data to JSON files"
```

---

## Task 6: 引入 SQLite 连接池

**Files:**
- Create: `src/core/database.py`
- Modify: `src/modules/messages/workflow.py` (_connect → 连接池)
- Modify: `src/modules/virtual_goods/service.py` (_connect → 连接池)
- Modify: `src/dashboard/repository.py` (_connect → 连接池)
- Test: `tests/test_database_pool.py`

**问题：** 每个数据库操作都通过 `_connect()` 创建新连接再关闭，增加不必要的开销。

- [x] **Step 1: 创建 `src/core/database.py`**

```python
"""SQLite 连接池管理。"""
from __future__ import annotations
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator


class SQLiteDatabase:
    """带 WAL 模式的 SQLite 数据库管理器。"""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """初始化数据库连接，启用 WAL 模式。"""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA busy_timeout=5000")

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """获取数据库连接（共享单连接 + 事务锁）。"""
        if self._connection is None:
            await self.initialize()
        assert self._connection is not None
        try:
            yield self._connection
        except Exception:
            await self._connection.rollback()
            raise

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None
```

- [x] **Step 2: 编写测试**

```python
import pytest
import tempfile
from src.core.database import SQLiteDatabase


@pytest.mark.asyncio
async def test_database_wal_mode():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        db = SQLiteDatabase(f.name)
        await db.initialize()
        async with db.connection() as conn:
            await conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
            await conn.execute("INSERT INTO test VALUES (1, 'hello')")
            await conn.commit()
            cursor = await conn.execute("SELECT val FROM test")
            row = await cursor.fetchone()
            assert dict(row)["val"] == "hello"
        await db.close()
```

- [x] **Step 3: 逐个替换 workflow.py、service.py、repository.py 的 `_connect()`**

在每个文件中，将 `_connect()` 替换为注入的 `SQLiteDatabase` 实例的 `connection()` 上下文管理器。

- [x] **Step 4: 运行测试**

Run: `python -m pytest tests/test_database_pool.py tests/test_workflow.py tests/test_orders.py -v`

- [x] **Step 5: 提交**

```bash
git add src/core/database.py src/modules/messages/workflow.py src/modules/virtual_goods/service.py src/dashboard/repository.py tests/test_database_pool.py
git commit -m "refactor(db): introduce SQLiteDatabase connection manager, eliminate per-query _connect()"
```

---

## Task 7: 消除 MimicOps 中的委托样板代码

**Files:**
- Modify: `src/dashboard/mimic_ops.py` (删除 ~140 行委托方法)

**问题：** `MimicOps` 中有约 140 行纯委托方法（如 `def diagnose_cookie(self, ...): return CookieService.diagnose_cookie(...)`）。

- [x] **Step 1: 添加 `__getattr__` 委托**

```python
# 在 MimicOps 类中添加:
_SERVICES = {
    "cookie": "CookieService",
    "xgj": "XGJService",
}

def __getattr__(self, name: str):
    """自动委托到子服务。"""
    # cookie 相关方法委托到 CookieService
    cookie_methods = {
        "diagnose_cookie", "validate_cookie_keys", "parse_cookie_text",
        "get_cookie_status_summary", "import_cookie_plugin_files",
    }
    if name in cookie_methods:
        from src.dashboard.services.cookie_service import CookieService
        return getattr(CookieService, name)

    # xgj 相关方法委托到 XGJService
    xgj_methods = {
        "get_xgj_products", "sync_xgj_products", "get_xgj_orders",
        "modify_order_price", "push_order_delivery",
    }
    if name in xgj_methods:
        from src.dashboard.services.xgj_service import XGJService
        service = XGJService.get_instance()
        return getattr(service, name)

    raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
```

- [x] **Step 2: 删除原有的 140 行委托方法**

删除 `mimic_ops.py` 中所有一行委托方法（保留有额外逻辑的方法）。

- [x] **Step 3: 运行测试确认路由正常**

Run: `python -m pytest tests/test_dashboard_routes_full.py tests/test_dashboard_router.py -v`

- [x] **Step 4: 提交**

```bash
git add src/dashboard/mimic_ops.py
git commit -m "refactor(mimic_ops): replace 140 lines of delegation boilerplate with __getattr__"
```

---

## Task 8: 移除重复的数据库迁移文件

**Files:**
- Delete: `database/migrations/20260306_wave_b1_virtual_goods_tables.sql`

**问题：** `wave_b_virtual_goods.sql` 和 `wave_b1_virtual_goods_tables.sql` 是完全重复的。

- [x] **Step 1: 确认两个文件内容完全相同**

Run: `diff database/migrations/20260306_wave_b_virtual_goods.sql database/migrations/20260306_wave_b1_virtual_goods_tables.sql`

- [x] **Step 2: 删除重复文件并提交**

```bash
git rm database/migrations/20260306_wave_b1_virtual_goods_tables.sql
git commit -m "chore: remove duplicate migration file wave_b1"
```

---

## Task 9: 清理依赖管理

**Files:**
- Modify: `requirements.txt`
- Modify: `requirements-dev.txt`

**问题：** pytest/pytest-cov 在主依赖中；requirements.lock 过时；同时使用 black 和 ruff。

- [x] **Step 1: 将 pytest 相关依赖移到 dev 依赖**

从 `requirements.txt` 移除：
```
pytest>=7.4.0,<9.0.0
pytest-asyncio>=0.23.0,<1.0.0
pytest-cov>=4.1.0,<6.0.0
```

添加到 `requirements-dev.txt`。

- [x] **Step 2: 从 dev 依赖移除 black（已有 ruff format）**

从 `requirements-dev.txt` 移除 `black`。

- [x] **Step 3: 更新 requirements.lock**

Run: `pip freeze > requirements.lock`

- [x] **Step 4: 提交**

```bash
git add requirements.txt requirements-dev.txt requirements.lock
git commit -m "chore: move pytest to dev deps, remove redundant black, update lock file"
```

---

## 完成标准

- [x] Provider 定价逻辑无重复（共享 `pricing_calculator.py`）
- [x] `format_eta_days` 单一来源（`quote/utils.py`）
- [x] CookieCloud 凭证读取单一来源（`CookieCloudClient`）
- [x] 错误处理装饰器从 6 个精简到 3 个
- [x] 硬编码业务数据外部化为 JSON 文件
- [x] SQLite 使用连接池而非每次新建连接
- [x] MimicOps 无委托样板代码
- [x] 重复迁移文件已删除
- [x] 依赖管理已清理
- [x] `python -m pytest tests/ -q` 全部通过
