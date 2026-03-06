# Contributing to xianyu-openclaw

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/G3niusYukki/xianyu-openclaw.git
cd xianyu-openclaw
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Project Layout

```
src/
├── cli.py              # CLI entry point
├── core/               # Framework: config, logging, browser client, crypto, cookie_grabber
├── modules/            # Business logic: listing, operations, messages, orders, analytics
├── dashboard_server.py # Python Dashboard API server
└── integrations/       # Third-party integrations (xianguanjia)
server/                 # Node.js backend (config proxy, webhook gate)
client/                 # React frontend (Vite + Tailwind)
tests/                  # Python test suite
```

## How to Contribute

### Bug Reports

Open an [issue](https://github.com/G3niusYukki/xianyu-openclaw/issues/new?template=bug_report.md) with:
- What you expected
- What actually happened
- Steps to reproduce
- Logs (`docker compose logs`)

### Feature Requests

Open an [issue](https://github.com/G3niusYukki/xianyu-openclaw/issues/new?template=feature_request.md) describing the use case.

### Pull Requests

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run linting: `ruff check src/`
5. Run tests: `python -m pytest tests/ -x`
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

## Code Style

- Python 3.10+
- Type hints everywhere
- Use `async/await` for I/O operations
- `loguru` for logging (not `print`)
- Structured JSON output from CLI commands

## Need Help?

Open an issue or start a [discussion](https://github.com/G3niusYukki/xianyu-openclaw/discussions).
