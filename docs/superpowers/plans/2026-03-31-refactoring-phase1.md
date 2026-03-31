# XianyuFlow Refactoring Phase 1 — Core Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce `mimic_ops.py` from 1208→<800 lines, remove `__getattr__` delegation, simplify `dashboard_server.py` to <700 lines, and split `quote_service.py` to <600 lines.

**Architecture:** Extract shared utilities first to break circular imports, then extract domain-specific services from `mimic_ops.py`, replace magic delegation with explicit forwarding, and refactor the server into handler modules. Each task is self-contained and testable.

**Tech Stack:** Python 3.12+, pytest, ruff

---

## File Structure (Target)

```
src/dashboard/
├── helpers/
│   ├── __init__.py                    # NEW
│   └── utils.py                       # NEW — shared utilities (_now_iso, _error_payload, _run_async, etc.)
├── services/
│   ├── __init__.py                    # MODIFY — update re-exports
│   ├── cookie_service.py              # MODIFY — fix import
│   ├── cookie_service.py              # MODIFY — import from helpers
│   ├── env_service.py                 # NEW — env read/write operations
│   ├── virtual_goods_service.py       # NEW — VG dashboard panel builder
│   ├── status_service.py              # NEW — service_status aggregation
│   ├── quote_service.py               # MODIFY — split + fix import
│   ├── xgj_service.py                 # MODIFY — fix import
│   ├── log_service.py                 # MODIFY — fix import
│   ├── reply_test_service.py          # MODIFY — fix import
│   └── template_service.py            # MODIFY — fix import
├── server/
│   ├── __init__.py                    # NEW
│   ├── handlers.py                    # NEW — CookieCloud, listing, dashboard data
│   └── middleware.py                  # NEW — CORS, auth
├── mimic_ops.py                       # MODIFY — slim facade only
├── dashboard_server.py                # MODIFY — slim server entry
└── routes/                            # EXISTING — minor import fixes
```

---

## Task 1: Create shared utilities module (`helpers/utils.py`)

**Why:** 5 files import `_now_iso`, `_error_payload`, `_run_async`, `_safe_int` from `mimic_ops.py`, creating circular dependencies (mimic_ops imports services, services import back from mimic_ops). Extract these to a shared module.

**Files:**
- Create: `src/dashboard/helpers/__init__.py`
- Create: `src/dashboard/helpers/utils.py`
- Modify: `src/dashboard/services/quote_service.py:26-29` (fix import)
- Modify: `src/dashboard/services/template_service.py:28` (fix import)
- Modify: `src/dashboard/services/log_service.py:408` (fix import)
- Modify: `src/dashboard/services/reply_test_service.py:37` (fix import)
- Modify: `src/dashboard/services/xgj_service.py:190,236,269` (fix imports)
- Modify: `src/dashboard/services/cookie_service.py:691` (fix import)
- Modify: `src/dashboard/routes/orders.py:243` (fix import)
- Modify: `src/dashboard/routes/system.py:186` (fix import)
- Modify: `src/dashboard/routes/products.py:15` (fix import)
- Modify: `src/dashboard_server.py:23` (fix import)
- Modify: `src/dashboard/mimic_ops.py` (re-export for backward compat, update internal use)
- Modify: `tests/test_system_xgj_health_priority.py:32,74` (fix monkeypatch path)
- Test: `pytest tests/ -q`

- [ ] **Step 1: Create `src/dashboard/helpers/__init__.py`**

```python
from src.dashboard.helpers.utils import (
    _error_payload,
    _extract_json_payload,
    _now_iso,
    _run_async,
    _safe_int,
    _test_xgj_connection,
)

__all__ = [
    "_error_payload",
    "_extract_json_payload",
    "_now_iso",
    "_run_async",
    "_safe_int",
    "_test_xgj_connection",
]
```

- [ ] **Step 2: Create `src/dashboard/helpers/utils.py`**

Extract these functions from `src/dashboard/mimic_ops.py` lines 35-137:
- `_safe_int` (line 35)
- `_error_payload` (line 49)
- `_extract_json_payload` (line 61)
- `_test_xgj_connection` (line 83)
- `_run_async` (line 127)
- `_now_iso` (line 137)

Also move the module-level cache variables:
- `_product_image_cache` (line 31)
- `_PRODUCT_IMAGE_CACHE_TTL` (line 32)

And the default templates:
- `DEFAULT_WEIGHT_TEMPLATE` (line 110)
- `DEFAULT_VOLUME_TEMPLATE` (line 117)

Copy them verbatim to the new file. Keep the same imports (add `asyncio` for `_run_async`, `datetime` for `_now_iso`).

- [ ] **Step 3: Update `mimic_ops.py` — re-export for backward compat**

In `mimic_ops.py`, replace the original function definitions (lines 31-137) with imports from helpers:

```python
from src.dashboard.helpers.utils import (
    DEFAULT_VOLUME_TEMPLATE,
    DEFAULT_WEIGHT_TEMPLATE,
    _PRODUCT_IMAGE_CACHE_TTL,
    _error_payload,
    _extract_json_payload,
    _now_iso,
    _product_image_cache,
    _run_async,
    _safe_int,
    _test_xgj_connection,
)
```

This preserves backward compatibility — any code importing from `mimic_ops` still works.

- [ ] **Step 4: Update all services to import from helpers**

For each service file, change lazy imports like:
```python
from src.dashboard.mimic_ops import _now_iso
```
to:
```python
from src.dashboard.helpers.utils import _now_iso
```

Files to update:
- `src/dashboard/services/quote_service.py:26-29` — replace the lazy `_now_iso` wrapper with direct import
- `src/dashboard/services/template_service.py:28` — fix import
- `src/dashboard/services/log_service.py:408` — fix import
- `src/dashboard/services/reply_test_service.py:37` — fix import
- `src/dashboard/services/xgj_service.py:190,236,269` — fix all 3 lazy imports
- `src/dashboard/services/cookie_service.py:691` — fix import

- [ ] **Step 5: Update route files**

- `src/dashboard/routes/orders.py:243` — change `from src.dashboard.mimic_ops import _test_xgj_connection` → `from src.dashboard.helpers.utils import _test_xgj_connection`
- `src/dashboard/routes/system.py:186` — same
- `src/dashboard/routes/products.py:15` — change `from src.dashboard.mimic_ops import _run_async as _ra` → `from src.dashboard.helpers.utils import _run_async as _ra`

- [ ] **Step 6: Update `dashboard_server.py`**

Line 23: change:
```python
from src.dashboard.mimic_ops import MimicOps, _error_payload, _safe_int
```
to:
```python
from src.dashboard.mimic_ops import MimicOps
from src.dashboard.helpers.utils import _error_payload, _safe_int
```

- [ ] **Step 7: Update test monkeypatch paths**

`tests/test_system_xgj_health_priority.py` lines 32 and 74:
Change `src.dashboard.mimic_ops._test_xgj_connection` → `src.dashboard.helpers.utils._test_xgj_connection`

- [ ] **Step 8: Run tests**

```bash
pytest tests/ -q
```
Expected: All tests pass (same as before, just import paths changed).

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor: extract shared utilities to src/dashboard/helpers/utils.py

Breaks circular imports by moving _now_iso, _error_payload, _run_async,
_safe_int, _test_xgj_connection to a shared helpers module.
mimic_ops.py re-exports for backward compatibility."
```

---

## Task 2: Extract `EnvService` from `mimic_ops.py`

**Why:** Env read/write logic (~40 lines) is self-contained and reusable.

**Files:**
- Create: `src/dashboard/services/env_service.py`
- Modify: `src/dashboard/mimic_ops.py` — remove env methods, use `EnvService`
- Modify: `src/dashboard/services/__init__.py` — add `EnvService` export
- Test: `pytest tests/ -q`

- [ ] **Step 1: Create `src/dashboard/services/env_service.py`**

Extract from `mimic_ops.py` lines 346-396:
- `env_path` property (line 347)
- `logs_dir` property (line 351)
- `cookie_plugin_dir` property (line 355)
- `_read_env_lines` (line 358)
- `_get_env_value` (line 363)
- `_set_env_value` (line 370)
- `_to_bool` static method (line 386)
- `_get_env_bool` (line 394)

```python
class EnvService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    @property
    def env_path(self) -> Path: ...
    @property
    def logs_dir(self) -> Path: ...
    @property
    def cookie_plugin_dir(self) -> Path: ...
    def _read_env_lines(self) -> list[str]: ...
    def _get_env_value(self, key: str) -> str: ...
    def _set_env_value(self, key: str, value: str) -> None: ...
    @staticmethod
    def _to_bool(value: Any, default: bool = False) -> bool: ...
    def _get_env_bool(self, key: str, default: bool = False) -> bool: ...
```

- [ ] **Step 2: Update `MimicOps.__init__` to create `EnvService`**

Add `self._env_service = EnvService(self.project_root)` in `__init__`.
Delegate `env_path`, `logs_dir`, `cookie_plugin_dir` via properties:
```python
@property
def env_path(self) -> Path:
    return self._env_service.env_path
```

Replace all internal calls like `self._get_env_value(...)` → `self._env_service._get_env_value(...)`.

- [ ] **Step 3: Update `__init__.py`**

Add `EnvService` to the imports and `__all__`.

- [ ] **Step 4: Run tests**

```bash
pytest tests/ -q
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: extract EnvService from mimic_ops.py"
```

---

## Task 3: Extract `VirtualGoodsDashboardService` from `mimic_ops.py`

**Why:** The VG dashboard panel building logic (lines 398-840, ~440 lines) is the largest chunk in `mimic_ops.py`. It's self-contained VG display logic.

**Files:**
- Create: `src/dashboard/services/vg_dashboard_service.py`
- Modify: `src/dashboard/mimic_ops.py` — remove VG methods, delegate to service
- Modify: `src/dashboard/services/__init__.py`
- Test: `pytest tests/ -q`

- [ ] **Step 1: Create `src/dashboard/services/vg_dashboard_service.py`**

Extract from `mimic_ops.py`:
- `_virtual_goods_service` (line 398) — factory for `VirtualGoodsService`
- `_vg_service_metrics` static (line 404)
- `_vg_int` static (line 415)
- `_build_virtual_goods_dashboard_panels` (line 421-840, ~420 lines)
- `get_virtual_goods_metrics` (line 608-673)
- `get_dashboard_readonly_aggregate` (line 674-695)
- `inspect_virtual_goods_order` (line 696-841)

The new class:
```python
class VirtualGoodsDashboardService:
    def __init__(self, project_root: Path, xgj_config_provider: Callable[[], dict]) -> None:
        self.project_root = project_root
        self._xgj_config_provider = xgj_config_provider
        # move _cost_table_repo, _shared_cookie_checker here if needed
```

Note: `get_virtual_goods_metrics` at line 608 calls `self._xianguanjia_service_config()` which is on `XGJService`. Pass the config as a parameter or use a callable provider.

- [ ] **Step 2: Update `MimicOps` to delegate**

In `mimic_ops.py`, replace VG methods with delegation:
```python
def get_virtual_goods_metrics(self, ...):
    return self._vg_dashboard_service.get_virtual_goods_metrics(...)

def get_dashboard_readonly_aggregate(self):
    return self._vg_dashboard_service.get_dashboard_readonly_aggregate()

def inspect_virtual_goods_order(self, order_id: str):
    return self._vg_dashboard_service.inspect_virtual_goods_order(order_id)
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/ -q
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: extract VirtualGoodsDashboardService from mimic_ops.py (~440 lines)"
```

---

## Task 4: Extract `StatusService` from `mimic_ops.py`

**Why:** `service_status()` (lines 933-1096, ~164 lines) is a complex aggregation method. Combined with `service_control`, `service_recover`, `service_auto_fix` (~110 lines), that's ~274 lines of status/control logic.

**Files:**
- Create: `src/dashboard/services/status_service.py`
- Modify: `src/dashboard/mimic_ops.py`
- Modify: `src/dashboard/services/__init__.py`
- Test: `pytest tests/ -q`

- [ ] **Step 1: Create `src/dashboard/services/status_service.py`**

Extract from `mimic_ops.py`:
- `service_status` (line 933-1096) — needs dependencies: module_console, cookie_service, quote_service, log_service, xgj_service, env_service
- `service_control` (line 1098-1142)
- `service_recover` (line 1144-1162)
- `service_auto_fix` (line 1164-1205)

Also needs to manage `_service_state`, `_service_started_at`, `_instance_id`, `_python_exec`, `_recover_lock`, `_last_cookie_fp`, `_last_auto_recover_*` state.

```python
class StatusService:
    def __init__(
        self,
        project_root: Path,
        module_console: ModuleConsole,
        cookie_service: CookieService,
        quote_service: QuoteService,
        log_service: LogService,
        xgj_service: XGJService,
        env_service: EnvService,
    ) -> None: ...
```

**BUG FIX:** `_maybe_auto_recover_presales` is called at line 1011 but never defined. Add a proper implementation:
```python
def _maybe_auto_recover_presales(
    self, *, service_status: str, token_error: str | None,
    cookie_text: str, presales_alive: bool,
) -> dict[str, Any]:
    """Auto-recover presales if conditions warrant it."""
    if service_status in ("running",) and not token_error and presales_alive:
        return {"stage": "monitoring"}
    if not cookie_text:
        return {"stage": "no_cookie"}
    if token_error == "FAIL_SYS_USER_VALIDATE":
        return {"stage": "cookie_expired", "last_auto_recover_at": self._last_auto_recover_at}
    # ... actual recovery logic
    return {"stage": "monitoring"}
```

Investigate the original intent: it should check if presales module is down and auto-recover. Check git history for the original implementation.

- [ ] **Step 2: Update `MimicOps` to delegate**

```python
def service_status(self) -> dict[str, Any]:
    return self._status_service.service_status()

def service_control(self, action: str) -> dict[str, Any]:
    return self._status_service.service_control(action)

def service_recover(self, target: str = "presales") -> dict[str, Any]:
    return self._status_service.service_recover(target)

def service_auto_fix(self) -> dict[str, Any]:
    return self._status_service.service_auto_fix()
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/ -q
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: extract StatusService from mimic_ops.py (~274 lines)

Also fixes missing _maybe_auto_recover_presales method (was called but never defined)."
```

---

## Task 5: Remove `__getattr__` delegation from `MimicOps`

**Why:** Magic `__getattr__` delegation hides method origins, makes debugging hard, and breaks IDE autocompletion. Replace with explicit forwarding methods.

**Files:**
- Modify: `src/dashboard/mimic_ops.py` — remove `__getattr__` and all `_DELEGATE_METHODS` frozensets
- Modify: `src/dashboard/routes/*.py` — update callers to use `mimic_ops.service.method()` where appropriate
- Modify: `src/dashboard_server.py` — update callers
- Test: `pytest tests/ -q`

- [ ] **Step 1: Add explicit forwarding methods to `MimicOps`**

For each method in the delegate frozensets that is actually called externally (from routes/server), add an explicit method. Based on the grep results, the actually-used delegated methods are:

**From cookie_service (used in routes/cookie.py):**
```python
def get_cookie(self) -> dict[str, Any]:
    return {"success": bool(self._env_service._get_env_value("XIANYU_COOKIE_1").strip()), ...}

def update_cookie(self, cookie: str, *, auto_recover: bool = False) -> dict[str, Any]:
    # Keep in MimicOps — it touches multiple services

def parse_cookie_text(self, text: str) -> dict[str, Any]:
    return self._cookie_service.parse_cookie_text(text)

def diagnose_cookie(self, cookie_text: str) -> dict[str, Any]:
    return self._cookie_service.diagnose_cookie(cookie_text)

def export_cookie_plugin_bundle(self) -> tuple[bytes, str]:
    return self._cookie_service.export_cookie_plugin_bundle()

def import_cookie_plugin_files(self, files, *, auto_recover=False):
    return self._cookie_service.import_cookie_plugin_files(...)

# Internal helpers used in service_status:
def _cookie_fingerprint(self, text): return self._cookie_service._cookie_fingerprint(text)
def _extract_cookie_pairs_from_header(self, text): return self._cookie_service._extract_cookie_pairs_from_header(text)
def _cookie_domain_filter_stats(self, text): return self._cookie_service._cookie_domain_filter_stats(text)
def _is_cookie_cloud_configured(self): return self._cookie_service._is_cookie_cloud_configured()
```

**From xgj_service (used in routes/orders.py, system.py):**
```python
def get_xianguanjia_settings(self): return self._xgj_service.get_xianguanjia_settings()
def save_xianguanjia_settings(self, data): return self._xgj_service.save_xianguanjia_settings(data)
def retry_xianguanjia_price(self, data): return self._xgj_service.retry_xianguanjia_price(data)
def retry_xianguanjia_delivery(self, data): return self._xgj_service.retry_xianguanjia_delivery(data)
def handle_order_callback(self, data): return self._xgj_service.handle_order_callback(data)
def handle_order_push(self, data): return self._xgj_service.handle_order_push(data)
def handle_product_callback(self, data): return self._xgj_service.handle_product_callback(data)
def _xianguanjia_service_config(self): return self._xgj_service._xianguanjia_service_config()
def _resolve_session_id_for_order(self, order_id): return self._xgj_service._resolve_session_id_for_order(order_id)
```

**From quote_service (used in routes/quote.py):**
```python
def route_stats(self): return self._quote_service.route_stats()
def export_routes_zip(self): return self._quote_service.export_routes_zip()
def get_template(self, default=False): return self._quote_service.get_template(default=default)
def get_markup_rules(self): return self._quote_service.get_markup_rules()
def import_route_files(self, files): return self._quote_service.import_route_files(files)
def import_markup_files(self, files): return self._quote_service.import_markup_files(files)
def save_template(self, name, content): return self._quote_service.save_template(name, content)
def save_markup_rules(self, rules): return self._quote_service.save_markup_rules(rules)
def get_pricing_config(self): return self._quote_service.get_pricing_config()
def save_pricing_config(self, cfg): return self._quote_service.save_pricing_config(cfg)
def get_cost_summary(self): return self._quote_service.get_cost_summary()
def query_route_cost(self, origin, dest): return self._quote_service.query_route_cost(origin, dest)
```

**From log_service (used in routes/dashboard_data.py):**
```python
def list_log_files(self): return self._log_service.list_log_files()
def read_log_content(self, **kw): return self._log_service.read_log_content(**kw)
def get_unmatched_message_stats(self, **kw): return self._log_service.get_unmatched_message_stats(**kw)
def _route_stats_nonblocking(self): return self._quote_service._route_stats_nonblocking()
def _risk_control_status_from_logs(self, **kw): return self._log_service._risk_control_status_from_logs(**kw)
def _query_message_stats_from_workflow(self): return self._log_service._query_message_stats_from_workflow()
```

**From reply_test_service (used in routes/messages.py):**
```python
def get_replies(self): return self._template_service.get_replies()  # or quote_service
def test_reply(self, body): return self._reply_test_service.test_reply(body)
```

**From template_service:**
```python
def get_reply_templates(self): return self._template_service.get_reply_templates()
```

- [ ] **Step 2: Delete `__getattr__` and all `_DELEGATE_METHODS` frozensets**

Remove lines 249-344 (the frozensets and `__getattr__`).

- [ ] **Step 3: Run tests**

```bash
pytest tests/ -q
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: remove __getattr__ delegation from MimicOps

Replace magic attribute delegation with explicit forwarding methods.
All routes continue to call mimic_ops.method() — no external API changes."
```

---

## Task 6: Extract `VirtualGoodsService` factory + `update_cookie` + `reset_database` into proper locations

**Why:** After Tasks 2-5, `mimic_ops.py` should have:
- `__init__` (~30 lines)
- Properties + env wrappers (~20 lines)
- `get_cookie` (~7 lines)
- `_trigger_presales_recover_after_cookie_update` (~20 lines)
- `update_cookie` (~36 lines)
- `import_cookie_plugin_files` (~7 lines)
- `reset_database` (~20 lines)
- Explicit forwarding methods (~80 lines)

Total: ~220 lines — well under 500. But `update_cookie` can move to cookie_service and `reset_database` can be a thin wrapper.

**Files:**
- Modify: `src/dashboard/services/cookie_service.py` — add `update_cookie` method
- Modify: `src/dashboard/mimic_ops.py` — slim down remaining methods
- Test: `pytest tests/ -q`

- [ ] **Step 1: Move `update_cookie` logic to `CookieService`**

`update_cookie` (lines 869-904) calls `parse_cookie_text`, `diagnose_cookie`, `_set_env_value`, and optionally triggers presales recovery. Move to `CookieService` with explicit dependencies:
```python
class CookieService:
    def update_cookie(self, cookie: str, *, auto_recover: bool = False,
                      env_service: EnvService, module_console: ModuleConsole) -> dict[str, Any]:
```

Keep a thin forwarding method in `MimicOps`.

- [ ] **Step 2: Run tests**

```bash
pytest tests/ -q
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: move update_cookie logic to CookieService"
```

---

## Task 7: Extract handlers from `dashboard_server.py`

**Why:** `dashboard_server.py` at 1080 lines has inline CookieCloud handling, listing publish, dashboard data assembly, and SPA serving that can be extracted.

**Files:**
- Create: `src/dashboard/server/__init__.py`
- Create: `src/dashboard/server/cookie_cloud.py` — CookieCloud handling (~100 lines)
- Create: `src/dashboard/server/listing_handler.py` — listing preview/publish (~70 lines)
- Create: `src/dashboard/server/dashboard_data.py` — dashboard aggregation (~100 lines)
- Create: `src/dashboard/server/middleware.py` — CORS + auth helpers (~80 lines)
- Modify: `src/dashboard_server.py` — import from server modules
- Test: `pytest tests/ -q`

- [ ] **Step 1: Create `src/dashboard/server/middleware.py`**

Extract from `dashboard_server.py`:
- `_normalize_origin` (line 36)
- `_iter_dashboard_allowed_origins` (line 53)
- `_is_allowed_dashboard_origin` (line 63)
- `_headers_to_dict` (line 74)
- `_extract_dashboard_token` (line 90)
- `_check_api_request_access` (line 101)
- `DashboardHandler._send_cors_headers` (line 131)
- `DashboardHandler._ensure_api_request_access` (line 141)
- `DashboardHandler._send_json` (line 164)
- `DashboardHandler._send_html` (line 173)
- `DashboardHandler._send_bytes` (line 181)
- `DashboardHandler.do_OPTIONS` (line 154)
- `DashboardHandler.log_message` (line 867)

- [ ] **Step 2: Create `src/dashboard/server/cookie_cloud.py`**

Extract from `dashboard_server.py`:
- `_handle_cookie_cloud` (line 591-645, 55 lines)
- `_read_cc_credentials` (line 646-653)
- `_try_instant_cookie_apply` (line 654-696, 43 lines)

Total: ~100 lines

- [ ] **Step 3: Create `src/dashboard/server/listing_handler.py`**

Extract:
- `_enrich_product_images` (line 190-291, 94 lines — actually this is in the handler)
- `_build_publish_config` (line 292-295)
- `_handle_listing_preview` (line 296-311)
- `_handle_listing_publish` (line 312-351)

Total: ~70 lines

- [ ] **Step 4: Create `src/dashboard/server/dashboard_data.py`**

Extract:
- `_enrich_summary_with_message_and_order_stats` (line 472-499)
- `_legacy_dashboard_payload` (line 500-560)
- `_aggregate_dashboard_payload` (line 561-590)
- `_get_live_dashboard` (line 469-471)

Total: ~120 lines

- [ ] **Step 5: Update `dashboard_server.py`**

Import from new modules. The main file should only contain:
- `DashboardHandler` class with slim routing methods (do_GET, do_POST, do_PUT, do_DELETE)
- `run_server()` function
- `parse_args()` and `main()`

Target: <400 lines.

- [ ] **Step 6: Run tests**

```bash
pytest tests/ -q
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: extract handler modules from dashboard_server.py

Split into server/cookie_cloud.py, server/listing_handler.py,
server/dashboard_data.py, server/middleware.py. Server entry drops to <400 lines."
```

---

## Task 8: Split `quote_service.py` into focused handlers

**Why:** At 952 lines, `quote_service.py` handles route tables, markup rules, pricing config, cost tables, and templates. Each domain can be its own handler.

**Files:**
- Create: `src/dashboard/services/quote/
│   ├── __init__.py`
│   ├── service.py` — thin facade <400 lines
│   ├── route_table_handler.py` — route stats, import, export ~200 lines
│   ├── markup_handler.py` — markup rules, import, field aliases ~200 lines
│   ├── cost_table_handler.py` — cost summary, query, pricing config ~150 lines
│   `template_handler.py` — template CRUD ~100 lines
- Modify: `src/dashboard/services/quote_service.py` → keep as thin re-export shim for backward compat
- Modify: `src/dashboard/services/__init__.py`
- Test: `pytest tests/ -q`

- [ ] **Step 1: Create `src/dashboard/services/quote/` package structure**

```python
# src/dashboard/services/quote/__init__.py
from src.dashboard.services.quote.service import QuoteService
```

- [ ] **Step 2: Extract `RouteTableHandler`**

Move from `quote_service.py`:
- `route_stats` (line 115)
- `_route_stats_nonblocking` (similar to route_stats but non-blocking)
- `import_route_files` (~80 lines)
- `export_routes_zip` (~60 lines)
- Related constants: `_ROUTE_FILE_EXTS`

- [ ] **Step 3: Extract `MarkupHandler`**

Move:
- `get_markup_rules` (~30 lines)
- `save_markup_rules` (~30 lines)
- `import_markup_files` (~80 lines)
- All `_MARKUP_*` constants and `_MARKUP_FIELD_ALIASES`

- [ ] **Step 4: Extract `CostTableHandler`**

Move:
- `get_pricing_config` (~20 lines)
- `save_pricing_config` (~30 lines)
- `get_cost_summary` (~40 lines)
- `query_route_cost` (~30 lines)

- [ ] **Step 5: Extract `TemplateHandler`**

Move:
- `get_template` (~30 lines)
- `save_template` (~30 lines)
- `get_reply_templates` (~20 lines)
- `get_replies` (~20 lines)

- [ ] **Step 6: Create slim `QuoteService` facade**

```python
class QuoteService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._route_handler = RouteTableHandler(project_root)
        self._markup_handler = MarkupHandler(project_root)
        self._cost_handler = CostTableHandler(project_root)
        self._template_handler = TemplateHandler(project_root)
        # Forward all public methods
```

Keep `config_path`, `_quote_dir`, `reset_database` in the facade.

- [ ] **Step 7: Keep `src/dashboard/services/quote_service.py` as backward-compat shim**

```python
from src.dashboard.services.quote.service import QuoteService
```

This ensures nothing breaks.

- [ ] **Step 8: Run tests**

```bash
pytest tests/ -q
```

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor: split QuoteService into focused handler modules

route_table_handler, markup_handler, cost_table_handler, template_handler.
quote_service.py remains as backward-compat re-export shim."
```

---

## Task 9: Pin dependency versions in `requirements.txt`

**Why:** Several dependencies lack upper-bound constraints, risking breakage on major version bumps.

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add upper-bound constraints**

For each dependency, add `<next_major.0.0`:
```
DrissionPage>=4.1,<5.0.0
rookiepy>=0.5.0,<1.0.0
oss2>=2.18.0,<3.0.0
pandas>=2.1.0,<3.0.0
```

Check all other dependencies and add appropriate bounds. Keep existing lower bounds.

- [ ] **Step 2: Run tests**

```bash
pytest tests/ -q
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add upper-bound version constraints to dependencies"
```

---

## Verification

After all tasks, verify:

```bash
# Line counts
wc -l src/dashboard/mimic_ops.py src/dashboard_server.py src/dashboard/services/quote_service.py

# Expected:
# mimic_ops.py < 500
# dashboard_server.py < 500
# quote_service.py < 50 (shim)

# No __getattr__ delegation
grep -c "__getattr__" src/dashboard/mimic_ops.py  # should be 0
grep -c "_DELEGATE_METHODS" src/dashboard/mimic_ops.py  # should be 0

# All tests pass
pytest tests/ -q

# Lint clean
ruff check src/
ruff format src/ --check
```

---

## Expected Results

| File | Before | After |
|------|--------|-------|
| `mimic_ops.py` | 1208 lines | ~220 lines |
| `dashboard_server.py` | 1080 lines | ~400 lines |
| `quote_service.py` | 952 lines | ~50 lines (shim) |
| `helpers/utils.py` | 0 | ~110 lines |
| `services/env_service.py` | 0 | ~60 lines |
| `services/vg_dashboard_service.py` | 0 | ~450 lines |
| `services/status_service.py` | 0 | ~280 lines |
| `server/middleware.py` | 0 | ~100 lines |
| `server/cookie_cloud.py` | 0 | ~100 lines |
| `server/listing_handler.py` | 0 | ~100 lines |
| `server/dashboard_data.py` | 0 | ~120 lines |
| `services/quote/*.py` | 0 | ~680 lines total |

All existing routes, API endpoints, and behavior preserved. No breaking changes.
