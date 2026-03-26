# 2026-03-26 Cookie/模块自启/RGV587 修复设计

## 概述

修复三个独立问题：
1. Dashboard "自动获取 cookie" 按钮失败 — `auto_grab()` 缺少 goofish-im fallback
2. Dashboard 启动后只有 presales 运行 — watchdog 不监控 operations/aftersales
3. RGV587 风控全自动恢复 — 确保 BitBrowser 路径畅通，0 人工接管

## 修改 1：auto_grab() 加入 goofish-im fallback

**文件**: `src/core/cookie_grabber.py`

在 `auto_grab()` 方法的 rookiepy 失败后，新增 Level 2：调用 `goofish_im_cookie.read_goofish_im_cookies()`。

```
auto_grab() 当前链路:
  Level 0: CookieCloud → 失败 →
  Level 1: rookiepy   → 失败 → 返回失败

修改后链路:
  Level 0: CookieCloud → 失败 →
  Level 1: rookiepy   → 失败 →
  Level 2: goofish-im → 失败 → 返回失败
```

改动量：~15 行。在 `auto_grab()` 的 Level 1 和最终返回之间插入一个 `await` 的 goofish-im 读取块，模式与现有两级完全一致（读取 → cancel 检查 → 校验 → 保存 → 返回）。

同时更新失败提示文案，去掉 BitBrowser 强制提及，改为列举可用方式。

## 修改 2：Dashboard 启动自动拉起所有模块

**文件**: `src/dashboard_server.py`

### 2a. 启动时自动拉起

在 `run_server()` 中 watchdog 线程启动之后、`server.serve_forever()` 之前，加入自动启动循环：

```python
# 自动拉起所有业务模块
for _target in ("presales", "operations", "aftersales"):
    try:
        module_console._run_module_cli(
            action="start", target=_target,
            extra_args=["--mode", "daemon", "--background",
                        "--interval", "5", "--limit", "20",
                        "--claim-limit", "10"],
            timeout_seconds=30,
        )
        logger.info("Auto-start: %s 已启动", _target)
    except Exception as exc:
        logger.warning("Auto-start: %s 启动失败: %s", _target, exc)
```

### 2b. Watchdog 扩展监控

将 watchdog 中只检查 presales 的逻辑扩展为循环检查三个模块。每个模块独立计数和重启限制（复用现有 `_WD_MAX_RESTARTS=3` 逻辑）。

改动量：~30 行（启动循环 15 行 + watchdog 循环重构 15 行）。

## 修改 3：RGV587 全自动恢复（BitBrowser 路径畅通）

**文件**: `src/modules/messages/ws_live.py`

当前 RGV587 恢复逻辑已经包含 BitBrowser 路径（line 1673），但需要确认：

1. BitBrowser 运行时，CDD cookie 读取 + slider 解滑块流程是否能自动完成（弹前台窗口）
2. 无 BitBrowser 时，是否应该等待而非反复重试消耗配额

**可能的优化**（需进一步确认代码细节后实施）：

- 检查 `_try_slider_recovery()` 是否能在无 BitBrowser 时正确降级到 DrissionPage
- 确认 BitBrowser CDP 连接失败时的错误处理不会阻塞整个恢复流程
- 如果 BitBrowser 未运行，减少无意义的重试，直接进入 `_wait_for_cookie_update_forever` 等待 cookie 更新

改动量：预计 ~10-20 行微调，不涉及架构变更。

## 不做的事

- 不引入新的配置项（auto-start 默认行为，不需要关闭）
- 不修改 CookieAutoRefresher（_tick() 已经正确使用 goofish-im）
- 不删除 CookieCloud/rookiepy 支持（它们是 fallback，不影响正常路径）
- 不动前端代码

## 测试

- `pytest tests/ -q` 必须全部通过
- 手动验证：重启 Dashboard → 三个模块自动运行 → Dashboard 按健康检查返回 alive_count=3
