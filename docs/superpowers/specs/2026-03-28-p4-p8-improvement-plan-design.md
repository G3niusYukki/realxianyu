---
name: P4-P8 Improvement Plan
date: 2026-03-28
status: approved
---

# P4-P8: Post-v10 Improvement Plan

## Background

After pulling 29 commits (P0 security fixes, P1 backend refactor, P2 frontend improvements, P3 architecture), the project has a mature monolith in `src/` but accumulated technical debt: lint errors (114), version mismatches across 3 files, stale plan documents, 4 unused microservice scaffolds, minimal frontend tests (2 files), no Docker orchestration, and missing features.

`MICROSERVICE_ROADMAP.md` recommends **Option B: simplify** — keep `gateway-service` + `common/`, delete scaffolding services. This plan adopts that recommendation.

## Scope

Deep improvement across 5 phases. No CI/CD deployment automation (deferred). Microservice decomposition halted per Option B.

---

## P4: Quickfix — Base Cleanup

Zero-risk fixes to restore a clean baseline.

### Tasks

| ID | Task | Details |
|----|------|---------|
| 4.1 | Ruff lint fix | `ruff check src/ --fix` (75 auto-fixable), manual fix remaining ~39. Primarily unused `noqa: F401` in `src/cli/*.py` and line-length issues. |
| 4.2 | Version unification | Set `src/__init__.py`, `pyproject.toml`, `client/package.json` all to `10.0.0`. |
| 4.3 | Sync P0-P3 plan checkboxes | Mark all completed tasks as `[x]` in `docs/superpowers/plans/2026-03-27-p{0,1,2,3}-*.md`. |
| 4.4 | Evaluate brand-assets plans | If `test_brand_assets_rename_cov100.py` and `test_brand_assets_zip_cov100.py` exist and pass, mark plans complete. Otherwise mark cancelled. |
| 4.5 | Cancel infra plans | Mark `phase1-infrastructure.md` and `phase2-service-decomposition.md` as cancelled (incompatible with Option B). |

**Exit criteria**: `ruff check src/` passes with 0 errors. All 3 version strings equal. Plan documents accurately reflect reality.

---

## P5: Cleanup — Microservice Simplification (Option B)

Execute the MICROSERVICE_ROADMAP.md Option B recommendation.

### Tasks

| ID | Task | Details |
|----|------|---------|
| 5.1 | Delete scaffold services | Remove `services/ai-service/`, `services/message-service/`, `services/order-service/`, `services/quote-service/`. |
| 5.2 | Verify retained services | Confirm `services/gateway-service/` and `services/common/` pass their tests independently. |
| 5.3 | Update CI workflow | Remove test matrix entries or scripts referencing deleted services from `.github/workflows/ci.yml`. |
| 5.4 | Update architecture docs | Rewrite `ARCHITECTURE.md`, `MICROSERVICE_ROADMAP.md`, `DEPLOYMENT.md` to reflect simplified structure. |
| 5.5 | Remove stale K8s manifests | Delete `k8s/canary-deployment.yaml` (references deleted message-service). |
| 5.6 | Remove stale Dockerfiles | Delete Dockerfiles for the 4 removed services. |

**Exit criteria**: `services/` contains only `gateway-service/` and `common/`. CI passes. No references to deleted services remain in docs or configs.

---

## P6: Testing — Test Coverage Enhancement

Frontend tests are critically low (2 test files vs 122 backend test files).

### Tasks

| ID | Task | Details |
|----|------|---------|
| 6.1 | Utility/API unit tests | Add Vitest tests for `utils/format.ts`, `api/accounts.ts`, `api/config.ts`, `api/dashboard.ts`, `api/listing.ts`, `api/xianguanjia.ts`. |
| 6.2 | React component tests | Add React Testing Library tests for `CollapsibleSection`, `PublishQueueCard`, `SliderStatsCard`, `XgjControlPanel`, `Pagination`, `ErrorBoundary`. |
| 6.3 | Custom hook tests | Expand `useHealthCheck.test.tsx`, add tests for any other custom hooks. |
| 6.4 | Backend service test audit | Verify `gateway-service` and `common` library test coverage is adequate. Add tests if gaps found. |
| 6.5 | Coverage threshold update | Adjust `vitest.config.ts` coverage thresholds and `codecov.yml` to reflect new frontend coverage. |

**Exit criteria**: Frontend has ≥10 test files covering utils, API layer, and key components. Backend service tests unchanged or improved. Coverage thresholds enforced in CI.

---

## P7: Infra — Infrastructure Integration

Enable one-command local development and containerized deployment.

### Tasks

| ID | Task | Details |
|----|------|---------|
| 7.1 | Monolith Dockerfile | Create `Dockerfile` at project root: Python 3.12-slim, install deps, build frontend, serve via `dashboard_server.py`. |
| 7.2 | docker-compose.yml | Orchestrate: main app (src/) + gateway-service + Redis. Development profile with volume mounts and hot-reload. |
| 7.3 | .dockerignore | Exclude `vendor/`, `data/*.db`, `node_modules/`, `dist/`, `.git/`, `__pycache__/`. |
| 7.4 | Helm chart cleanup | Remove deleted services from `infra/helm/xianyuflow-infra/Chart.yaml` dependencies. Keep only main app + gateway + infra components (Redis, PostgreSQL, Kafka). |
| 7.5 | Quickstart update | Update `QUICKSTART.md` with `docker-compose up` instructions alongside existing bare-metal steps. |

**Exit criteria**: `docker-compose up` starts the full application locally. All services healthy. Documentation accurate.

---

## P8: Polish — Final Touches

Bring the project to a release-ready state.

### Tasks

| ID | Task | Details |
|----|------|---------|
| 8.1 | Analytics page decision | Evaluate options: (a) restore independent Analytics page, (b) keep redirect to Dashboard with analytics section, (c) remove route entirely. Document decision. |
| 8.2 | Documentation sweep | Update `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` to reflect v10.0.0 state, simplified architecture, new test infrastructure. |
| 8.3 | Final validation | Run full suite: `ruff check src/`, `pytest tests/ -q`, `cd client && npm run build`, `docker-compose up` smoke test. All must pass. |

**Exit criteria**: All lint checks pass. All tests pass. Frontend builds. Docker starts. Documentation is current.

---

## Dependencies

```
P4 (quickfix)
 └─→ P5 (cleanup)
      └─→ P6 (testing) ──→ P8 (polish)
      └─→ P7 (infra)  ──→ P8 (polish)
```

P6 and P7 can run in parallel after P5 completes. P8 requires both P6 and P7.

## Out of Scope

- CI/CD deployment automation (staging/production)
- Microservice decomposition (Option B chosen)
- New business features
- Performance optimization beyond existing P3 work
