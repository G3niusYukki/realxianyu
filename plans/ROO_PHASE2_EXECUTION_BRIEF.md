# Roo Phase 2 执行简报（指挥官下达）

> 下达时间：2026-03-14  
> **当前状态**：Phase 2.1–2.5 已完成（5 commits）  
> **dashboard_server.py**：6048 → 5481 行（-9.4%），已迁移 39/91 路由（43%）  
> **下一步**：Phase 2.6 routes/cookie.py  
> 依据：`plans/dashboard-server-refactor-plan.md` v2

---

## 一、执行原则

1. **每完成一个路由文件 → 提交一个 commit**，便于回滚和 code review
2. **迁移模式**：从 `dashboard_server.py` 提取 if-else 逻辑到 `routes/<name>.py`，使用 `@get(path)` / `@post(path)` 装饰器 + `RouteContext`
3. **不改变业务逻辑**：只做机械搬迁，保持原有 `mimic_ops` 调用不变
4. **验证**：每个文件迁移后运行 `pytest tests/test_*dashboard* -q --tb=short` 并手动 curl 2–3 个端点

---

## 二、Phase 2.2：routes/dashboard_data.py

### 2.1 路由清单（8 个）

| # | 方法 | 路径 | mimic_ops 调用 | 特殊处理 |
|---|------|------|----------------|----------|
| 1 | GET | `/api/summary` | 内联逻辑（非 mimic_ops） | 见 4102–4118 行 |
| 2 | GET | `/api/top-products` | 同上 | 见 4110–4118 行 |
| 3 | GET | `/api/recent-operations` | 同上 | 见 4119–4127 行 |
| 4 | GET | `/api/trend` | 同上 | 见 4128–4136 行 |
| 5 | GET | `/api/dashboard` | `get_dashboard_readonly_aggregate()` | 4447–4450 |
| 6 | GET | `/api/logs/files` | `list_log_files()` | 4359–4361 |
| 7 | GET | `/api/logs/content` | `read_log_content(file_name, tail, page, size, search)` | 4363–4385，含分页/搜索分支 |
| 8 | GET | `/api/logs/realtime/stream` | SSE 流，`read_log_content` 轮询 | 4387–4416，需 `ctx._handler.send_response/wfile` 等 |

**注意**：`/api/summary`、`/api/top-products`、`/api/recent-operations`、`/api/trend` 均由 `_legacy_dashboard_payload(path, query)` 统一处理（先尝试 xianguanjia API，失败则 fallback 到 repo）。迁移时：**保留** `_legacy_dashboard_payload` 在 `DashboardHandler` 上，4 个路由各自调用 `ctx._handler._legacy_dashboard_payload(ctx.path, ctx.query)` 即可。

### 2.2 RouteContext 能力缺口

`/api/logs/realtime/stream` 需要直接写 SSE 到 `wfile`，当前 `RouteContext` 可能没有暴露。可选方案：

- 在 `RouteContext` 增加 `write_sse(data: str)` 或 `raw_response()` 供流式响应使用  
- 或通过 `ctx._handler` 访问 `self.send_response` / `self.wfile`（约定为仅此路由使用）

建议：先实现，若需 `ctx._handler.wfile` 等，在路由内使用并在注释中标明「流式响应例外」。

### 2.3 实现模板

```python
# routes/dashboard_data.py
"""Dashboard legacy data + log viewer routes."""

from src.dashboard.router import get, RouteContext

@get("/api/dashboard")
def handle_dashboard(ctx: RouteContext) -> None:
    aggregate = ctx.mimic_ops.get_dashboard_readonly_aggregate()
    ctx.send_json(aggregate, status=200 if aggregate.get("success") else 400)

@get("/api/logs/files")
def handle_logs_files(ctx: RouteContext) -> None:
    ctx.send_json(ctx.mimic_ops.list_log_files())
# ... 其余类似
```

### 2.4 完成后动作

1. 在 `routes/__init__.py` 中增加：`from src.dashboard.routes import dashboard_data`
2. 从 `dashboard_server.py` 的 `do_GET` 中删除上述 8 个 if-else 分支
3. 运行测试并 curl 验证
4. 提交：`refactor(dashboard): Phase 2.2 - migrate dashboard_data + logs (8 routes)`

---

## 三、Phase 2.3–2.8 路线图（简要）

| Phase | 文件 | 路由数 | 复杂度 | 备注 |
|-------|------|--------|--------|------|
| 2.2 | dashboard_data.py | 8 | 中 | 含 SSE 流 |
| 2.3 | config.py | ~6 | 低 | config CRUD、intent-rules、manual-mode |
| 2.4 | messages.py | ~6 | 低 | replies、test-reply、notifications/test、ai/test |
| 2.5 | quote.py | ~8 | 中 | 含文件上传 import-markup、save-template |
| 2.6 | cookie.py | ~10 | 中 | 含 SSE、multipart、download |
| 2.7 | orders.py | ~11 | 中 | 含 webhook 验签、callback |
| 2.8 | products.py | ~15 | 中高 | 商品、发布队列、素材、composition |

**建议顺序**：2.2 → 2.3 → 2.4 → 2.5 → 2.6 → 2.7 → 2.8（按方案第四章）

---

## 四、Phase 2.6：routes/cookie.py（待执行）

### 4.1 路由清单（~10 个）

| # | 方法 | 路径 | 说明 |
|---|------|------|------|
| 1 | GET | `/api/get-cookie` | mimic_ops.get_cookie() |
| 2 | GET | `/api/download-cookie-plugin` | mimic_ops.export_cookie_plugin_bundle()，返回 zip，`send_bytes` |
| 3 | GET | `/api/cookie/auto-grab/status` | **SSE 流**，轮询 CookieGrabber 状态 |
| 4 | GET | `/api/cookie/auto-refresh/status` | 检查 _cookie_auto_refresher 状态 |
| 5 | POST | `/api/update-cookie` | json_body().get("cookie")，调用 mimic_ops |
| 6 | POST | `/api/import-cookie-plugin` | **multipart**，ctx.multipart_files() |
| 7 | POST | `/api/parse-cookie` | json_body，mimic_ops.parse_cookie |
| 8 | POST | `/api/cookie-diagnose` | json_body，mimic_ops.cookie_diagnose |
| 9 | POST | `/api/cookie/validate` | json_body，mimic_ops.validate_cookie |
| 10 | POST | `/api/cookie/auto-grab` | 启动 CookieGrabber 后台线程 |
| 11 | POST | `/api/cookie/auto-grab/cancel` | 取消 grabber |

**SSE 注意**：`/api/cookie/auto-grab/status` 与 dashboard_data 的 `/api/logs/realtime/stream` 类似，需 `ctx._handler.send_response` / `wfile` 直写。

---

## 六、常见坑点提醒

1. **`_safe_int` 等辅助函数**：若多路由复用，可放在 `routes/dashboard_data.py` 顶部或 `router.py` 的 utils 中
2. **`_now_iso()`**：`system.py` 已有，dashboard_data 可 `from src.dashboard.routes.system import _now_iso` 或自建
3. **重复路径**：`/api/summary`、`/api/trend` 等在 do_GET 中出现两次，迁移时只保留主逻辑，删除重复分支
4. **virtual_goods 相关**：`/api/virtual-goods/metrics`、`/api/virtual-goods/inspect-order` 属于 **orders.py**（Phase 2.7），不要放入 dashboard_data

---

## 七、指挥官检查点

每完成一个 Phase 2.x，向指挥官报告：

- [ ] 迁移的路由数量
- [ ] `dashboard_server.py` 行数变化（当前基线：5481）
- [ ] 测试通过情况（passed / failed 数量）
- [ ] 是否已提交 commit

---

## 八、新会话启动指令（复制给 Roo）

```
继续 dashboard_server 重构。请阅读 plans/ROO_PHASE2_EXECUTION_BRIEF.md。
Phase 2.1–2.5 已完成，当前 dashboard_server.py 5481 行，39/91 路由已迁移。
下一步：Phase 2.6 routes/cookie.py（~11 路由，含 SSE、multipart、download）。
按简报第四章路由清单迁移，完成后提交并报告检查点。
```

---

*简报结束。按此执行，遇阻及时反馈。*
