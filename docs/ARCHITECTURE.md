# 架构设计

> 当前 `main` 的真实形态是“Dashboard 主线 + 部分服务化资产并存”的混合架构，不是一个已经完整切走 Helm/Kubernetes 的纯微服务仓库。

## 一、当前运行时主线

```text
浏览器
  ↓
Dashboard Server (src/dashboard_server.py, :8091)
  ├─ 托管 client/dist
  ├─ 暴露 /healthz
  └─ 暴露 /api/*
        ↓
     src/dashboard/routes/*
        ↓
     dashboard/services + modules + integrations
```

这是当前最完整、最可用的本地运行链路。

## 二、并存的服务化资产

仓库中同时存在 `services/` 目录：

- `gateway-service`
- `quote-service`
- `ai-service`
- `message-service`
- `order-service`
- `common`

这些目录说明仓库已经开始服务化拆分，但当前现实是：

- `gateway-service` 可单独运行，且已能打通闲管家 Open Platform
- 其他服务主要是代码骨架和实验性拆分结果
- `services/scheduler-service` 当前不存在
- `services/helm/xianyuflow` 当前不存在

所以不能把当前主线描述成“六服务 + Helm Chart 已全部就绪”。

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

本地基础设施脚本、Terraform 和 Helm 资产。当前更准确的定位是“基础设施与实验性部署资产”，不是“完整应用交付层”。

## 四、端口职责

| 端口 | 服务 | 用途 |
|------|------|------|
| `8091` | `src.dashboard_server` | 主 UI + Dashboard API |
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
- 独立 `gateway-service` 基础可运行

### 未完整落地

- 完整 Helm 应用 Chart
- 一键式 K8s 应用部署
- 完整六服务生产编排
- 纯服务化替代 `dashboard_server`

## 七、阅读建议

如果你要理解当前仓库，优先顺序应是：

1. `README.md`
2. `docs/DEPLOYMENT.md`
3. `src/dashboard_server.py`
4. `src/dashboard/routes/`
5. `services/gateway-service/`
