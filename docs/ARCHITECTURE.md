# 架构设计

> **Option B executed on 2026-03-28.** Four scaffold services (ai-service, message-service, order-service, quote-service) removed. Current architecture is monolith + gateway-service.

## 一、当前运行时架构

```text
浏览器
  ↓
Dashboard Server (src/, :8091)
  ├─ 托管 client/dist
  ├─ 暴露 /healthz
  └─ 暴露 /api/*
        ↓
     src/dashboard/routes/*
        ↓
     dashboard/services + modules + integrations

Gateway Service (services/gateway-service/, :8000)
  └─ 闲管家 Open Platform 适配 API

Common Library (services/common/)
  └─ 共享配置、数据库、缓存、双写等基础设施
```

这是当前完整、可用的运行链路。所有业务逻辑集中在 `src/` 单体中。

## 二、服务化资产

仓库中保留 `services/` 目录：

- `gateway-service` — 可单独运行，已能打通闲管家 Open Platform
- `common` — 共享配置、数据库、缓存、双写等库（含 51 个测试）

> 注意：`ai-service`、`message-service`、`order-service`、`quote-service` 已于 2026-03-28 移除（Option B）。

## 三、核心目录职责

### `src/`

当前主线 Python 代码：

- `src/dashboard_server.py`：HTTP 入口，服务 `8091`
- `src/dashboard/routes/`：Dashboard API 路由
- `src/dashboard/services/`：Cookie/XGJ 等服务层
- `src/modules/`：消息、订单、报价、商品、虚拟商品等业务模块
- `src/integrations/xianguanjia/`：闲管家 Open Platform / Virtual Supply 集成
- `src/cli/`：CLI 入口与运维命令

### `client/`

React/Vite 前端。开发期走 `5173`，构建后由 `src.dashboard_server` 托管。

### `services/`

服务化代码与公共库：

- `services/gateway-service`：FastAPI 网关，服务 `8000`
- `services/common`：共享配置、数据库、缓存、双写等库

### `infra/`

本地基础设施脚本、Terraform 和 Helm 资产。当前更准确的定位是”基础设施与实验性部署资产”，不是”完整应用交付层”。

## 四、端口职责

| 端口 | 服务 | 用途 |
|------|------|------|
| `8091` | Dashboard Server (`src/`) | 主 UI + Dashboard API |
| `8000` | `gateway-service` | Open Platform 适配 API |
| `5173` | `vite` | 前端开发服务器 |

如果浏览器要打开“页面”，默认应看 `8091`，不是 `8000`。

## 五、配置优先级

当前主线遵循：

1. `.env`
2. `data/system_config.json`
3. `config/config.yaml`

说明：

- `config/config.yaml` 是主配置默认值
- `data/system_config.json` 是 Dashboard 持久化覆盖
- `.env` 拥有最高优先级

## 六、当前真实判断

### 已落地

- Dashboard UI 与 `/api/*` 主链路
- React 构建产物由 Python 托管
- 闲管家 Open Platform 集成
- 独立 `gateway-service` 可运行
- `services/common/` 共享基础设施（51 个测试）
- Option B 执行完毕，移除 4 个 scaffold 服务

### 未完整落地

- 完整 Helm 应用 Chart
- 一键式 K8s 应用部署
- 纯服务化替代 `dashboard_server`

## 七、阅读建议

如果你要理解当前仓库，优先顺序应是：

1. `README.md`
2. `docs/DEPLOYMENT.md`
3. `src/dashboard_server.py`
4. `src/dashboard/routes/`
5. `services/gateway-service/`
