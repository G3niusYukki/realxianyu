# Microservice Migration Roadmap

**Status**: Draft
**Last Updated**: 2026-03-28
**Owner**: Architecture / Backend Team

---

## Executive Summary

This document evaluates the current state of the `services/` directory (microservices architecture) versus the `src/` monolith, and outlines two options for the future direction of the codebase. After assessment, **Option B (Simplify)** is recommended at this stage, with a clear decision gate for revisiting Option A.

---

## 1. 现状评估 (Current State Assessment)

### 1.1 Directory Structure

```
.
|-- services/           # Microservices attempt
|   |-- gateway-service/     # COMPLETE - FastAPI app
|   |   |-- app/main.py
|   |   |-- app/signing.py
|   |   |-- app/routes/
|   |   |-- Dockerfile
|   |   |-- pyproject.toml
|   |   |-- tests/           # Tests exist
|   |
|   |-- ai-service/          # INCOMPLETE - scaffolding only
|   |   |-- app/main.py
|   |   |-- app/client.py
|   |   |-- app/context.py
|   |   |-- app/state_machine.py
|   |   |-- app/prompts/
|   |   |-- Dockerfile
|   |   |-- pyproject.toml
|   |
|   |-- message-service/     # INCOMPLETE - scaffolding only
|   |   |-- app/main.py
|   |   |-- app/websocket.py
|   |   |-- app/handler.py
|   |   |-- app/reply.py
|   |   |-- app/connection_pool.py
|   |   |-- Dockerfile
|   |   |-- pyproject.toml
|   |
|   |-- order-service/       # INCOMPLETE - scaffolding only
|   |   |-- app/main.py
|   |   |-- app/models.py
|   |   |-- app/state_machine.py
|   |   |-- app/virtual_goods.py
|   |   |-- Dockerfile
|   |   |-- pyproject.toml
|   |
|   |-- quote-service/       # INCOMPLETE - scaffolding only
|   |   |-- app/main.py
|   |   |-- app/engine.py
|   |   |-- app/cost_table.py
|   |   |-- app/providers.py
|   |   |-- Dockerfile
|   |   |-- pyproject.toml
|   |
|   |-- common/              # PARTIAL - shared utilities with tests
|   |   |-- xianyuflow_common/
|   |   |   |-- cache.py         # MultiLevelCache
|   |   |   |-- database.py      # Database wrappers
|   |   |   |-- dual_write.py    # DualWriteManager
|   |   |   |-- kafka.py
|   |   |   |-- metrics.py
|   |   |   |-- config.py
|   |   |   |-- telemetry.py
|   |   |-- tests/               # 51 tests for common components
|   |   |-- schema/
|   |   |-- pyproject.toml
|
|-- src/                  # Monolith - ALL business logic lives here
    |-- main.py
    |-- modules/
    |   |-- accounts/
    |   |-- analytics/
    |   |-- compliance/
    |   |-- content/
    |   |-- followup/
    |   |-- growth/
    |   |-- listing/
    |   |-- media/
    |   |-- messages/
    |   |-- operations/
    |   |-- orders/
    |   |-- quote/
    |   |-- ticketing/
    |   |-- virtual_goods/
    |-- cli/
    |-- core/
    |-- integrations/
    |-- dashboard/
```

### 1.2 Service Status Summary

| Service | Status | Implementation | Dockerfile | Tests | Independently Deployable |
|---------|--------|---------------|------------|-------|-------------------------|
| `gateway-service` | **Complete** | Full FastAPI app with routing and signing | Yes | Yes | **Yes** |
| `ai-service` | **Incomplete** | Skeleton only, no real implementation | Yes | No | No |
| `message-service` | **Incomplete** | Skeleton only, no real implementation | Yes | No | No |
| `order-service` | **Incomplete** | Skeleton only, no real implementation | Yes | No | No |
| `quote-service` | **Incomplete** | Skeleton only, no real implementation | Yes | No | No |
| `common/` | **Partial** | Shared utilities with 51 tests | N/A | Yes | Shared lib only |

### 1.3 Key Insight

The `services/` directory represents an attempted microservices decomposition that was started but never finished. Only `gateway-service` is fully functional and independently deployable. All business logic for messages, orders, quotes, listings, and virtual goods **still lives exclusively in `src/`**. The incomplete services exist as scaffolding with placeholder code.

Meanwhile, `services/common/` has genuine infrastructure work: `MultiLevelCache`, database wrappers, and `DualWriteManager` (with 51 passing tests). This is valuable shared infrastructure that could serve either option.

---

## 2. 方案 A — 推进迁移 (Option A — Push Migration)

### Overview

Continue the original plan: gradually extract services from the `src/` monolith into the `services/` directory, eventually achieving full microservices deployment.

### Migration Phases

#### Phase 1: Database Migration Foundation (Months 0-3)
**Goal**: Enable dual-write between SQLite (current) and PostgreSQL (target)

- Finalize `services/common/` PostgreSQL schema
- Implement `DualWriteManager` for transactional dual-write
- Run dual-write in shadow mode (read from SQLite, write to both, compare results)
- Validate data consistency between SQLite and PostgreSQL
- Document all SQL queries in `src/` that need migration

**Prerequisite**: `services/common/` already has `DualWriteManager` — this phase extends it.

#### Phase 2: First Service Extraction (Months 3-6)
**Goal**: Extract the lowest-risk service as a proof of concept

**Recommended**: Extract `quote-service` or `message-service` first.

Rationale for `quote-service`:
- Bounded domain with clear inputs/outputs
- Calculation-heavy, less transactional complexity
- AI-service already has quote-related prompts (can reuse)

Rationale for `message-service`:
- Well-isolated WebSocket handling
- Lower risk to core ordering flow

Steps:
1. Copy business logic from `src/modules/quote/` to `services/quote-service/`
2. Implement API contracts (FastAPI routes matching `gateway-service` expectations)
3. Add integration tests
4. Deploy `quote-service` alongside `src/` monolith
5. Route quote requests through `gateway-service` to the new service
6. Keep `src/` as fallback for 2 weeks, then cut over

#### Phase 3: Gateway Becomes True API Gateway (Months 6-9)
**Goal**: `gateway-service` routes to extracted services, not monolith

- Move from "monolith-first with service helpers" to "service-first"
- `gateway-service` routes requests to extracted services via HTTP/gRPC
- `src/` is called only for un-extracted functionality
- Implement service discovery (Consul, etcd, or static config)

#### Phase 4: Continue Extraction (Months 9-18)
**Goal**: Extract remaining services in priority order

1. `message-service` — WebSocket message handling
2. `order-service` — Order lifecycle and state machine
3. `ai-service` — AI context and state machine (already has scaffolding)

#### Phase 5: Kubernetes / Container Orchestration (Months 18+)
**Goal**: Full containerized deployment

- Migrate all services to Kubernetes/Docker Compose
- Implement service mesh (Istio or Linkerd)
- Add circuit breakers, retries, and observability
- Decommission `src/` monolith

### Pros
- Achieves the original microservices vision
- Enables independent scaling of high-traffic services
- Allows different teams to own different services
- Better fault isolation
- Technology flexibility per service

### Cons
- **Significant engineering effort** — current team has not committed to this
- Risk of incomplete migration leaving codebase in worse state
- Data consistency challenges during dual-write period
- Increased operational complexity
- Network latency between services
- Distributed tracing and debugging overhead

### Cost Estimate
- **Developer months**: 12-24 months for partial extraction (Phases 1-3)
- **Ongoing ops cost**: Higher (multiple services to monitor)

---

## 3. 方案 B — 精简 services/ (Option B — Simplify)

### Overview

Abandon the incomplete microservices migration and focus engineering effort on improving the `src/` monolith. Keep only the functional parts of `services/`.

### Changes

#### Keep
- `services/gateway-service/` — Already independently deployable, valuable as entry point
- `services/common/` — Shared utilities (`MultiLevelCache`, database wrappers, `DualWriteManager`, Kafka client, metrics, telemetry). These are genuinely useful infrastructure regardless of architecture.
- `services/common/tests/` — 51 tests for shared utilities

#### Remove
- `services/ai-service/` — No real implementation, only scaffolding
- `services/message-service/` — No real implementation, only scaffolding
- `services/order-service/` — No real implementation, only scaffolding
- `services/quote-service/` — No real implementation, only scaffolding

#### Refocus
- All new development happens in `src/`
- Continue improving `src/` architecture: better module boundaries, cleaner interfaces, improved tests
- `services/common/` remains available as a library for future extraction if needed
- `gateway-service` continues to proxy requests into `src/` (existing pattern)

### Pros
- **Eliminates dead code** — removes scaffolding that creates confusion
- **Focuses engineering effort** — no split attention between monolith and services
- **Reduces cognitive load** — developers only need to understand one codebase
- **Keeps valuable infrastructure** — `services/common/` has genuine utility
- **Preserves optionality** — `common/` and `gateway-service` remain ready for future extraction
- **Lower risk** — no data consistency challenges, no dual-write complexity

### Cons
- Monolith remains the single point of failure
- Cannot independently scale individual features
- All code uses same technology stack (no flexibility)
- Team growth may eventually require service boundaries

### Cost Estimate
- **Developer months**: 1-2 weeks to remove dead services
- **Ongoing cost**: Lower ops complexity

---

## 4. 建议时间线 (Recommended Timeline)

### Option B Path (Recommended)

```
Now (Month 0)
  |
  +-- Document decision (this document)
  +-- Get team sign-off on Option B
  |
Month 1
  |
  +-- Remove dead services: ai/, message/, order/, quote/
  +-- Update any references to removed services
  +-- Clean up CI/CD if it references removed services
  |
Ongoing
  |
  +-- Continue development in src/
  +-- Improve src/ module structure
  +-- Add tests to src/ coverage
```

### Option A Path (If Revisited Later)

```
Decision Gate (Month 0-3)
  |
  +-- Evaluate team capacity for microservices
  +-- Assess business needs (scaling, multi-team)
  +-- If "yes" to both, proceed with Option A
  |
Phase 1 (Months 0-3)
  |
  +-- Dual-write setup: SQLite -> PostgreSQL
  +-- Shadow mode validation
  |
Phase 2 (Months 3-6)
  |
  +-- Extract first service (quote or message)
  +-- Deploy alongside monolith
  |
Phase 3 (Months 6-9)
  |
  +-- Gateway becomes true API gateway
  +-- Route to extracted services
  |
Phase 4+ (Months 9+)
  |
  +-- Continue extraction
  +-- Eventually containerized deployment
```

### Decision Gate (Re-evaluate at 12 months)

If any of the following conditions are met, revisit Option A:
- Team grows to 5+ backend engineers needing clear ownership
- Traffic patterns require independent scaling of specific features
- Business requires different technology stacks per domain
- Compliance needs service-level isolation

---

## 5. 建议结论 (Recommendation)

### Recommended: **Option B — 精简 services/ (Simplify)**

**Rationale**:

1. **Cost-Benefit**: The microservices migration was started but never completed. Continuing requires significant investment with no near-term benefit. Removing dead scaffolding costs almost nothing and provides immediate clarity.

2. **Team Reality**: Based on the current state, the team has not committed the resources needed for a full microservices migration. Starting but not finishing creates more problems than it solves.

3. **Preserved Optionality**: Option B does not foreclose microservices. `services/common/` and `services/gateway-service/` remain ready for future extraction. The infrastructure investments are not wasted.

4. **Engineering Focus**: Removing confusion about "which services are real" lets the team focus on shipping product improvements in the monolith.

### What to Do Now

1. **This week**: Delete `services/ai-service/`, `services/message-service/`, `services/order-service/`, `services/quote-service/`
2. **This week**: Verify `services/gateway-service/` and `services/common/` still work
3. **This month**: Update any documentation mentioning the removed services
4. **This month**: Update CI/CD pipelines to remove references to deleted services
5. **Quarterly**: Re-evaluate whether Option A makes sense based on team growth and business needs

### If Option A is Chosen Instead

Proceed with the phases outlined in Section 2, starting with Phase 1 (Database Migration). Do not attempt to skip phases — the dual-write foundation is critical for data consistency during extraction.

---

## Appendix: Relevant Files

### services/ Status

- `services/gateway-service/app/main.py` — Complete FastAPI entry point
- `services/gateway-service/app/signing.py` — Request signing logic
- `services/gateway-service/app/routes/` — Route handlers (orders, products)
- `services/gateway-service/tests/` — Unit tests
- `services/gateway-service/Dockerfile` — Docker build
- `services/common/xianyuflow_common/cache.py` — MultiLevelCache implementation
- `services/common/xianyuflow_common/database.py` — Database wrappers
- `services/common/xianyuflow_common/dual_write.py` — DualWriteManager
- `services/common/tests/` — 51 tests for shared utilities

### Monolith Business Logic (src/)

All actual business logic lives in `src/modules/`:
- `src/modules/messages/` — Message handling
- `src/modules/orders/` — Order lifecycle
- `src/modules/quote/` — Quote calculation
- `src/modules/listing/` — Listing management
- `src/modules/virtual_goods/` — Virtual goods
- Plus: accounts, analytics, compliance, content, followup, growth, media, operations, ticketing

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-03-28 | P3 Architecture | Initial draft |
