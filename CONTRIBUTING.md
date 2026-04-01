# Contributing to xianyuflow

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/G3niusYukki/realxianyu.git
cd realxianyu
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd client && npm install && npm run build && cd ..
# Optional for lint/type tooling:
pip install -r requirements-dev.txt
```

## Project Layout

```
src/
├── cli/                # CLI entry point (python -m src.cli)
├── core/               # Config, logging, browser client, crypto, cookie, database (24 modules)
├── modules/            # Business logic (14 modules: messages, orders, quote, listing, virtual_goods, ...)
├── dashboard/          # Dashboard facade (mimic_ops.py, 337 lines) + routes + services
│   ├── mimic_ops.py    # Facade proxy (337 lines，不含业务逻辑)
│   ├── services/       # Extracted business services (12 files, 4,291 lines)
│   │   ├── cookie_service.py    # Cookie 管理 (787 lines)
│   │   ├── xgj_service.py       # 闲管家集成 (597 行)
│   │   ├── status_service.py     # 状态管理 (370 行)
│   │   ├── vg_dashboard_service.py # 虚拟商品 Dashboard (469 行)
│   │   ├── log_service.py        # 日志服务 (567 行)
│   │   ├── template_service.py # 模板服务 (149 行)
│   │   ├── env_service.py        # 环境变量服务 (66 行)
│   │   ├── reply_test_service.py # 回复测试 (100 行)
│   │   └── quote/             # 报价子包
│   │       ├── facade.py, RouteHandler.py, MarkupHandler.py, cost_handler.py
│   ├── server/
│   │   └── middleware.py     # CORS + API Token 鉴权 (97 行)
│   ├── config_service.py       # Dashboard 配置 CRUD
│   ├── module_console.py       # 模块控制台
│   └── routes/                  # HTTP 路由（11 files）
├── integrations/       # Third-party integrations (xianguanjia)
│   ├── signing.py           # 笾名算法
│   ├── open_platform_client.py
│   ├── virtual_supply_client.py
│   └── errors.py,             # 错误映射
├── dashboard_server.py # HTTP 服务器入口
└── main.py             # Python 程序入口（非常驻服务)
client/                 React + Vite + Tailwind 前端
tests/
  unit/                     单元测试（106 文件）
  └── integration/              集成测试（16 文件）
scripts/                # Build, deploy, and utility scripts
```
└── cli/                # CLI entry point (python -m src.cli)
├── core/               # Config, logging, browser client, crypto, cookie, database (24 modules)
├── modules/            # Business logic (14 modules: messages, orders, quote, listing, virtual_goods, ...)
├── dashboard/          # Dashboard facade (mimic_ops.py, 337 lines) + routes + services
│   ├── mimic_ops.py    # Facade proxy — delegates to services
│   ├── services/       # Extracted business services (12 files, 4,291 lines)
│   ├── server/         # Middleware (CORS, auth)
│   └── routes/         # HTTP route handlers (11 files)
├── integrations/       # Third-party integrations (xianguanjia)
├── dashboard_server.py # HTTP server entry
└── main.py             # Python program entry
client/                 React frontend (Vite + Tailwind)
tests/
├── unit/               # Unit tests (106 files)
└── integration/              # Integration tests (16 files)
scripts/                # Build, deploy, and utility scripts
```

## How to Contribute

### Bug Reports

Open an [issue](https://github.com/G3niusYukki/realxianyu/issues/new?template=bug_report.md) with:
- What you expected
- What actually happened
- Steps to reproduce
- Logs (from `logs/app.log` or terminal output)

### Feature Requests

Open an [issue](https://github.com/G3niusYukki/realxianyu/issues/new?template=feature_request.md) describing the use case.

### Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run linting: `./venv/bin/python -m ruff check src/ services/`
5. Run format check: `./venv/bin/python -m ruff format src/ services/ --check`
6. Run tests: `./venv/bin/python -m pytest tests/ -q`
7. Unit tests only: `./venv/bin/python -m pytest tests/unit/ -q`
8. Integration tests: `./venv/bin/python -m pytest tests/integration/ -q`
6. Commit with a clear message: `git commit -m "feat: add price optimization"`
7. Push to your fork and open a PR

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | When to use |
|--------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code restructuring (no behavior change) |
| `test:` | Adding or updating tests |
| `chore:` | Build, CI, dependency updates |

## Versioning (版本号规范)

项目遵循 [Semantic Versioning 2.0.0](https://semver.org/lang/zh-CN/) (语义化版本)。

版本号格式：`MAJOR.MINOR.PATCH`

| 变更类型 | 版本位 | 何时递增 | 示例 |
|----------|--------|---------|------|
| **MAJOR** | 主版本 | 架构重构、破坏性变更、大规模重写 | 重构消息引擎 → 9.0.0 |
| **MINOR** | 次版本 | 新增功能（向后兼容） | 新增议价动态回复 → 9.4.0 |
| **PATCH** | 修订号 | Bug 修复、小优化（向后兼容） | 修复去重标记 → 9.4.1 |

### 版本号存储位置（唯一真相源）

版本号定义在 `src/__init__.py` 的 `__version__` 变量中。修改版本时 **必须同步更新**：

1. `src/__init__.py` — `__version__ = "X.Y.Z"` (Python 后端读取)
2. `package.json` — `"version": "X.Y.Z"` (npm 元数据)

`scripts/build_release.sh` 会自动从 `src/__init__.py` 读取版本号生成发布包，无需手动改。

### 何时更新版本号

- 每次准备发布新 Release 前更新，不要在开发中频繁修改
- git tag 必须与 `__version__` 一致：`git tag v9.5.0`
- GitHub Release 标题格式：`v9.5.0`

### 禁止事项

- 不得回退版本号（如从 8.0.0 改回 1.0.0）
- 不得跳过版本号（如从 8.0.0 跳到 10.0.0）
- 不得使用非数字后缀（如 8.0.0-beta）除非团队明确约定

## Code Style

- Python 3.12+
- Type hints everywhere
- Use `async/await` for I/O operations
- Python `logging` module (`logging.getLogger(__name__)`)
- Structured JSON output from CLI commands

## Need Help?

Open an issue or start a [discussion](https://github.com/G3niusYukki/realxianyu/discussions).
