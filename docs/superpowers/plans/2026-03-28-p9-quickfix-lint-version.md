# P9: Quickfix — Lint Cleanup & Version Alignment

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zero lint errors across `src/` and `services/`, CI covering both directories, version strings aligned to 10.1.0.

**Architecture:** 42 lint errors exist — 33 auto-fixable, 9 need manual attention (6 B008 FastAPI false-positives, 1 B017 blind exception, 1 B905 zip strict, 1 E402 import order). CI only lints `src/` but should lint `services/` too. Version mismatch: CHANGELOG=10.1.0 but code=10.0.0.

**Tech Stack:** ruff 0.15.x, Python 3.12, FastAPI (gateway-service)

---

### Task 1: Auto-fix 33 Lint Errors

**Files:**
- Modify: `services/common/xianyuflow_common/cache.py` (UP045 ×6, UP035 ×1)
- Modify: `services/common/xianyuflow_common/config.py` (UP045 ×2)
- Modify: `services/common/xianyuflow_common/database.py` (UP035 ×1)
- Modify: `services/common/xianyuflow_common/dual_write.py` (UP045 ×3)
- Modify: `services/common/xianyuflow_common/kafka.py` (UP035 ×1)
- Modify: `services/common/xianyuflow_common/metrics.py` (UP035 ×1, I001 ×1)
- Modify: `services/common/xianyuflow_common/models/base.py` (UP017 ×3)
- Modify: `services/common/xianyuflow_common/__init__.py` (I001 ×1)
- Modify: `services/common/tests/test_dual_write.py` (F401 ×2, I001 ×1)
- Modify: `services/conftest.py` (F401 ×1)
- Modify: `services/gateway-service/app/routes/orders.py` (F401 ×2)
- Modify: `services/gateway-service/app/routes/products.py` (F401 ×2)
- Modify: `services/gateway-service/tests/test_main.py` (I001 ×1)
- Modify: `services/gateway-service/tests/test_signing.py` (I001 ×1, F401 ×1)

- [ ] **Step 1: Run ruff auto-fix**

Run: `ruff check src/ services/ --fix`
Expected: "Fixed 33 errors" or similar. 33 auto-fixable issues resolved.

- [ ] **Step 2: Verify remaining errors**

Run: `ruff check src/ services/ --statistics`
Expected: 9 remaining errors (6×B008, 1×B017, 1×B905, 1×E402)

- [ ] **Step 3: Run tests to verify nothing broke**

Run: `./venv/bin/python -m pytest tests/ -q --tb=short && cd services/common && ../../../venv/bin/python -m pytest tests/ -q --tb=short && cd ../../gateway-service && ../../../venv/bin/python -m pytest tests/ -q --tb=short`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "fix(lint): auto-fix 33 lint issues (UP045, F401, I001, UP035, UP017)"
```

---

### Task 2: Fix Ruff Config Deprecation in services/common

**Files:**
- Modify: `services/common/pyproject.toml`

The top-level `[tool.ruff]` keys `select` and `ignore` are deprecated in ruff 0.15.x. Must move to `[tool.ruff.lint]`.

- [ ] **Step 1: Update pyproject.toml ruff config**

Current config in `services/common/pyproject.toml` (lines after `[tool.ruff]`):

```toml
[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501"]
```

Change to:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501"]
```

- [ ] **Step 2: Verify no deprecation warning**

Run: `ruff check services/common/ 2>&1 | head -5`
Expected: No deprecation warning about top-level linter settings

- [ ] **Step 3: Commit**

```bash
git add services/common/pyproject.toml
git commit -m "fix(lint): move ruff config to lint section in services/common"
```

---

### Task 3: Add Ruff Config for Gateway Service (B008 Ignore)

**Files:**
- Modify: `services/gateway-service/pyproject.toml`

6 B008 errors in gateway-service are all FastAPI `Depends()` in default arguments — this is the canonical FastAPI dependency injection pattern and a false positive. Add per-project ruff config to ignore B008.

- [ ] **Step 1: Add ruff config to gateway-service pyproject.toml**

Append to `services/gateway-service/pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["B008", "E501"]
```

- [ ] **Step 2: Verify B008 suppressed**

Run: `ruff check services/gateway-service/ --statistics`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add services/gateway-service/pyproject.toml
git commit -m "fix(lint): add ruff config for gateway-service, ignore B008 (FastAPI DI)"
```

---

### Task 4: Manual Lint Fixes (B017, B905, E402)

**Files:**
- Modify: `services/common/tests/test_database.py:114` (B017)
- Modify: `services/common/xianyuflow_common/dual_write.py:238` (B905)
- Modify: `services/common/xianyuflow_common/metrics.py:326` (E402)

- [ ] **Step 1: Fix B017 in test_database.py**

Line 114 has `pytest.raises(Exception)` which is a blind exception assertion. The test raises `ValueError("test error")` on line 117. Change to catch `ValueError` instead:

```python
        with pytest.raises(ValueError, match="test error"):
            async with db.session() as session:
                assert session is not None
                raise ValueError("test error")
```

- [ ] **Step 2: Fix B905 in dual_write.py**

Line ~238 has `zip(sqlite_data, pg_data)`. Add `strict=True`:

```python
        for i, (sqlite_row, pg_row) in enumerate(zip(sqlite_data, pg_data, strict=True)):
```

- [ ] **Step 3: Fix E402 in metrics.py**

Line 326 has `import asyncio` after function definitions. Move it to the top of the file, into the existing import block (after `from contextlib import contextmanager`):

Add after line 5:
```python
import asyncio
```

And remove line 326 (`import asyncio`) and the comment above it (`# Import asyncio for decorator checks`).

- [ ] **Step 4: Verify zero lint errors**

Run: `ruff check src/ services/ --statistics`
Expected: 0 errors

- [ ] **Step 5: Run tests**

Run: `./venv/bin/python -m pytest tests/ -q && cd services/common && ../../../venv/bin/python -m pytest tests/ -q && cd ../../gateway-service && ../../../venv/bin/python -m pytest tests/ -q`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add services/common/tests/test_database.py services/common/xianyuflow_common/dual_write.py services/common/xianyuflow_common/metrics.py
git commit -m "fix(lint): resolve B017, B905, E402 manual lint errors"
```

---

### Task 5: Update CI to Lint services/

**Files:**
- Modify: `.github/workflows/ci.yml:39`

CI currently only lints `src/`. Must also lint `services/`.

- [ ] **Step 1: Update CI ruff check command**

In `.github/workflows/ci.yml`, change the ruff check step (line 39) from:

```yaml
        run: ruff check src/ --extend-ignore I001,E501,UP012,RUF100
```

to:

```yaml
        run: ruff check src/ services/ --extend-ignore I001,E501,UP012,RUF100
```

- [ ] **Step 2: Verify CI config is valid**

Run: `grep -n 'ruff check' .github/workflows/ci.yml`
Expected: Shows `ruff check src/ services/ --extend-ignore I001,E501,UP012,RUF100`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "fix(ci): lint services/ directory in CI alongside src/"
```

---

### Task 6: Version Alignment (10.0.0 → 10.1.0)

**Files:**
- Modify: `src/__init__.py:5`
- Modify: `pyproject.toml`
- Modify: `client/package.json`

CHANGELOG already has `[10.1.0] - 2026-03-28` entry. Bump code to match.

- [ ] **Step 1: Update src/__init__.py**

Change `__version__ = "10.0.0"` to `__version__ = "10.1.0"`

- [ ] **Step 2: Update pyproject.toml**

Change `version = "10.0.0"` to `version = "10.1.0"`

- [ ] **Step 3: Update client/package.json**

Change `"version": "10.0.0"` to `"version": "10.1.0"`

- [ ] **Step 4: Verify all 3 match**

Run: `grep -n 'version.*10\.1\.0' src/__init__.py pyproject.toml client/package.json`
Expected: 3 matches

- [ ] **Step 5: Commit**

```bash
git add src/__init__.py pyproject.toml client/package.json
git commit -m "chore: bump version to 10.1.0"
```

---

### Task 7: Final Validation

- [ ] **Step 1: Run full lint check**

Run: `ruff check src/ services/ && ruff format --check src/ services/`
Expected: 0 errors

- [ ] **Step 2: Run all tests**

Run: `./venv/bin/python -m pytest tests/ -q`
Expected: All pass

- [ ] **Step 3: Run services tests**

Run: `cd services/common && ../../../venv/bin/python -m pytest tests/ -q && cd ../../gateway-service && ../../../venv/bin/python -m pytest tests/ -q`
Expected: All pass

- [ ] **Step 4: Frontend build**

Run: `cd client && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Frontend tests**

Run: `cd client && npx vitest run`
Expected: All pass
