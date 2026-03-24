# Agent Documentation Index

> 专为 AI Agent (Claude, GitHub Copilot, Gemini 等) 设计的项目文档

**项目**: XianyuFlow | 闲流 (XianyuFlow | 闲流)  
**仓库**: https://github.com/G3niusYukki/realxianyu  
**技术栈**: Python 3.12+ (asyncio) + React/Vite + SQLite

---

## Quick Navigation

| 文档 | 用途 | 阅读顺序 |
|------|------|----------|
| [Quick Start](#quick-start) | 5分钟上手 | 1 |
| [Architecture](ARCHITECTURE.md) | 架构设计 | 2 |
| [Repository Reference](CLAUDE.md) | 详细代码约定 | 3 |
| [API Reference](../API.md) | HTTP API 文档 | 4 |

---

## Quick Start

### Prerequisites

- **Python**: 3.12 or higher
- **Node.js**: v18 or higher (for building frontend)
- **npm**: or yarn / pnpm

### 1. Build Frontend

```bash
cd client
npm install
npm run build
cd ..
```

*Note: If `client/dist` does not exist, the backend will return 404 when accessing dashboard.*

### 2. Setup Backend

```bash
# Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install Playwright for slider auto-solve
playwright install chromium
```

### 3. Configuration

```bash
cp .env.example .env
```

**Key variables:**
- `PORT`: Dashboard port (default: 8080)
- `XIANYU_COOKIE_1`: Essential for Xianyu connection
- `DEEPSEEK_API_KEY`: For message auto-reply
- `COOKIE_CLOUD_*`: For automatic cookie syncing

### 4. Start Service

```bash
python -m src.main
```

Dashboard: `http://localhost:<PORT>` (default 8080)

---

## Project Structure

```
src/
├── core/               # Infrastructure (config, logging, browser client)
├── services/           # Business services (CookieService, XGJService)
├── modules/            # Business modules
│   ├── messages/       # WebSocket, message reply, workflow
│   ├── orders/         # Order fulfillment, auto pricing
│   ├── quote/          # Quote engine
│   ├── listing/        # Product listing
│   └── virtual_goods/  # Virtual goods verification
├── integrations/       # XianGuanjia API integration
├── dashboard/          # Dashboard routes, facade (mimic_ops.py)
├── cli/                # Modular CLI package
├── dashboard_server.py # HTTP server entry
└── main.py             # Python program entry

client/                 # React/Vite frontend
config/                 # YAML configuration
```

---

## Key Constraints

### 1. No Business Logic in `mimic_ops.py`

The `src/dashboard/mimic_ops.py` file is a Facade proxy only. **Do not add new business logic there.**

Add logic to appropriate `modules/` or `services/` instead.

### 2. No `global` Declarations

Use singleton classes instead:

```python
# ❌ Don't do this
global some_state

# ✅ Do this
class WebSocketTransportManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

Existing singletons:
- `WebSocketTransportManager` - WS connection management
- `MessageServiceRegistry` - Active service registry
- `GeoKnownCache` - Province/city resolution cache
- `QuoteLedger` - Quote persistence
- `AutoPricePoller` - Auto pricing poller

### 3. YAML is Single Source of Truth

- **YAML** (`config/config.yaml`): Main config with defaults
- **JSON** (`data/system_config.json`): Dashboard UI overrides
- **Environment** (`.env`): Highest priority at runtime

New config items go to `config/config.yaml`, not new sources.

### 4. Preserve Import Patterns

CLI files use dynamic imports for test monkeypatching:

```python
def some_function():
    from src.cli import _json_out  # noqa: F401
    # Use _json_out here
```

### 5. Tests Must Pass

```bash
./venv/bin/python -m pytest tests/ -q
```

All PRs must pass tests.

---

## Common Tasks

### Adding a New Module

1. Create `src/modules/mymodule/` directory
2. Add `service.py` with main service class
3. Add tests in `tests/test_mymodule_*.py`
4. Register in `src/modules/__init__.py` if needed
5. Add routes in `src/dashboard/routes/` if API needed

### Adding a Config Option

1. Add to `config/config.yaml` with default value
2. Add to `src/core/config_models.py` if using Pydantic models
3. Access via `get_config()`:

```python
from src.core.config import get_config
config = get_config()
value = config.my_option
```

### Running Tests

```bash
# All tests (~1172)
./venv/bin/python -m pytest tests/ -q

# Specific module
./venv/bin/python -m pytest tests/test_messages_cov100.py -v

# With coverage
pytest tests/ -v --cov=src
```

### Code Style

```bash
# Check
ruff check src/ --extend-ignore I001,E501,UP012,RUF100

# Format
ruff format src/
```

---

## Architecture Notes

### Configuration System

```
config.yaml defaults < system_config.json < .env overrides
```

Dashboard edits auto-merge via `Config._merge_system_config()`.

### Message Flow

```
User sends message
    ↓
WS notification (ws_live.py)
    ↓
MessagesService.receive_message()
    ↓
ReplyEngine generates reply (with AI quote)
    ↓
QuoteEngine calculates logistics price
    ↓
WS sends reply
```

### Cookie Management

4-level fallback:
1. XianGuanjia IM direct read
2. CookieCloud sync
3. Local direct read
4. Playwright hard decode

---

## Troubleshooting

### Port Already in Use

```bash
# macOS/Linux
lsof -ti:8091 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

### Cookie Expired

Update via Dashboard (`/accounts` page) or `.env` file.

### Tests Failing

```bash
# Check specific test
pytest tests/test_failing.py -v --tb=short

# Clear pytest cache
rm -rf .pytest_cache
```

---

## External Resources

- [Repository](https://github.com/G3niusYukki/realxianyu)
- [Issues](https://github.com/G3niusYukki/realxianyu/issues)
- [Discussions](https://github.com/G3niusYukki/realxianyu/discussions)

---

**Last Updated**: 2026-03-24  
**Maintained by**: Project maintainers
