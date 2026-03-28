# P4-P8 Improvement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up lint errors, unify versions, remove unused microservice scaffolds, add frontend tests, create Docker orchestration, and polish the project to release-ready state.

**Architecture:** Follows MICROSERVICE_ROADMAP.md Option B — keep `gateway-service` + `common/`, delete 4 scaffold services. Monolith (`src/`) remains the primary application. Docker Compose for local development only.

**Tech Stack:** Python 3.12, ruff, Vitest + React Testing Library, Docker, docker-compose

**Spec:** `docs/superpowers/specs/2026-03-28-p4-p8-improvement-plan-design.md`

---

## P4: Quickfix — Base Cleanup

### Task 1: Fix E501 line-length violations

**Files:**
- Modify: `src/core/config.py:298`
- Modify: `src/core/cookie_grabber.py:563`
- Modify: `src/core/doctor.py:31`
- Modify: `src/core/slider_solver.py:411`
- Modify: `src/dashboard/config_service.py:695`
- Modify: `src/dashboard/mimic_ops.py:2496,2517`
- Modify: `src/dashboard/services/cookie_service.py:422`
- Modify: `src/dashboard_server.py:630`
- Modify: `src/modules/messages/dedup.py:133,144`
- Modify: `src/modules/messages/quote_composer.py:188`
- Modify: `src/modules/messages/reply_engine.py:252,282,292,302,393,436,479,565,689,721,804,919,943`
- Modify: `src/modules/messages/service.py:123,1335`
- Modify: `src/modules/messages/ws_live.py:1476,1690`
- Modify: `src/modules/virtual_goods/service.py:352,403,413,484,641,1134,1139`
- Modify: `src/modules/virtual_goods/store.py:85,93,94`

- [ ] **Step 1: Run ruff to list all E501 errors**

Run: `ruff check src/ --select E501`
Expected: 39 errors listed with file:line:col format

- [ ] **Step 2: Fix E501 errors in each file**

For each flagged line, break long lines to fit within 120-char limit. Common patterns:
- Break function calls across multiple lines with proper indentation
- Use parenthesized string concatenation for long strings
- Break long dict/list literals across lines

The worst offenders (fix carefully):
- `config_service.py:695` — 303 chars, likely a long JSON/dict literal
- `reply_engine.py:689` — 200 chars, likely a long string/log message
- `reply_engine.py:252` — 180 chars, likely a long conditional

- [ ] **Step 3: Verify ruff passes**

Run: `ruff check src/`
Expected: 0 errors

- [ ] **Step 4: Run tests to verify no breakage**

Run: `./venv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -5`
Expected: All tests pass (1726+ passed)

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "style: fix 39 E501 line-length violations across src/"
```

---

### Task 2: Unify version strings to 10.0.0

**Files:**
- Modify: `pyproject.toml:3`
- Modify: `client/package.json:3`

- [ ] **Step 1: Update pyproject.toml**

In `pyproject.toml` line 3, change `version = "9.5.0"` to `version = "10.0.0"`

- [ ] **Step 2: Update client/package.json**

In `client/package.json` line 3, change `"version": "9.2.0"` to `"version": "10.0.0"`

- [ ] **Step 3: Verify all three match**

Run: `grep -n 'version' src/__init__.py pyproject.toml client/package.json | head -10`
Expected: All three show `10.0.0`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml client/package.json
git commit -m "chore: unify version to 10.0.0 across all files"
```

---

### Task 3: Sync P0-P3 plan document checkboxes

**Files:**
- Modify: `docs/superpowers/plans/2026-03-27-p0-security-fixes.md`
- Modify: `docs/superpowers/plans/2026-03-27-p1-backend-refactor.md`
- Modify: `docs/superpowers/plans/2026-03-27-p2-frontend-improvements.md`
- Modify: `docs/superpowers/plans/2026-03-27-p3-architecture-longterm.md`

- [ ] **Step 1: Mark P0 tasks complete**

In `docs/superpowers/plans/2026-03-27-p0-security-fixes.md`, change all `- [ ]` to `- [x]`. Verify each checkbox item is actually implemented in the codebase before marking complete.

- [ ] **Step 2: Mark P1 tasks complete**

In `docs/superpowers/plans/2026-03-27-p1-backend-refactor.md`, change all `- [ ]` to `- [x]`. Verify each item (e.g. `pricing_calculator.py` exists, `pricing_calculator` module exists, `__getattr__` in MimicOps) before marking.

- [ ] **Step 3: Mark P2 tasks complete**

In `docs/superpowers/plans/2026-03-27-p2-frontend-improvements.md`, change all `- [ ]` to `- [x]`. Verify each item (e.g. `strictNullChecks` in tsconfig.json, `React.lazy` in App.tsx, `Analytics.tsx` deleted) before marking.

- [ ] **Step 4: Mark P3 tasks complete**

In `docs/superpowers/plans/2026-03-27-p3-architecture-longterm.md`, change all `- [ ]` to `- [x]`. Verify each item (e.g. `migration.py` exists, `vitest.config.ts` exists, sub-components extracted) before marking.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/
git commit -m "docs: sync P0-P3 plan checkboxes — all completed"
```

---

### Task 4: Evaluate and update brand-assets plans

**Files:**
- Modify: `docs/superpowers/plans/2026-03-21-brand-assets-rename.md`
- Modify: `docs/superpowers/plans/2026-03-21-brand-assets-zip-upload.md`

- [ ] **Step 1: Verify brand-assets tests exist and pass**

Run: `./venv/bin/python -m pytest tests/test_brand_assets_rename_cov100.py tests/test_brand_assets_rename_route_cov100.py tests/test_brand_assets_zip_cov100.py -v --tb=short 2>&1 | tail -20`
Expected: All pass

- [ ] **Step 2: Mark brand-assets plans complete**

If tests pass, change all `- [ ]` to `- [x]` in both:
- `docs/superpowers/plans/2026-03-21-brand-assets-rename.md`
- `docs/superpowers/plans/2026-03-21-brand-assets-zip-upload.md`

If tests fail, add `> **Status: CANCELLED**` header and close all checkboxes as cancelled.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/
git commit -m "docs: mark brand-assets plans complete"
```

---

### Task 5: Cancel infrastructure plans (incompatible with Option B)

**Files:**
- Modify: `docs/superpowers/plans/2026-03-27-phase1-infrastructure.md`
- Modify: `docs/superpowers/plans/2026-03-27-phase2-service-decomposition.md`

- [ ] **Step 1: Add cancellation notice to phase1 plan**

At the top of `docs/superpowers/plans/2026-03-27-phase1-infrastructure.md`, add after the header:

```markdown
> **Status: CANCELLED** — Superseded by MICROSERVICE_ROADMAP.md Option B (simplify). K8s/Terraform infrastructure for removed services is no longer needed.
```

- [ ] **Step 2: Add cancellation notice to phase2 plan**

Same for `docs/superpowers/plans/2026-03-27-phase2-service-decomposition.md`:

```markdown
> **Status: CANCELLED** — Superseded by MICROSERVICE_ROADMAP.md Option B (simplify). Service decomposition halted; scaffolding services will be removed.
```

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/plans/
git commit -m "docs: cancel phase1/phase2 infra plans (Option B)"
```

---

## P5: Cleanup — Microservice Simplification

### Task 6: Delete scaffold microservice directories

**Files:**
- Delete: `services/ai-service/` (10 files)
- Delete: `services/message-service/` (9 files)
- Delete: `services/order-service/` (7 files)
- Delete: `services/quote-service/` (7 files)
- Delete: `k8s/canary-deployment.yaml`

- [ ] **Step 1: Delete the four service directories**

```bash
rm -rf services/ai-service/
rm -rf services/message-service/
rm -rf services/order-service/
rm -rf services/quote-service/
```

- [ ] **Step 2: Delete canary deployment manifest**

```bash
rm k8s/canary-deployment.yaml
```

- [ ] **Step 3: Verify services/ only contains gateway + common**

Run: `ls services/`
Expected: `common/  conftest.py  gateway-service/  pytest.ini`

- [ ] **Step 4: Run tests to verify nothing breaks**

Run: `./venv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -5`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove 4 scaffold services and canary manifest (Option B)"
```

---

### Task 7: Update references to removed services

**Files:**
- Modify: `docs/ARCHITECTURE.md` (lines 27-30 list services)
- Modify: `docs/MICROSERVICE_ROADMAP.md` (extensive references)
- Modify: `CHANGELOG.md` (lines 28-51, 59 list services)
- Modify: `scripts/rollback.sh` (lines 4, 42-51, 193 list services)

- [ ] **Step 1: Update ARCHITECTURE.md**

Read `docs/ARCHITECTURE.md`. Remove or rewrite sections that list the 4 deleted services as running components. Update the architecture diagram to show only:
- Dashboard Server (src/, :8091)
- Gateway Service (services/gateway-service/, :8000)
- Common Library (services/common/)

Keep the honest assessment tone. Add note that Option B was executed.

- [ ] **Step 2: Update MICROSERVICE_ROADMAP.md**

Add status banner at top:
```markdown
> **Status: DECIDED — Option B executed on 2026-03-28.** Four scaffold services removed. See git history for details.
```

Keep the document body as-is (historical decision record).

- [ ] **Step 3: Update CHANGELOG.md**

Remove entries that list features of ai-service, message-service, order-service, quote-service as if they exist. Add new entry:
```markdown
## [10.0.1] - 2026-03-28
### Changed
- Removed scaffold services (ai-service, message-service, order-service, quote-service) per Option B
- Simplified to monolith + gateway-service architecture
```

- [ ] **Step 4: Update scripts/rollback.sh**

Read `scripts/rollback.sh`. Remove the 4 deleted services from the rollback targets list. Keep gateway-service if it's listed.

- [ ] **Step 5: Verify no dangling references**

Run: `grep -rn "ai-service\|message-service\|order-service\|quote-service" --include="*.py" --include="*.sh" --include="*.yml" --include="*.yaml" --include="*.toml" .`
Expected: No results outside `docs/superpowers/` (historical plans/specs are OK to keep)

- [ ] **Step 6: Commit**

```bash
git add docs/ARCHITECTURE.md docs/MICROSERVICE_ROADMAP.md CHANGELOG.md scripts/rollback.sh
git commit -m "docs: update architecture docs to reflect Option B simplification"
```

---

### Task 8: Verify retained services pass tests

**Note:** CI workflow (`.github/workflows/ci.yml`) already only references `services/common` and `services/gateway-service` — no CI changes needed after deletions.

**Files:**
- Test: `services/gateway-service/tests/`
- Test: `services/common/tests/`

- [ ] **Step 1: Run gateway-service tests**

Run: `cd services && python -m pytest gateway-service/tests/ -v --tb=short 2>&1 | tail -20`
Expected: 11 tests pass

- [ ] **Step 2: Run common library tests**

Run: `cd services && python -m pytest common/tests/ -v --tb=short 2>&1 | tail -20`
Expected: 40 tests pass

- [ ] **Step 3: Run full CI lint + test suite**

Run: `ruff check src/ && ./venv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -5`
Expected: 0 ruff errors, all tests pass

---

## P6: Testing — Frontend Test Coverage Enhancement

### Task 9: Add test script and setup to package.json

**Files:**
- Modify: `client/package.json` (add test script)
- Modify: `client/vitest.config.ts` (add setup file, coverage config)

- [ ] **Step 1: Add test script to package.json**

In `client/package.json`, add to `scripts`:
```json
"test": "vitest run",
"test:watch": "vitest",
"test:coverage": "vitest run --coverage"
```

- [ ] **Step 2: Create test setup file**

Create `client/src/test-setup.ts`:
```typescript
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 3: Update vitest.config.ts to use setup file**

In `client/vitest.config.ts`, update `setupFiles`:
```typescript
setupFiles: ["./src/test-setup.ts"],
```

- [ ] **Step 4: Verify existing tests still pass**

Run: `cd client && npm test`
Expected: 2 existing tests pass

- [ ] **Step 5: Commit**

```bash
git add client/package.json client/vitest.config.ts client/src/test-setup.ts
git commit -m "test(frontend): add test scripts and setup configuration"
```

---

### Task 10: Add API layer tests

**Files:**
- Create: `client/src/api/__tests__/index.test.ts`
- Create: `client/src/api/__tests__/accounts.test.ts`
- Create: `client/src/api/__tests__/config.test.ts`
- Create: `client/src/api/__tests__/dashboard.test.ts`
- Create: `client/src/api/__tests__/listing.test.ts`
- Create: `client/src/api/__tests__/xianguanjia.test.ts`

- [ ] **Step 1: Write test for API error handling (index.ts)**

Create `client/src/api/__tests__/index.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { api } from "../index";

describe("API client configuration", () => {
  it("has /api base URL", () => {
    expect(api.defaults.baseURL).toBeTruthy();
  });

  it("has 15s timeout", () => {
    expect(api.defaults.timeout).toBe(15000);
  });
});
```

- [ ] **Step 2: Write remaining API module tests**

Follow the same mock pattern for each API module. For each file, mock `api` from `../index` and test that each exported function calls the correct endpoint:

Create `client/src/api/__tests__/accounts.test.ts`:
```typescript
import { getAccounts } from "../accounts";
import { api } from "../index";
vi.mock("../index", () => ({ api: { get: vi.fn() } }));
describe("accounts API", () => {
  it("calls GET /accounts", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { ok: true, data: [] } });
    await getAccounts();
    expect(api.get).toHaveBeenCalledWith("/accounts");
  });
});
```

Create `client/src/api/__tests__/config.test.ts`:
```typescript
import { getSystemConfig, saveSystemConfig, getConfigSections } from "../config";
import { api } from "../index";
vi.mock("../index", () => ({ api: { get: vi.fn(), put: vi.fn() } }));
describe("config API", () => {
  it("calls GET /config for getSystemConfig", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { config: {} } });
    await getSystemConfig();
    expect(api.get).toHaveBeenCalledWith("/config");
  });
  it("calls PUT /config for saveSystemConfig", async () => {
    vi.mocked(api.put).mockResolvedValue({ data: { config: {} } });
    await saveSystemConfig({ key: "val" });
    expect(api.put).toHaveBeenCalledWith("/config", { key: "val" });
  });
  it("calls GET /config/sections for getConfigSections", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { sections: [] } });
    await getConfigSections();
    expect(api.get).toHaveBeenCalledWith("/config/sections");
  });
});
```

Create `client/src/api/__tests__/dashboard.test.ts`:
```typescript
import { getSystemStatus, getDashboardSummary, serviceControl } from "../dashboard";
import { api } from "../index";
vi.mock("../index", () => ({ api: { get: vi.fn(), post: vi.fn() } }));
describe("dashboard API", () => {
  it("calls GET /status for getSystemStatus", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: {} });
    await getSystemStatus();
    expect(api.get).toHaveBeenCalledWith("/status");
  });
  it("calls GET /summary for getDashboardSummary", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { data: {} } });
    await getDashboardSummary();
    expect(api.get).toHaveBeenCalledWith("/summary");
  });
  it("calls POST /service/control for serviceControl", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} });
    await serviceControl("start");
    expect(api.post).toHaveBeenCalledWith("/service/control", { action: "start" });
  });
});
```

Create `client/src/api/__tests__/listing.test.ts`:
```typescript
import { getTemplates, getBrandAssets, getPublishQueue } from "../listing";
import { api } from "../index";
vi.mock("../index", () => ({ api: { get: vi.fn(), post: vi.fn() } }));
describe("listing API", () => {
  it("calls GET /listing/templates for getTemplates", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: {} });
    await getTemplates();
    expect(api.get).toHaveBeenCalledWith("/listing/templates");
  });
  it("calls GET /brand-assets for getBrandAssets", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { ok: true, assets: [] } });
    await getBrandAssets();
    expect(api.get).toHaveBeenCalledWith("/brand-assets", { params: {} });
  });
  it("calls GET /publish-queue for getPublishQueue", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { ok: true, items: [] } });
    await getPublishQueue();
    expect(api.get).toHaveBeenCalledWith("/publish-queue", { params: {} });
  });
});
```

Create `client/src/api/__tests__/xianguanjia.test.ts`:
```typescript
import { getProducts, getOrders } from "../xianguanjia";
import { api } from "../index";
vi.mock("../index", () => ({ api: { post: vi.fn() } }));
describe("xianguanjia API", () => {
  it("calls proxyXgjApi for getProducts", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { ok: true, data: {} } });
    await getProducts(1, 10);
    expect(api.post).toHaveBeenCalled();
  });
  it("calls proxyXgjApi for getOrders", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { ok: true, data: {} } });
    await getOrders({ page_no: 1 });
    expect(api.post).toHaveBeenCalled();
  });
});
```

- [ ] **Step 3: Run tests**

Run: `cd client && npm test`
Expected: All tests pass (10+ total now)

- [ ] **Step 4: Commit**

```bash
git add client/src/api/__tests__/
git commit -m "test(frontend): add API layer unit tests"
```

---

### Task 11: Add React component tests

**Files:**
- Create: `client/src/components/__tests__/CollapsibleSection.test.tsx`
- Create: `client/src/components/__tests__/Pagination.test.tsx`
- Create: `client/src/components/__tests__/ErrorBoundary.test.tsx`

- [ ] **Step 1: Write CollapsibleSection test**

Create `client/src/components/__tests__/CollapsibleSection.test.tsx`:

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import CollapsibleSection from "../CollapsibleSection";

describe("CollapsibleSection", () => {
  it("renders title", () => {
    render(
      <CollapsibleSection title="Test Section">
        <p>Content</p>
      </CollapsibleSection>
    );
    expect(screen.getByText("Test Section")).toBeInTheDocument();
  });

  it("toggles content on click", () => {
    render(
      <CollapsibleSection title="Test" defaultOpen={true}>
        <p>Hidden Content</p>
      </CollapsibleSection>
    );
    expect(screen.getByText("Hidden Content")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Test"));
    expect(screen.queryByText("Hidden Content")).not.toBeInTheDocument();
  });

  it("renders summary when closed", () => {
    render(
      <CollapsibleSection title="Test" summary="Summary text" defaultOpen={false}>
        <p>Content</p>
      </CollapsibleSection>
    );
    expect(screen.getByText("Summary text")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Write Pagination test**

Create `client/src/components/__tests__/Pagination.test.tsx`:

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Pagination from "../Pagination";

describe("Pagination", () => {
  it("renders nothing when total pages <= 1", () => {
    const { container } = render(
      <Pagination current={1} total={5} pageSize={10} onChange={vi.fn()} />
    );
    expect(container.innerHTML).toBe("");
  });

  it("calls onChange when page clicked", () => {
    const onChange = vi.fn();
    render(
      <Pagination current={1} total={25} pageSize={10} onChange={onChange} />
    );
    const nextButton = screen.getByLabelText("下一页");
    fireEvent.click(nextButton);
    expect(onChange).toHaveBeenCalledWith(2);
  });
});
```

- [ ] **Step 3: Write ErrorBoundary test**

Create `client/src/components/__tests__/ErrorBoundary.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ErrorBoundary from "../ErrorBoundary";

function ThrowingChild(): JSX.Element {
  throw new Error("Test error");
}

describe("ErrorBoundary", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <p>Normal content</p>
      </ErrorBoundary>
    );
    expect(screen.getByText("Normal content")).toBeInTheDocument();
  });

  it("renders fallback on error", () => {
    render(
      <ErrorBoundary>
        <ThrowingChild />
      </ErrorBoundary>
    );
    expect(screen.getByRole("button", { name: /reload/i })).toBeInTheDocument();
  });
});
```

- [ ] **Step 4: Run tests**

Run: `cd client && npm test`
Expected: All component tests pass

- [ ] **Step 5: Commit**

```bash
git add client/src/components/__tests__/
git commit -m "test(frontend): add CollapsibleSection, Pagination, ErrorBoundary tests"
```

---

### Task 12: Add dashboard card component tests

**Files:**
- Create: `client/src/pages/dashboard/__tests__/PublishQueueCard.test.tsx`
- Create: `client/src/pages/dashboard/__tests__/SliderStatsCard.test.tsx`
- Create: `client/src/pages/dashboard/__tests__/XgjControlPanel.test.tsx`

- [ ] **Step 1: Write PublishQueueCard test**

Create `client/src/pages/dashboard/__tests__/PublishQueueCard.test.tsx`:

```tsx
import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import PublishQueueCard from "../PublishQueueCard";

vi.mock("../../../api/listing", () => ({
  getPublishQueue: vi.fn(),
}));

import { getPublishQueue } from "../../../api/listing";

describe("PublishQueueCard", () => {
  it("renders loading then shows queue count", async () => {
    vi.mocked(getPublishQueue).mockResolvedValue({
      data: { ok: true, items: [
        { id: "1", status: "draft" },
        { id: "2", status: "ready" },
      ] },
    } as any);
    render(<PublishQueueCard />);
    await waitFor(() => {
      expect(screen.getByText(/2/)).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Write SliderStatsCard test**

Create `client/src/pages/dashboard/__tests__/SliderStatsCard.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import SliderStatsCard from "../SliderStatsCard";

vi.mock("../../../api/dashboard", () => ({
  getSliderStats: vi.fn(),
}));

import { getSliderStats } from "../../../api/dashboard";

describe("SliderStatsCard", () => {
  it("returns null when no data", () => {
    vi.mocked(getSliderStats).mockResolvedValue({
      data: { ok: false },
    } as any);
    const { container } = render(<SliderStatsCard />);
    expect(container.innerHTML).toBe("");
  });
});
```

- [ ] **Step 3: Write XgjControlPanel test**

Create `client/src/pages/dashboard/__tests__/XgjControlPanel.test.tsx`:

```tsx
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import XgjControlPanel from "../XgjControlPanel";

vi.mock("../../../api/index", () => ({
  api: { post: vi.fn() },
}));

import { api } from "../../../api/index";

describe("XgjControlPanel", () => {
  it("renders form inputs", () => {
    render(<XgjControlPanel />);
    expect(screen.getByLabelText(/appKey/i)).toBeInTheDocument();
  });

  it("test button calls api.post", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { ok: true } } as any);
    render(<XgjControlPanel />);
    const testBtn = screen.getByRole("button", { name: /test|连接/i });
    fireEvent.click(testBtn);
    await waitFor(() => {
      expect(api.post).toHaveBeenCalled();
    });
  });
});
```

- [ ] **Step 4: Run tests**

Run: `cd client && npm test`
Expected: All tests pass (12+ total)

- [ ] **Step 5: Commit**

```bash
git add client/src/pages/dashboard/__tests__/
git commit -m "test(frontend): add dashboard card component tests"
```

---

### Task 13: Add custom hook tests

**Files:**
- Modify: `client/src/hooks/__tests__/useHealthCheck.test.tsx` (expand existing)

- [ ] **Step 1: Expand useHealthCheck test**

Read `client/src/hooks/useHealthCheck.test.tsx` (already exists). Add test cases for:
- Initial loading state is true
- Calls refresh() triggers re-fetch
- Handles error gracefully (returns "unreachable" message)

```typescript
it("starts in loading state", () => {
  vi.mocked(api.get).mockReturnValue(new Promise(() => {}));
  const { result } = renderHook(() => useHealthCheck(true));
  expect(result.current.loading).toBe(true);
});

it("refresh() triggers re-fetch", async () => {
  vi.mocked(api.get).mockResolvedValue({ data: { python: { ok: true, message: "up" } } });
  const { result } = renderHook(() => useHealthCheck(false));
  await act(async () => {
    await result.current.refresh();
  });
  expect(api.get).toHaveBeenCalledWith("/health/check");
});
```

Note: Import `renderHook`, `act` from `@testing-library/react`. Add `@testing-library/react` as devDep if not present.

- [ ] **Step 2: Run tests**

Run: `cd client && npm test`
Expected: All hook tests pass

- [ ] **Step 3: Commit**

```bash
git add client/src/hooks/__tests__/
git commit -m "test(frontend): expand useHealthCheck hook tests"
```

---

### Task 14: Update coverage configuration and codecov

**Files:**
- Modify: `client/vitest.config.ts`
- Modify: `codecov.yml`

- [ ] **Step 1: Add coverage configuration to vitest.config.ts**

Add coverage config:
```typescript
coverage: {
  provider: "v8",
  reporter: ["text", "lcov"],
  include: ["src/**/*.{ts,tsx}"],
  exclude: ["src/**/*.test.*", "src/**/__tests__/**", "src/vite-env.d.ts", "src/types/**"],
},
```

- [ ] **Step 2: Update codecov.yml for frontend coverage**

Read `codecov.yml` and remove the `client/**/*` ignore pattern (if present). Add a frontend component:

```yaml
component_management:
  individual_components:
    - component_id: frontend
      paths:
        - client/src/
```

Run: `cd client && npm run test:coverage`
Expected: Coverage report generated, all tests pass

- [ ] **Step 3: Commit**

- [ ] **Step 3: Run coverage report**

Run: `cd client && npm run test:coverage`
Expected: Coverage report generated, all tests pass

- [ ] **Step 4: Commit**

```bash
git add client/vitest.config.ts codecov.yml
git commit -m "test(frontend): add coverage configuration and codecov frontend section"
```

---

## P7: Infra — Infrastructure Integration

### Task 15: Create monolith Dockerfile

**Files:**
- Create: `Dockerfile` (project root)
- Create: `.dockerignore`

- [ ] **Step 1: Create .dockerignore**

Create `.dockerignore`:
```
.git
.github
__pycache__
*.pyc
*.pyo
node_modules
vendor
data/*.db
data/*.db-journal
dist
*.egg-info
.venv
venv
.env
*.log
.DS_Store
.claude
```

- [ ] **Step 2: Create root Dockerfile**

Create `Dockerfile`:
```dockerfile
# --- Stage 1: Build frontend ---
FROM node:20-slim AS frontend
WORKDIR /build
COPY client/package.json client/package-lock.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# --- Stage 2: Python app ---
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY database/ ./database/
COPY --from=frontend /build/dist ./client/dist/

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8091
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8091/api/health')" || exit 1

CMD ["python", "-m", "src.dashboard_server", "--host", "0.0.0.0", "--port", "8091"]
```

- [ ] **Step 3: Verify Dockerfile builds (if Docker available)**

Run: `docker build -t xianyuflow:latest . 2>&1 | tail -10`
Expected: Build succeeds (or skip if Docker not available)

- [ ] **Step 4: Commit**

```bash
git add Dockerfile .dockerignore
git commit -m "infra: add monolith Dockerfile with multi-stage frontend build"
```

---

### Task 16: Create docker-compose.yml

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create docker-compose.yml**

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8091:8091"
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    env_file:
      - .env
    restart: unless-stopped

  gateway:
    build:
      context: .
      dockerfile: services/gateway-service/Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

Note: No Redis — app uses SQLite. Gateway Dockerfile uses `services/` context.

- [ ] **Step 2: Verify compose config is valid**

Run: `docker-compose config 2>&1 | head -20`
Expected: Valid YAML output (or skip if Docker not available)

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "infra: add docker-compose for local development"
```

---

### Task 17: Update Helm chart and infrastructure docs

**Files:**
- Modify: `infra/helm/xianyuflow-infra/Chart.yaml`
- Modify: `docs/DEPLOYMENT.md`

- [ ] **Step 1: Update Helm chart description**

In `infra/helm/xianyuflow-infra/Chart.yaml`, update description to note these are optional future dependencies, not currently used:

```yaml
description: XianyuFlow infrastructure Helm chart (optional — Redis, PostgreSQL, Kafka not currently used by main application)
```

- [ ] **Step 2: Update DEPLOYMENT.md**

Add a Docker section to `docs/DEPLOYMENT.md`:

```markdown
## X、Docker 部署（实验性）

    # 构建并启动
    docker-compose up -d

    # 查看日志
    docker-compose logs -f app

| 容器 | 端口 | 说明 |
|------|------|------|
| app | 8091 | 主应用（Dashboard + API） |
| gateway | 8000 | Open Platform 适配 API |
```

- [ ] **Step 3: Commit**

```bash
git add infra/helm/xianyuflow-infra/Chart.yaml docs/DEPLOYMENT.md
git commit -m "docs: update deployment docs with Docker instructions"
```

---

### Task 18: Update QUICKSTART.md

**Files:**
- Modify: `QUICKSTART.md`

- [ ] **Step 1: Add Docker quickstart option**

Add a section at the top of `QUICKSTART.md` for Docker-based quickstart:

```markdown
## 快速开始（Docker）

    git clone https://github.com/G3niusYukki/realxianyu.git && cd realxianyu
    cp .env.example .env   # 编辑填写必要配置
    docker-compose up -d
    # 访问 http://localhost:8091

## 快速开始（裸机）
```

Keep existing bare-metal instructions below.

- [ ] **Step 2: Commit**

```bash
git add QUICKSTART.md
git commit -m "docs: add Docker quickstart option to QUICKSTART"
```

---

## P8: Polish — Final Touches

### Task 19: Resolve Analytics page

**Files:**
- Modify: `client/src/App.tsx` (if route needs update)

- [ ] **Step 1: Evaluate current Analytics state**

Read `client/src/App.tsx` to check the Analytics route. Currently it redirects to `/dashboard`.

Decision: Keep the redirect. The Analytics functionality lives within Dashboard's analytics section. Remove the unused `/analytics` route entry to avoid dead code.

- [ ] **Step 2: Remove or update Analytics route**

If `App.tsx` has a route like `<Route path="/analytics" element={<Navigate to="/dashboard" />}>`, update it to remove the dead route entirely. Update any nav links that reference `/analytics`.

- [ ] **Step 3: Commit**

```bash
git add client/src/App.tsx
git commit -m "chore: remove dead Analytics route"
```

---

### Task 20: Documentation sweep

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTRIBUTING.md`

- [ ] **Step 1: Update README.md**

Ensure README reflects:
- v10.0.0 version
- Simplified architecture (monolith + gateway-service)
- Docker quickstart option
- Updated directory structure (services/ only has gateway + common)

- [ ] **Step 2: Update CHANGELOG.md**

Add unreleased section with all P4-P8 changes:

```markdown
## [10.1.0] - 2026-03-28
### Added
- Frontend test suite (Vitest + React Testing Library)
- Dockerfile and docker-compose.yml for local development
- .dockerignore

### Changed
- Unified version to 10.0.0 across all files
- Removed scaffold services per Option B (monolith + gateway only)
- Updated architecture documentation

### Removed
- services/ai-service/ (scaffold)
- services/message-service/ (scaffold)
- services/order-service/ (scaffold)
- services/quote-service/ (scaffold)
- k8s/canary-deployment.yaml
- Dead Analytics page route
```

- [ ] **Step 3: Commit**

```bash
git add README.md CHANGELOG.md CONTRIBUTING.md
git commit -m "docs: update documentation for v10.1.0 release"
```

---

### Task 21: Final validation

- [ ] **Step 1: Run ruff lint**

Run: `ruff check src/`
Expected: 0 errors

- [ ] **Step 2: Run backend tests**

Run: `./venv/bin/python -m pytest tests/ -q --tb=short`
Expected: All pass

- [ ] **Step 3: Run frontend build**

Run: `cd client && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Run frontend tests**

Run: `cd client && npm test`
Expected: All pass (10+ tests)

- [ ] **Step 5: Verify git status is clean**

Run: `git status`
Expected: clean working tree

- [ ] **Step 6: Final commit if any fixes needed**

If any issues found in steps 1-4, fix and commit with:
```bash
git commit -m "fix: address final validation issues"
```
