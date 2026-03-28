# Contributing to xianyuflow

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm

### Install

```bash
git clone https://github.com/G3niusYukki/realxianyu.git
cd realxianyu
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd client && npm install && cd ..
```

### Docker Setup

```bash
docker-compose up -d
```

Dashboard UI at `http://127.0.0.1:8091/`, Gateway API at `http://127.0.0.1:8000/`.

## Project Layout

```
src/
├── cli/                # CLI entry point (python -m src.cli)
├── core/               # Config, logging, browser client, crypto, cookie_grabber
├── modules/            # Business logic: messages, orders, quote, listing, virtual_goods, ...
├── dashboard/          # Dashboard facade (mimic_ops.py) + routes + services
├── integrations/       # Third-party integrations (xianguanjia)
├── dashboard_server.py # HTTP server entry
└── main.py             # Python program entry
client/                 # React frontend (Vite + Tailwind)
services/
  gateway-service/      # Open Platform gateway (FastAPI)
  common/               # Shared libraries (Pydantic config)
tests/                  # Python test suite (100+ files)
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
4. Run linting: `ruff check src/`
5. Run Python tests: `./venv/bin/python -m pytest tests/ -q`
6. Run frontend tests: `cd client && npm test`
7. Build frontend: `cd client && npm run build`
8. Commit with a clear message: `git commit -m "feat: add price optimization"`
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
- `loguru` for logging (not `print`)
- Structured JSON output from CLI commands

## Frontend Testing

The frontend uses [Vitest](https://vitest.dev/) with [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/):

```bash
cd client
npm test            # Run all frontend tests
npm run test:run    # Single run (no watch)
npm run build       # Verify production build
```

Test files are co-located alongside source files in `__tests__/` directories (e.g., `src/components/__tests__/Pagination.test.tsx`).

Key dependencies: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`.

## Need Help?

Open an issue or start a [discussion](https://github.com/G3niusYukki/realxianyu/discussions).
