# QA Release Verdict

- **任务ID**: `XY-QA-API-FIRST-MAIN-20260307`
- **执行时间**: `2026-03-07 06:27` (Asia/Shanghai)
- **执行目录**: `/Users/peterzhang/xianyu-openclaw`
- **结论**: `Go（有条件）`

## 1. 执行命令

```bash
cd /Users/peterzhang/xianyu-openclaw
cd client && npm run build
cd ../server && npm test -- --runInBand
cd .. && python3 -m compileall src
cd .. && .venv/bin/python -m pytest --tb=short -q

.venv/bin/python -m src.dashboard_server --host 127.0.0.1 --port 18091
PORT=13001 PYTHON_API_URL=http://127.0.0.1:18091 node server/src/app.js
curl -fsS http://127.0.0.1:18091/healthz
curl -fsS http://127.0.0.1:18091/api/config/sections
curl -fsS http://127.0.0.1:18091/api/accounts
curl -fsS http://127.0.0.1:13001/health
curl -fsS http://127.0.0.1:13001/api/config/sections
```

## 2. 检查结果

- 前端构建通过
  - `vite build`
  - 输出产物：`dist/index.html`、`dist/assets/index-*.css`、`dist/assets/index-*.js`
- Node 测试通过
  - `2` 个 suite，`6` 个测试全部通过
- Python 编译通过
  - `python3 -m compileall src`
- Python 全量测试通过
  - `891 passed in 68.99s`
- 本地 smoke 通过
  - Python `/healthz`
  - Python `/api/config/sections`
  - Python `/api/accounts`
  - Node `/health`
  - Node `/api/config/sections`

## 3. 覆盖率结论

基于本次全量 pytest 输出：

- `Required test coverage of 60% reached`
- `Total coverage: 89.04%`

## 4. 发现与处置

### 已处理

- `tests/test_targeted_xy_cov_009.py::test_setup_wizard_start_now_runs_post_checks`
  - 原因：`setup_wizard.run_setup()` 新增闲管家字段提问后，兼容测试输入序列耗尽。
  - 处置：将闲管家配置恢复为“沿用现有值或后续在 `/config` 配置”，并调整向导提问顺序。
  - 结果：相关向导测试恢复通过，全量 pytest 重新跑通。

### 非阻断观察项

- 系统 Python 未安装项目依赖时，直接运行 `python3 -m src.dashboard_server` 会因缺少 `httpx` 失败。
  - 当前口径已统一为使用 `.venv/bin/python` 或 `./start.sh` / `start.bat` 启动。
  - 这不是代码缺陷，但部署文档必须继续保持该前提。

## 5. 发布建议

### Go（有条件）

放行理由：

1. 当前 `main` 的前端、Node、Python 三类检查均通过。
2. 全量测试基线已经更新到 `891` 个用例，并全部通过。
3. 本地 smoke 已验证核心服务和关键配置接口可用。
4. 主文档、部署文档、API 文档和 release 文档已同步到 API-first 现状。

上线前仍需补的最后一项：

- 使用真实 `XGJ_APP_KEY / XGJ_APP_SECRET` 在目标环境做一次外部联调，确认商品、订单、自动上架和回调链路。
