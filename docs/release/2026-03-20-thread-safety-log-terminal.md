# 2026-03-20 Thread Safety & Real-time Log Terminal

## 概要

本次发布重点解决代码质量与可观测性问题：

- 6 个单例类全部实现线程安全（双检锁 DCL）
- 模块运行时状态写入改为原子操作
- 新增实时日志终端 UI
- 修复 4 个既有测试失败

## 主要改动

### 代码质量

- **单例线程安全**：为 `GeoKnownCache`、`QuoteLedger`、`WebSocketTransportManager`、`MessageServiceRegistry`、`_HealthCache`、`_VersionCache` 全部添加双检锁，避免多线程/多进程环境下竞态条件
- **静默异常修复**：`MessageServiceRegistry` 加载系统配置时的裸 `except` 改为 `except (OSError, ValueError)` 并记录 debug 日志
- **MTOP 密钥外部化**：`XIANYU_MTOP_APP_KEY` / `XIANYU_MTOP_APP_SECRET` 环境变量可覆盖硬编码默认值
- **模块状态原子写入**：`_write_module_state` 改用 `tempfile.NamedTemporaryFile` + `os.replace()` POSIX 原子替换，进程崩溃时不再损坏 `.json` 文件
- **空字符串判断修复**：`CookieHealthChecker` 用 `is not None` 替代 `or`，正确区分"未传参数"与"空字符串"

### 新功能

- **实时日志终端**：`/日志` 页面新增 4 栏（售前/运营/售后/应用），SSE 流式推送，支持自动滚动、清屏、日志级别颜色区分

### Bug 修复

- 修复 `test_check_sync_no_cookie` / `test_check_async_no_cookie`（空 Cookie 误读环境变量）
- 修复 `test_env_variable_resolution` / `test_env_variable_missing`（单例状态泄漏）

## 发布前检查

- `npm run build` 通过
- `python -m pytest tests/ -q` — 1176 passed, 16 skipped, 0 failed

## 版本

- `src/__init__.py`: 9.2.5 → 9.3.0
- `pyproject.toml`: 9.2.0 → 9.3.0
- `package.json`: 9.2.0 → 9.3.0
