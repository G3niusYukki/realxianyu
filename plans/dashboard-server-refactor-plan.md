# dashboard_server.py 拆分方案（v2 — 审查修订版）

> 生成时间：2026-03-14
> 状态：**修订版**（根据审查反馈调整了执行顺序、文件数量、路由设计和 MimicOps 终态）

---

## 一、审查反馈摘要与应对

| # | 审查意见 | 应对 |
|---|----------|------|
| 1 | Phase 顺序应调换：先路由迁移再拆 MimicOps | ✅ 调换为 Phase 2 路由迁移 → Phase 3 拆 MimicOps |
| 2 | 文件数爆炸（21 个新文件） | ✅ 合并低密度路由，控制在 8 个路由文件 + 4 个服务文件 |
| 3 | 路由签名与 DashboardHandler 强耦合 | ✅ router 提取 query/body 参数，路由函数接收结构化上下文 |
| 4 | 前缀路由匹配机制缺失 | ✅ Phase 1 明确前缀路由注册和匹配实现 |
| 5 | MimicOps 应消亡而非保留为 facade | ✅ Phase 4 目标改为移除 MimicOps |

---

## 二、修订后的目标目录结构

```
src/dashboard/
├── __init__.py
├── router.py                      # 路由框架（增强：前缀匹配 + 参数提取）
├── config_service.py              # 已有，保持不变
├── repository.py                  # 已有，保持不变
├── module_console.py              # 已有，保持不变
│
├── routes/                        # 8 个路由文件
│   ├── __init__.py                # 导入所有路由模块触发注册
│   ├── system.py                  # 健康检查 + 服务控制 + 模块管理 + 数据库重置
│   ├── config.py                  # 配置 CRUD + 意图规则 + 人工模式
│   ├── cookie.py                  # Cookie 全生命周期
│   ├── quote.py                   # 报价规则 + 加价规则 + 模板
│   ├── messages.py                # 回复日志 + 对话沙盒 + 通知测试 + AI 测试
│   ├── products.py                # 商品上架 + 发布队列 + 素材管理
│   ├── orders.py                  # 订单回调 + 催单 + 虚拟商品 + 闲管家
│   └── dashboard_data.py          # 仪表盘数据 + 日志查看
│
├── services/                      # 4 个领域服务
│   ├── __init__.py
│   ├── cookie_ops.py              # Cookie 解析/验证/导入/导出/诊断
│   ├── quote_ops.py               # 报价规则解析/导入/导出
│   ├── log_viewer.py              # 日志文件列表/内容读取/风控分析
│   └── env_manager.py             # .env 文件读写
│
└── vendor/                        # 已有，保持不变
```

### 路由文件合并说明

| 路由文件 | 合并了原方案的 | 路由数 |
|----------|---------------|--------|
| `system.py` | health + service_control + modules + database | ~12 |
| `config.py` | config + 部分 messages（intent-rules, manual-mode） | ~6 |
| `cookie.py` | cookie（不变） | ~10 |
| `quote.py` | quote（不变） | ~8 |
| `messages.py` | messages + notifications | ~6 |
| `products.py` | products（不变） | ~15 |
| `orders.py` | orders + virtual_goods + xianguanjia | ~11 |
| `dashboard_data.py` | dashboard_legacy + logs | ~7 |

---

## 三、Phase 1：增强 router.py（风险：极低）

### 3.1 路由上下文设计

```python
# src/dashboard/router.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

if TYPE_CHECKING:
    from src.dashboard_server import DashboardHandler

@dataclass
class RouteContext:
    """路由处理函数接收的结构化上下文。"""
    _handler: DashboardHandler         # 内部引用，路由函数应使用 send_json 等方法
    path: str                          # 请求路径
    query: dict[str, list[str]]        # 已解析的 query params
    path_params: dict[str, str] = field(default_factory=dict)  # 前缀匹配提取的路径参数
    _body_cache: Any = field(default=None, repr=False)

    def query_str(self, key: str, default: str = "") -> str:
        """获取单值 query 参数。"""
        values = self.query.get(key, [])
        return values[0] if values else default

    def query_int(self, key: str, default: int = 0,
                  min_val: int | None = None, max_val: int | None = None) -> int:
        """获取整数 query 参数，支持范围约束。"""
        try:
            n = int(self.query_str(key, str(default)))
        except (TypeError, ValueError):
            n = default
        if min_val is not None:
            n = max(n, min_val)
        if max_val is not None:
            n = min(n, max_val)
        return n

    def json_body(self) -> dict[str, Any]:
        """懒加载 JSON body。"""
        if self._body_cache is None:
            self._body_cache = self._handler._read_json_body()
        return self._body_cache

    def send_json(self, payload: Any, status: int = 200) -> None:
        self._handler._send_json(payload, status=status)

    def send_bytes(self, data: bytes, content_type: str,
                   status: int = 200, download_name: str | None = None) -> None:
        self._handler._send_bytes(data, content_type, status=status,
                                  download_name=download_name)

    def multipart_files(self) -> list[tuple[str, bytes]]:
        """读取 multipart 上传的文件。"""
        return self._handler._read_multipart_files()

    @property
    def repo(self):
        """访问 DashboardRepository。"""
        return self._handler.repo

    @property
    def module_console(self):
        """访问 ModuleConsole。"""
        return self._handler.module_console

    @property
    def mimic_ops(self):
        """访问 MimicOps（Phase 3 后逐步移除）。"""
        return self._handler.mimic_ops
```

### 3.2 前缀路由注册机制

```python
# router.py 中增加

RouteHandler = Callable[[RouteContext], None]

_GET_ROUTES: dict[str, RouteHandler] = {}
_POST_ROUTES: dict[str, RouteHandler] = {}
_PUT_ROUTES: dict[str, RouteHandler] = {}
_DELETE_ROUTES: dict[str, RouteHandler] = {}

# 前缀路由：按注册顺序匹配，最长前缀优先
_GET_PREFIX_ROUTES: list[tuple[str, str, RouteHandler]] = []
# 每个元素: (prefix, param_name, handler)
# 例如: ("/api/brand-assets/file/", "filename", handler)

def get(path: str):
    """注册精确匹配 GET 路由。"""
    def decorator(fn: RouteHandler) -> RouteHandler:
        _GET_ROUTES[path] = fn
        return fn
    return decorator

def get_prefix(prefix: str, param_name: str = "sub_path"):
    """注册前缀匹配 GET 路由，剩余路径存入 ctx.path_params[param_name]。"""
    def decorator(fn: RouteHandler) -> RouteHandler:
        _GET_PREFIX_ROUTES.append((prefix, param_name, fn))
        # 按前缀长度降序排列，确保最长前缀优先匹配
        _GET_PREFIX_ROUTES.sort(key=lambda x: len(x[0]), reverse=True)
        return fn
    return decorator

# POST/PUT/DELETE 同理增加 post_prefix 等

def dispatch_get(path: str, ctx: RouteContext) -> bool:
    """尝试分发 GET 请求。返回 True 表示已处理。"""
    handler = _GET_ROUTES.get(path)
    if handler:
        handler(ctx)
        return True
    for prefix, param_name, handler in _GET_PREFIX_ROUTES:
        if path.startswith(prefix):
            ctx.path_params[param_name] = path[len(prefix):]
            handler(ctx)
            return True
    return False
```

### 3.3 Phase 1 变更清单

| 文件 | 变更 |
|------|------|
| `src/dashboard/router.py` | 新增 `RouteContext`、`get_prefix`/`post_prefix`、`dispatch_*` 函数、`delete` 装饰器 |
| `src/dashboard/routes/__init__.py` | 新建，空文件（后续 Phase 导入用） |

**测试**：仅测试 router.py 本身的注册和分发逻辑，不涉及业务代码。

---

## 四、Phase 2：路由迁移（风险：低）

### 4.1 迁移模式

```python
# 示例：routes/system.py

from src.dashboard.router import get, post, RouteContext

@get("/healthz")
def handle_healthz(ctx: RouteContext) -> None:
    db_ok = False
    try:
        with ctx.repo._connect() as conn:
            conn.execute("SELECT 1")
        db_ok = True
    except Exception:
        pass
    # ... 构建 payload
    ctx.send_json(payload)

@get("/api/module/status")
def handle_module_status(ctx: RouteContext) -> None:
    window = ctx.query_int("window", default=60, min_val=1, max_val=10080)
    limit = ctx.query_int("limit", default=20, min_val=1, max_val=200)
    payload = ctx.module_console.status(window_minutes=window, limit=limit)
    status = 200 if not payload.get("error") else 500
    ctx.send_json(payload, status=status)
```

### 4.2 迁移顺序（8 个文件，按独立性从高到低）

| 顺序 | 文件 | 路由数 | 风险 | 说明 |
|------|------|--------|------|------|
| 1 | `system.py` | 12 | 极低 | 健康检查、模块管理、服务控制 — 最独立 |
| 2 | `dashboard_data.py` | 7 | 低 | 仪表盘数据、日志查看 — 仅读数据 |
| 3 | `config.py` | 6 | 低 | 配置 CRUD、意图规则、人工模式 |
| 4 | `messages.py` | 6 | 低 | 回复日志、对话沙盒、通知/AI 测试 |
| 5 | `quote.py` | 8 | 中 | 报价规则、加价规则（含文件上传） |
| 6 | `cookie.py` | 10 | 中 | Cookie 全生命周期（含文件上传、SSE 流） |
| 7 | `orders.py` | 11 | 中 | 订单、虚拟商品、闲管家（含 webhook 回调） |
| 8 | `products.py` | 15 | 中高 | 商品上架、发布队列、素材（最复杂） |

### 4.3 DashboardHandler 改造

```python
class DashboardHandler(BaseHTTPRequestHandler):
    repo: DashboardRepository
    module_console: ModuleConsole
    mimic_ops: MimicOps  # Phase 3 后移除

    def _build_context(self) -> RouteContext:
        parsed = urlparse(self.path)
        return RouteContext(
            handler=self,
            path=parsed.path,
            query=parse_qs(parsed.query),
        )

    def do_GET(self) -> None:
        ctx = self._build_context()

        # cookie-cloud 特殊处理（混合 GET/POST）
        if ctx.path.startswith("/cookie-cloud/") or ctx.path == "/cookie-cloud":
            self._handle_cookie_cloud(...)
            return

        # 装饰器注册的路由
        if dispatch_get(ctx.path, ctx):
            return

        # SPA 静态文件 fallback
        if ctx.path in {"/", "/cookie", "/test", "/logs", "/logs/realtime"}:
            self._serve_spa_file(ctx.path)
            return

        # vendor 静态文件
        if ctx.path.startswith("/vendor/"):
            self._serve_vendor_file(ctx.path)
            return

        # SPA catch-all
        self._serve_spa_file(ctx.path)

    # do_POST, do_PUT, do_DELETE 同理
```

### 4.4 每个文件迁移后的验证

每迁移一个路由文件：
1. `pytest tests/ -v --tb=short -q` — 全量测试
2. 启动服务，用 curl 验证迁移的路由仍正常工作
3. 确认 `do_GET`/`do_POST` 中对应的 if-else 分支已删除

---

## 五、Phase 3：拆分 MimicOps 为领域服务（风险：中高）

### 5.1 策略变更

原方案保留 MimicOps 为 facade，修订后改为**渐进消亡**：

1. 先将方法搬到领域服务，MimicOps 中保留**转发方法**（一行调用）
2. 路由函数逐步改为直接调用领域服务
3. 当 MimicOps 中所有方法都变成转发后，删除 MimicOps

### 5.2 拆分顺序

| 顺序 | 服务 | 方法数 | 依赖 | 风险 |
|------|------|--------|------|------|
| 1 | `env_manager.py` | 5 | 无外部依赖 | 极低 |
| 2 | `log_viewer.py` | 8 | 仅读文件 | 低 |
| 3 | `cookie_ops.py` | 25 | env_manager + 外部解析 | 中 |
| 4 | `quote_ops.py` | 20 | config + CostTableRepository | 中 |

### 5.3 关键耦合处理

**`update_cookie()` → `_maybe_auto_recover_presales()`**：
- `cookie_ops.py` 提供 `update_cookie()` 方法
- 接受一个可选的 `on_cookie_updated: Callable` 回调
- 在 `run_server()` 初始化时注入回调，回调内部调用 `service_control` 的恢复逻辑

**`get_replies()` 跨库查询**：
- 保持在路由层（`routes/messages.py`）直接实现，不拆到服务层
- 因为它本质是一个**视图查询**，不是领域逻辑

**`test_reply()` 的 `_sandbox_services` 缓存**：
- 保持在路由层（`routes/messages.py`），因为 MessagesService 实例管理是请求级别的

### 5.4 服务初始化

```python
# dashboard_server.py 中 run_server()

from src.dashboard.services.env_manager import EnvManager
from src.dashboard.services.log_viewer import LogViewer
from src.dashboard.services.cookie_ops import CookieOps
from src.dashboard.services.quote_ops import QuoteOps

project_root = Path(__file__).resolve().parents[1]

# 创建服务实例
env_mgr = EnvManager(project_root)
log_viewer = LogViewer(project_root)
cookie_ops = CookieOps(project_root, env_mgr)
quote_ops = QuoteOps(project_root)

# 注入到 Handler 类变量（与现有 repo/module_console 模式一致）
DashboardHandler.env_manager = env_mgr
DashboardHandler.log_viewer = log_viewer
DashboardHandler.cookie_ops = cookie_ops
DashboardHandler.quote_ops = quote_ops
```

---

## 六、Phase 4：移除 MimicOps（风险：低）

### 6.1 前提条件

- 所有路由函数已改为直接调用领域服务或 Handler 类变量上的服务
- MimicOps 中所有方法要么已搬到服务中，要么已内联到路由函数中
- 全量测试通过

### 6.2 变更

1. 删除 `MimicOps` 类
2. 删除 `DashboardHandler.mimic_ops` 类变量
3. `run_server()` 中移除 `MimicOps` 实例化
4. 看门狗逻辑中的 `mimic_ops` 引用改为直接调用 `module_console`

### 6.3 最终 dashboard_server.py 结构

```python
# ~400 行

# 导入
from src.dashboard.router import dispatch_get, dispatch_post, ...
from src.dashboard.routes import *  # 触发路由注册

class DashboardHandler(BaseHTTPRequestHandler):
    # 类变量：由 run_server() 注入
    repo: DashboardRepository
    module_console: ModuleConsole
    env_manager: EnvManager
    log_viewer: LogViewer
    cookie_ops: CookieOps
    quote_ops: QuoteOps

    # HTTP 方法分发（~80 行）
    def do_GET(self) -> None: ...
    def do_POST(self) -> None: ...
    def do_PUT(self) -> None: ...
    def do_DELETE(self) -> None: ...
    def do_OPTIONS(self) -> None: ...

    # 辅助方法（~100 行）
    def _send_json(self, ...) -> None: ...
    def _send_html(self, ...) -> None: ...
    def _send_bytes(self, ...) -> None: ...
    def _send_cors_headers(self) -> None: ...
    def _build_context(self) -> RouteContext: ...
    def _read_json_body(self) -> dict: ...
    def _read_multipart_files(self) -> list: ...
    def _serve_spa_file(self, path) -> None: ...
    def _serve_vendor_file(self, path) -> None: ...

def run_server(...) -> None:
    # 服务初始化 + 看门狗 + 信号处理（~150 行）
    ...
```

---

## 七、风险矩阵

| 风险 | 影响 | 概率 | 缓解 |
|------|------|------|------|
| 路由迁移遗漏某个 if-else 分支 | 对应 API 404 | 中 | 迁移后逐个 curl 验证 |
| 前缀路由匹配顺序错误 | 错误的路由被命中 | 低 | 按前缀长度降序排列 |
| `get_replies()` 跨库查询在路由层实现时丢失逻辑 | 回复日志空白 | 中 | 保持原有代码不动，仅搬位置 |
| Cookie 更新后 presales 恢复失败 | 服务不自愈 | 中 | 回调注入模式，保持调用链完整 |
| `_handle_cookie_cloud` 混合 GET/POST | 拆分后行为不一致 | 低 | 拆为两个独立函数 |
| 看门狗引用 MimicOps | Phase 4 删除后看门狗崩溃 | 低 | 看门狗改为直接调用 module_console |

---

## 八、实施检查清单

### Phase 1 完成标准
- [ ] `router.py` 支持 `RouteContext`、`get_prefix`/`post_prefix`、`delete`
- [ ] `dispatch_get`/`dispatch_post`/`dispatch_put`/`dispatch_delete` 函数可用
- [ ] `routes/__init__.py` 存在
- [ ] router 单元测试通过

### Phase 2 完成标准（每个路由文件）
- [ ] 路由文件创建并注册
- [ ] `dashboard_server.py` 中对应 if-else 分支已删除
- [ ] 全量 pytest 通过
- [ ] curl 验证迁移的路由正常工作

### Phase 3 完成标准（每个服务文件）
- [ ] 服务类创建，方法从 MimicOps 搬入
- [ ] MimicOps 中对应方法改为一行转发
- [ ] 路由函数改为直接调用服务
- [ ] 全量 pytest 通过

### Phase 4 完成标准
- [ ] MimicOps 类已删除
- [ ] `dashboard_server.py` 行数 <= 500
- [ ] 全量 pytest 通过
- [ ] 前端所有页面功能正常
